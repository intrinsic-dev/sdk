// Copyright 2023 Intrinsic Innovation LLC

package bundleio

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"archive/tar"
	descriptorpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"google.golang.org/protobuf/proto"
	psmpb "intrinsic/skills/proto/processed_skill_manifest_go_proto"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/util/archive/tartooling"
)

const (
	skillManifestPathInTar = "skill_manifest.binpb"
)

// makeOnlySkillManifestHandlers returns a map of handlers that only pull out
// the skill manifest from the tar file into the returned proto. Can be used
// with a fallback handler.
func makeOnlySkillManifestHandlers() (*smpb.SkillManifest, map[string]handler) {
	manifest := new(smpb.SkillManifest)
	handlers := map[string]handler{
		skillManifestPathInTar: makeBinaryProtoHandler(manifest),
	}
	return manifest, handlers
}

// makeSkillAssetHandlers returns handlers for all assets listed in the
// skill manifest. This will be at most:
// * A handler that ignores the manifest
// * A binary proto handler for the file descriptor set file
// * A handler that wraps opts.ImageProcessor to be called on every image
// * A binary proto handler for the parameterized behavior tree file
func makeSkillAssetHandlers(manifest *smpb.SkillManifest, opts ProcessSkillOpts) (*psmpb.ProcessedSkillAssets, map[string]handler) {
	handlers := map[string]handler{
		skillManifestPathInTar: ignoreHandler, // already read this.
	}
	// Don't generate an empty assets message if there wasn't one to begin
	// with. This is a slightly odd state, but Process is not doing validation of
	// the manifest. This also protects against nil access of
	// manifest.GetAssets().{MemberVariable}, which is required for checking the
	// "optional" piece of "optional string" fields in this version of the golang
	// proto API.
	if manifest.GetAssets() == nil {
		return nil, handlers
	}

	processedAssets := &psmpb.ProcessedSkillAssets{}
	if p := manifest.GetAssets().FileDescriptorSetFilename; p != nil {
		processedAssets.FileDescriptorSet = new(descriptorpb.FileDescriptorSet)
		handlers[*p] = makeBinaryProtoHandler(processedAssets.FileDescriptorSet)
	}
	switch manifest.GetAssets().GetDeploymentType().(type) {
	case *smpb.SkillAssets_ImageFilename:
		p := manifest.GetAssets().GetImageFilename()
		handlers[p] = func(r io.Reader) error {
			img, err := opts.ImageProcessor(manifest.GetId(), p, r)
			if err != nil {
				return fmt.Errorf("error processing image: %v", err)
			}
			processedAssets.DeploymentType = &psmpb.ProcessedSkillAssets_Image{
				Image: img,
			}
			return nil
		}
	case *smpb.SkillAssets_BehaviorTreeFilename:
		p := manifest.GetAssets().GetBehaviorTreeFilename()
		if opts.BehaviorTreeProcessor == nil {
			handlers[p] = ignoreHandler
		} else {
			handlers[p] = func(r io.Reader) error {
				cas, err := opts.BehaviorTreeProcessor(r)
				if err != nil {
					return fmt.Errorf("error processing behavior tree: %v", err)
				}
				processedAssets.DeploymentType = &psmpb.ProcessedSkillAssets_BehaviorTreeCasUri{
					BehaviorTreeCasUri: cas,
				}
				return nil
			}
		}
	}
	return processedAssets, handlers
}

// ReadSkill reads the skill bundle archive from path. It returns the
// skill manifest and a mapping between bundle filenames and their contents.
func ReadSkill(path string) (*smpb.SkillManifest, map[string][]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, nil, fmt.Errorf("could not open %q: %v", path, err)
	}
	defer f.Close()

	m, handlers := makeOnlySkillManifestHandlers()
	inlined, fallback := makeCollectInlinedFallbackHandler()
	if err := walkTarFile(tar.NewReader(f), handlers, fallback); err != nil {
		return nil, nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}
	return m, inlined, nil
}

// ReadSkillManifest reads the bundle archive from path. It returns only
// skill manifest.
func ReadSkillManifest(path string) (*smpb.SkillManifest, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("could not open %q: %v", path, err)
	}
	defer f.Close()

	m, handlers := makeOnlySkillManifestHandlers()
	if err := walkTarFile(tar.NewReader(f), handlers, nil); err != nil {
		return nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}
	return m, nil
}

// BehaviorTreeProcessor is a closure that pushes a serialized behavior tree
// to CAS and returns a reference to the stored object.
type BehaviorTreeProcessor func(r io.Reader) (string, error)

// ProcessSkillOpts contains the necessary handlers to generate a processed
// skill manifest.
type ProcessSkillOpts struct {
	ImageProcessor
	BehaviorTreeProcessor
}

// ProcessSkill creates a processed manifest from a bundle on disk using the
// provided processing functions. It avoids doing any validation except for
// that required to transform the specified files in the bundle into their
// processed variants.
func ProcessSkill(path string, opts ProcessSkillOpts) (*psmpb.ProcessedSkillManifest, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("could not open %q: %v", path, err)
	}
	defer f.Close()

	// Read the manifest and then reset the file once we have the information
	// about the bundle we're going to process.
	manifest, handlers := makeOnlySkillManifestHandlers()
	if err := walkTarFile(tar.NewReader(f), handlers, nil); err != nil {
		return nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}
	if _, err := f.Seek(0, io.SeekStart); err != nil {
		return nil, fmt.Errorf("could not seek in %q: %v", path, err)
	}

	// Initialize handlers for when we walk through the file again now that we
	// know what we're looking for, but error on unexpected files this time.
	processedAssets, handlers := makeSkillAssetHandlers(manifest, opts)
	fallback := func(n string, r io.Reader) error {
		return fmt.Errorf("unexpected file %q", n)
	}
	if err := walkTarFile(tar.NewReader(f), handlers, fallback); err != nil {
		return nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}

	psm := &psmpb.ProcessedSkillManifest{
		Assets: processedAssets,
	}
	m := &psmpb.SkillMetadata{
		Id:                    manifest.GetId(),
		Vendor:                manifest.GetVendor(),
		Documentation:         manifest.GetDocumentation(),
		ExtendedDocumentation: manifest.GetExtendedDocumentation(),
		DisplayName:           manifest.GetDisplayName(),
	}
	// We do this to avoid adding empty sub messages.
	if !proto.Equal(m, &psmpb.SkillMetadata{}) {
		psm.Metadata = m
	}
	d := &psmpb.SkillDetails{
		Options:       manifest.GetOptions(),
		Dependencies:  manifest.GetDependencies(),
		Parameter:     manifest.GetParameter(),
		ExecuteResult: manifest.GetReturnType(),
		StatusInfo:    manifest.GetStatusInfo(),
	}
	// We do this to avoid adding empty sub messages.
	if !proto.Equal(d, &psmpb.SkillDetails{}) {
		psm.Details = d
	}
	return psm, nil
}

// ValidateSkill checks that the assets of a skill bundle are all
// contained within the inlined file map.
func ValidateSkill(manifest *smpb.SkillManifest, inlinedFiles map[string][]byte) error {
	files := make([]string, 0, len(inlinedFiles))
	usedFiles := make(map[string]bool)
	for f := range inlinedFiles {
		files = append(files, f)
		usedFiles[f] = true
	}
	fileNames := strings.Join(files, ", ")
	// Check that every defined asset is in the inlined filemap.
	assets := map[string]string{
		"image tar":           manifest.GetAssets().GetImageFilename(),
		"behavior tree file":  manifest.GetAssets().GetBehaviorTreeFilename(),
		"file descriptor set": manifest.GetAssets().GetFileDescriptorSetFilename(),
	}
	for desc, path := range assets {
		if path != "" {
			if _, ok := inlinedFiles[path]; !ok {
				return fmt.Errorf("the skill manifest's %s %q is not in the bundle. files are %s", desc, path, fileNames)
			}
			delete(usedFiles, path)
		}
	}
	if len(usedFiles) > 0 {
		files := make([]string, 0, len(usedFiles))
		for f := range usedFiles {
			files = append(files, f)
		}
		fileNames := strings.Join(files, ", ")
		return fmt.Errorf("found unexpected files in the archive: %s", fileNames)
	}
	return nil
}

// WriteSkillOpts provides the details to construct a skill bundle.
type WriteSkillOpts struct {
	Manifest    *smpb.SkillManifest
	Descriptors *descriptorpb.FileDescriptorSet
	ImageTar    string
	PBT         string
}

// WriteSkill creates a tar archive at the specified path with the details
// given in opts. Only the manifest is required and its assets field will be
// overwritten with what is placed in the archive based on ops.
func WriteSkill(path string, opts WriteSkillOpts) error {
	if opts.Manifest == nil {
		return fmt.Errorf("opts.Manifest must not be nil")
	}
	if opts.ImageTar != "" && opts.PBT != "" {
		return fmt.Errorf("opts.ImageTar and opts.PBT cannot both be set")
	}
	out, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0644)
	if err != nil {
		return fmt.Errorf("failed to open %q for writing: %w", path, err)
	}
	defer out.Close()
	tw := tar.NewWriter(out)

	opts.Manifest.Assets = new(smpb.SkillAssets)
	if opts.Descriptors != nil {
		descriptorName := "descriptors-transitive-descriptor-set.proto.bin"
		opts.Manifest.Assets.FileDescriptorSetFilename = &descriptorName
		if err := tartooling.AddBinaryProto(opts.Descriptors, tw, descriptorName); err != nil {
			return fmt.Errorf("unable to write FileDescriptorSet to bundle: %v", err)
		}
	}
	if opts.ImageTar != "" {
		base := filepath.Base(opts.ImageTar)
		opts.Manifest.Assets.DeploymentType = &smpb.SkillAssets_ImageFilename{
			ImageFilename: base,
		}
		if err := tartooling.AddFile(opts.ImageTar, tw, base); err != nil {
			return fmt.Errorf("unable to write %q to bundle: %v", path, err)
		}
	}
	if opts.PBT != "" {
		base := filepath.Base(opts.PBT)
		opts.Manifest.Assets.DeploymentType = &smpb.SkillAssets_BehaviorTreeFilename{
			BehaviorTreeFilename: base,
		}
		if err := tartooling.AddFile(opts.PBT, tw, base); err != nil {
			return fmt.Errorf("unable to write %q to bundle: %v", path, err)
		}
	}
	// Now we can write the manifest, since assets have been completed.
	if err := tartooling.AddBinaryProto(opts.Manifest, tw, skillManifestPathInTar); err != nil {
		return fmt.Errorf("unable to write skill manifest to bundle: %v", err)
	}
	if err := tw.Close(); err != nil {
		return err
	}
	return nil
}
