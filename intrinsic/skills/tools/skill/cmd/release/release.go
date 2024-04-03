// Copyright 2023 Intrinsic Innovation LLC

// Package release defines the command that releases skills to the catalog.
package release

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillmanifestpb "intrinsic/skills/proto/skill_manifest_go_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/registry"
	"intrinsic/util/proto/protoio"
)

const (
	keyDescription = "description"
)

var cmdFlags = cmdutils.NewCmdFlags()

var (
	buildCommand    = "bazel"
	buildConfigArgs = []string{
		"-c", "opt",
	}
)

func release(cmd *cobra.Command, req *skillcatalogpb.CreateSkillRequest, idVersion string) error {
	conn, err := clientutils.DialSkillCatalogFromInctl(cmd, cmdFlags)
	if err != nil {
		return fmt.Errorf("failed to create client connection: %v", err)
	}
	defer conn.Close()

	_ = skillcataloggrpcpb.NewSkillCatalogClient(conn)
	err = status.Errorf(codes.Unimplemented, "releasing skills is not yet supported")

	if err != nil {
		if s, ok := status.FromError(err); ok && cmdFlags.GetFlagIgnoreExisting() && s.Code() == codes.AlreadyExists {
			log.Printf("skipping release: skill %q already exists in the catalog", idVersion)
			return nil
		}
		return fmt.Errorf("could not release the skill :%w", err)
	}

	log.Printf("finished releasing the skill")

	return nil
}

func getManifest() (*skillmanifestpb.Manifest, error) {
	manifestFilePath, manifestTarget, err := cmdFlags.GetFlagsManifest()
	if err != nil {
		return nil, err
	}
	if manifestTarget != "" {
		var err error
		if manifestFilePath, err = getManifestFileFromTarget(manifestTarget); err != nil {
			return nil, fmt.Errorf("cannot build manifest target %q: %v", manifestTarget, err)
		}
	}

	manifest := new(skillmanifestpb.Manifest)
	if err := protoio.ReadBinaryProto(manifestFilePath, manifest); err != nil {
		return nil, fmt.Errorf("cannot read proto file %q: %v", manifestFilePath, err)
	}

	return manifest, nil
}

func getManifestFileFromTarget(target string) (string, error) {
	buildArgs := []string{"build"}
	buildArgs = append(buildArgs, buildConfigArgs...)
	buildArgs = append(buildArgs, target)

	out, err := execute(buildCommand, buildArgs...)
	if err != nil {
		return "", fmt.Errorf("could not build manifest: %v\n%s", err, out)
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

func namePackageFromID(skillID string) (string, string, error) {
	name, err := idutils.NameFrom(skillID)
	if err != nil {
		return "", "", errors.Wrapf(err, "could not retrieve skill name from id")
	}
	pkg, err := idutils.PackageFrom(skillID)
	if err != nil {
		return "", "", errors.Wrapf(err, "could not retrieve skill package from id")
	}

	return name, pkg, nil
}

func remoteOpt() remote.Option {
	return remote.WithAuthFromKeychain(google.Keychain)
}

var releaseExamples = strings.Join(
	[]string{
		`Build a skill then upload and release it to the skill catalog:
  $ inctl skill release --type=build //abc:skill.tar ...`,
		`Upload and release a skill image to the skill catalog:
  $ inctl skill release --type=archive /path/to/skill.tar ...`,
		`Upload a skill image to the catalog service, push it to the service's configured registry, then release it to the skill catalog:
  $ inctl skill release --type=archive_server_side_push /path/to/skill.tar ...`,
	},
	"\n\n",
)

var releaseCmd = &cobra.Command{
	Use:     "release target",
	Short:   "Release a skill to the catalog",
	Example: releaseExamples,
	Args:    cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		target := args[0]
		dryRun := cmdFlags.GetFlagDryRun()
		targetType := cmdFlags.GetFlagSkillReleaseType()
		project := clientutils.ResolveProject(cmd.Context(), cmdFlags)

		manifest, err := getManifest()
		if err != nil {
			return err
		}

		req := &skillcatalogpb.CreateSkillRequest{
			Manifest:     manifest,
			Version:      cmdFlags.GetFlagVersion(),
			ReleaseNotes: cmdFlags.GetFlagReleaseNotes(),
			Default:      cmdFlags.GetFlagDefault(),
			OrgPrivate:   cmdFlags.GetFlagOrgPrivate(),
		}

		// Functions to prepare each release type.
		releasePreparers := map[string]func() error{}

		serverSideArchivePreparer := func() error {
			bytes, err := os.ReadFile(target)
			if err != nil {
				return fmt.Errorf("failed to read skill image %q: %v", target, err)
			}
			req.DeploymentType = &skillcatalogpb.CreateSkillRequest_SkillImage{
				SkillImage: &skillcatalogpb.SkillImage{
					ImageArchive: bytes,
				},
			}

			return nil
		}

		pushSkillPreparer := func() error {
			var transferer imagetransfer.Transferer
			if dryRun {
				transferer = imagetransfer.Readonly(remoteOpt())
			} else {
				transferer = imagetransfer.RemoteTransferer(remoteOpt())
			}
			imgpb, _, err := registry.PushSkill(target, registry.PushOptions{
				Registry:   fmt.Sprintf("gcr.io/%s", project),
				Type:       targetType,
				Transferer: transferer,
			})
			if err != nil {
				return fmt.Errorf("could not push target %q to the container registry: %v", target, err)
			}
			req.DeploymentType = &skillcatalogpb.CreateSkillRequest_Image{Image: imgpb}

			return nil
		}
		releasePreparers["build"] = pushSkillPreparer
		releasePreparers["archive"] = pushSkillPreparer
		releasePreparers["image"] = pushSkillPreparer
		releasePreparers["archive_server_side_push"] = serverSideArchivePreparer

		// Prepare the release based on the specified release type.
		if prepareRelease, ok := releasePreparers[targetType]; !ok {
			return fmt.Errorf("unknown release type %q", targetType)
		} else if err := prepareRelease(); err != nil {
			return err
		}

		idVersion, err := idutils.IDVersionFrom(manifest.GetId().GetPackage(), manifest.GetId().GetName(), req.GetVersion())
		if err != nil {
			return err
		}

		if dryRun {
			log.Printf("Skipping release of skill %q to the skill catalog (dry-run)", idVersion)
			return nil
		}
		log.Printf("releasing skill %q to the skill catalog", idVersion)

		return release(cmd, req, idVersion)
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(releaseCmd)
	cmdFlags.SetCommand(releaseCmd)

	cmdFlags.AddFlagDefault("skill")
	cmdFlags.AddFlagDryRun()
	cmdFlags.AddFlagIgnoreExisting("skill")
	cmdFlags.AddFlagOrgPrivate()
	cmdFlags.AddFlagsManifest()
	cmdFlags.AddFlagReleaseNotes("skill")
	cmdFlags.AddFlagSkillReleaseType()
	cmdFlags.AddFlagVersion("skill")
}
