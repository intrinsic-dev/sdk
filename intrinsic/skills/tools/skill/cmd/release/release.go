// Copyright 2023 Intrinsic Innovation LLC

// Package release defines the command that releases skills to the catalog.
package release

import (
	"fmt"
	"log"
	"os/exec"
	"strings"

	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillmanifestpb "intrinsic/skills/proto/skill_manifest_go_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/directupload"
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

func release(cmd *cobra.Command, conn *grpc.ClientConn, req *skillcatalogpb.CreateSkillRequest, idVersion string) error {
	_ = skillcataloggrpcpb.NewSkillCatalogClient(conn)
	return status.Errorf(codes.Unimplemented, "releasing skills is not yet supported")

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
		project := clientutils.ResolveCatalogProjectFromInctl(cmdFlags)

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

		useDirectUpload := true
		needConn := true

		var conn *grpc.ClientConn
		if needConn {
			var err error
			conn, err = clientutils.DialCatalogFromInctl(cmd, cmdFlags)
			if err != nil {
				return fmt.Errorf("failed to create client connection: %v", err)
			}
			defer conn.Close()
		}

		// Functions to prepare each release type.
		pushSkillPreparer := func() error {
			if dryRun {
				log.Printf("Skipping pushing skill %q to the container registry (dry-run)", target)
				return nil
			}

			var transferer imagetransfer.Transferer
			if useDirectUpload {
				opts := []directupload.Option{
					directupload.WithDiscovery(directupload.NewCatalogTarget(conn)),
					directupload.WithOutput(cmd.OutOrStdout()),
				}
				transferer = directupload.NewTransferer(cmd.Context(), opts...)
			}
			imageTag, err := imageutils.GetAssetVersionImageTag("skill", cmdFlags.GetFlagVersion())
			if err != nil {
				return err
			}
			imgpb, _, err := registry.PushSkill(target, registry.PushOptions{
				Registry:   imageutils.GetRegistry(project),
				Tag:        imageTag,
				Type:       targetType,
				Transferer: transferer,
			})
			if err != nil {
				return fmt.Errorf("could not push target %q to the container registry: %v", target, err)
			}
			req.DeploymentType = &skillcatalogpb.CreateSkillRequest_Image{Image: imgpb}

			return nil
		}
		releasePreparers := map[string]func() error{
			"archive": pushSkillPreparer,
			"build":   pushSkillPreparer,
			"image":   pushSkillPreparer,
		}

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

		return release(cmd, conn, req, idVersion)
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
