// Copyright 2023 Intrinsic Innovation LLC

// Package skillio contains utilities that process user-provided skills.
package skillio

import (
	"fmt"
	"log"
	"os/exec"
	"strings"

	"github.com/google/go-containerregistry/pkg/v1/tarball"
	"github.com/pkg/errors"
	"intrinsic/assets/bundleio"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imageutils"
	ipb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	psmpb "intrinsic/skills/proto/processed_skill_manifest_go_proto"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/skills/tools/resource/cmd/bundleimages"
	"intrinsic/skills/tools/skill/cmd/registry"
	"intrinsic/util/proto/protoio"
)

var (
	buildCommand    = "bazel"
	buildConfigArgs = []string{
		"--config", "intrinsic",
	}
)

// execute runs a command and captures its output.
func execute(buildCommand string, buildArgs ...string) ([]byte, error) {
	c := exec.Command(buildCommand, buildArgs...)
	out, err := c.Output() // Ignore stderr
	if err != nil {
		return nil, fmt.Errorf("exec command failed: %v\n%s", err, out)
	}
	return out, nil
}

func getOutputFiles(target string) ([]string, error) {
	buildArgs := []string{"cquery"}
	buildArgs = append(buildArgs, buildConfigArgs...)
	buildArgs = append(buildArgs, "--output=files", target)
	out, err := execute(buildCommand, buildArgs...)
	if err != nil {
		return nil, fmt.Errorf("could not get output files: %v\n%s", err, out)
	}
	return strings.Split(strings.TrimSpace(string(out)), "\n"), nil
}

func buildTarget(target string) (string, error) {
	buildArgs := []string{"build"}
	buildArgs = append(buildArgs, buildConfigArgs...)
	buildArgs = append(buildArgs, target)
	out, err := execute(buildCommand, buildArgs...)
	if err != nil {
		return "", fmt.Errorf("could not build target %q: %v\n%s", target, err, out)
	}

	outputFiles, err := getOutputFiles(target)
	if err != nil {
		return "", fmt.Errorf("could not get output files of target %s: %v", target, err)
	}
	if len(outputFiles) == 0 {
		return "", fmt.Errorf("target %s did not have any output files", target)
	}
	if len(outputFiles) > 1 {
		log.Printf("Warning: Rule %s was expected to have only one output file, but it had %d", target, len(outputFiles))
	}
	return outputFiles[0], nil
}

// ProcessedSkill contains output of ProcessFile or ProcessBuildTarget. Every
// instance should either have both its Manifest and Image fields populated, or
// have ProcessedManifest filled in.
type ProcessedSkill struct {
	Manifest          *smpb.SkillManifest
	Image             *ipb.Image
	ProcessedManifest *psmpb.ProcessedSkillManifest
	ID                string
}

// ProcessSkillOpts contains options for ProcessFile and ProcessBuildTarget
// functions.
type ProcessSkillOpts struct {
	Target               string
	ManifestFilePath     string
	ManifestTarget       string
	Version              string
	RegistryOpts         imageutils.RegistryOptions
	AllowMissingManifest bool
	DryRun               bool
}

func processBundleFile(opts ProcessSkillOpts) (*ProcessedSkill, error) {
	if opts.DryRun {
		manifest, err := bundleio.ReadSkillManifest(opts.Target)
		if err != nil {
			return nil, fmt.Errorf("failed to read skill manifest from bundle: %v", err)
		}
		id, err := idutils.IDFromProto(manifest.GetId())
		if err != nil {
			return nil, fmt.Errorf("invalid ID in manifest: %v", err)
		}
		log.Printf("Skipping pushing skill %q to the container registry (dry-run)", opts.Target)
		return &ProcessedSkill{
			ProcessedManifest: &psmpb.ProcessedSkillManifest{
				Metadata: &psmpb.SkillMetadata{
					Id: manifest.GetId(),
				},
			},
			ID: id,
		}, nil
	}

	manifest, err := bundleio.ProcessSkill(opts.Target, bundleio.ProcessSkillOpts{
		ImageProcessor: bundleimages.CreateImageProcessor(opts.RegistryOpts),
	})
	if err != nil {
		return nil, errors.Wrap(err, "Could not read bundle file "+opts.Target)
	}
	id, err := idutils.IDFromProto(manifest.GetMetadata().GetId())
	if err != nil {
		return nil, fmt.Errorf("invalid ID in manifest: %v", err)
	}
	return &ProcessedSkill{
		ProcessedManifest: manifest,
		ID:                id,
	}, nil
}

func processContainerImageFile(opts ProcessSkillOpts) (*ProcessedSkill, error) {
	var manifest *smpb.SkillManifest
	var id string
	if !opts.AllowMissingManifest {
		if opts.ManifestFilePath == "" && opts.ManifestTarget == "" {
			return nil, fmt.Errorf("either ManifestFilePath or ManifestTarget must be provided when using container image skills")
		}

		manifestFilePath := opts.ManifestFilePath
		if opts.ManifestTarget != "" {
			var err error
			if manifestFilePath, err = buildTarget(opts.ManifestTarget); err != nil {
				return nil, fmt.Errorf("cannot build manifest target %q: %v", opts.ManifestTarget, err)
			}
		}

		manifest = &smpb.SkillManifest{}
		if err := protoio.ReadBinaryProto(manifestFilePath, manifest); err != nil {
			return nil, fmt.Errorf("cannot read proto file %q: %v", manifestFilePath, err)
		}

		var err error
		id, err = idutils.IDFromProto(manifest.GetId())
		if err != nil {
			return nil, fmt.Errorf("invalid ID in manifest: %v", err)
		}
	} else {
		var err error
		id, err = imageutils.SkillIDFromTarget(opts.Target, imageutils.Archive)
		if err != nil {
			return nil, fmt.Errorf("could not get skill ID from skill container image: %v", err)
		}
	}

	imageTag, err := imageutils.GetAssetVersionImageTag("skill", opts.Version)
	if err != nil {
		return nil, err
	}

	if opts.DryRun {
		log.Printf("Skipping pushing skill %q to the container registry (dry-run)", opts.Target)
		return &ProcessedSkill{
			Manifest: manifest,
			ID:       id,
		}, nil
	}

	imgpb, _, err := registry.PushSkill(opts.Target, registry.PushOptions{
		RegistryOpts: opts.RegistryOpts,
		Tag:          imageTag,
		Type:         string(imageutils.Archive),
	})
	if err != nil {
		return nil, fmt.Errorf("could not push %q to the container registry: %v", opts.Target, err)
	}
	return &ProcessedSkill{
		Manifest: manifest,
		Image:    imgpb,
		ID:       id,
	}, nil
}

// ProcessFile processes either a skill container image (and associated manifest
// file) or a skill bundle file.
func ProcessFile(opts ProcessSkillOpts) (*ProcessedSkill, error) {
	if IsValidSkillBundle(opts.Target) {
		return processBundleFile(opts)
	}
	if IsValidContainerImage(opts.Target) {
		return processContainerImageFile(opts)
	}
	return nil, fmt.Errorf("%q does not appear to be a valid skill", opts.Target)
}

// ProcessBuildTarget builds a skill and then processes the resulting file.
func ProcessBuildTarget(opts ProcessSkillOpts) (*ProcessedSkill, error) {
	path, err := buildTarget(opts.Target)
	if err != nil {
		return nil, err
	}

	return ProcessFile(ProcessSkillOpts{
		Target:               path,
		ManifestFilePath:     opts.ManifestFilePath,
		ManifestTarget:       opts.ManifestTarget,
		Version:              opts.Version,
		RegistryOpts:         opts.RegistryOpts,
		AllowMissingManifest: opts.AllowMissingManifest,
		DryRun:               opts.DryRun,
	})
}

// IsValidContainerImage returns true if the given file is a container image.
func IsValidContainerImage(path string) bool {
	if _, err := tarball.ImageFromPath(path, nil); err != nil {
		return false
	}
	return true
}

// IsValidSkillBundle returns true if the given file is a skill bundle file.
func IsValidSkillBundle(path string) bool {
	if _, err := bundleio.ReadSkillManifest(path); err != nil {
		return false
	}
	return true
}

// SkillIDFromArchive extracts the skill ID from a skill archive file.
func SkillIDFromArchive(path string) (string, error) {
	if IsValidSkillBundle(path) {
		manifest, err := bundleio.ReadSkillManifest(path)
		if err != nil {
			return "", fmt.Errorf("failed to read skill manifest from bundle: %v", err)
		}
		id, err := idutils.IDFromProto(manifest.GetId())
		if err != nil {
			return "", fmt.Errorf("invalid skill ID in manifest: %v", err)
		}
		return id, nil
	}
	if IsValidContainerImage(path) {
		id, err := imageutils.SkillIDFromTarget(path, imageutils.Archive)
		if err != nil {
			return "", fmt.Errorf("could not get skill ID from skill container image: %v", err)
		}
		return id, nil
	}
	return "", fmt.Errorf("%q does not appear to be a valid skill", path)
}

// SkillIDFromBuildTarget extracts the skill ID from a build target.
func SkillIDFromBuildTarget(target string) (string, error) {
	path, err := buildTarget(target)
	if err != nil {
		return "", err
	}
	return SkillIDFromArchive(path)
}
