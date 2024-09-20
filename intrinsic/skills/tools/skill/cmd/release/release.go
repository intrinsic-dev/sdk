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
	"intrinsic/assets/bundleio"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillmanifestpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/skills/tools/resource/cmd/bundleimages"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/directupload"
	"intrinsic/skills/tools/skill/cmd/skillio"
	"intrinsic/util/proto/protoio"
)

const (
	keyDescription = "description"
)

var cmdFlags = cmdutils.NewCmdFlags()

var (
	buildCommand    = "bazel"
	buildConfigArgs = []string{
		"--config", "intrinsic",
	}
)

func getManifest() (*skillmanifestpb.SkillManifest, error) {
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

	manifest := new(skillmanifestpb.SkillManifest)
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

func release(cmd *cobra.Command, conn *grpc.ClientConn, req *skillcatalogpb.CreateSkillRequest, idVersion string) error {
	client := skillcataloggrpcpb.NewSkillCatalogClient(conn)
	if _, err := client.CreateSkill(cmd.Context(), req); err != nil {
		if s, ok := status.FromError(err); ok && cmdFlags.GetFlagIgnoreExisting() && s.Code() == codes.AlreadyExists {
			log.Printf("skipping release: skill %q already exists in the catalog", idVersion)
			return nil
		}
		return fmt.Errorf("could not release the skill :%w", err)
	}

	log.Printf("finished releasing the skill")

	return nil
}

type imageTransfererOpts struct {
	cmd             *cobra.Command
	conn            *grpc.ClientConn
	useDirectUpload bool
}

func imageTransferer(opts imageTransfererOpts) imagetransfer.Transferer {
	var transferer imagetransfer.Transferer
	if opts.useDirectUpload {
		dopts := []directupload.Option{
			directupload.WithDiscovery(directupload.NewCatalogTarget(opts.conn)),
			directupload.WithOutput(opts.cmd.OutOrStdout()),
		}
		transferer = directupload.NewTransferer(opts.cmd.Context(), dopts...)
	}
	return transferer
}

func skillRequestFromManifest() (*skillcatalogpb.CreateSkillRequest, error) {
	manifest, err := getManifest()
	if err != nil {
		return nil, err
	}
	return &skillcatalogpb.CreateSkillRequest{
		ManifestType: &skillcatalogpb.CreateSkillRequest_Manifest{
			Manifest: manifest,
		},
		Version:      cmdFlags.GetFlagVersion(),
		ReleaseNotes: cmdFlags.GetFlagReleaseNotes(),
		Default:      cmdFlags.GetFlagDefault(),
		OrgPrivate:   cmdFlags.GetFlagOrgPrivate(),
	}, nil
}

type skillRequestFromBundleOpts struct {
	flags      *cmdutils.CmdFlags
	transferer imagetransfer.Transferer
	path       string
}

func skillRequestFromBundle(opts skillRequestFromBundleOpts) (*skillcatalogpb.CreateSkillRequest, error) {
	manifest, err := bundleio.ProcessSkill(opts.path, bundleio.ProcessSkillOpts{
		ImageProcessor: bundleimages.CreateImageProcessor(imageutils.RegistryOptions{
			Transferer: opts.transferer,
			URI:        imageutils.GetRegistry(clientutils.ResolveCatalogProjectFromInctl(opts.flags)),
		}),
	})
	if err != nil {
		return nil, errors.Wrap(err, "Could not read bundle file "+opts.path)
	}
	return &skillcatalogpb.CreateSkillRequest{
		ManifestType: &skillcatalogpb.CreateSkillRequest_ProcessedSkillManifest{
			ProcessedSkillManifest: manifest,
		},
		Version:      opts.flags.GetFlagVersion(),
		Default:      opts.flags.GetFlagDefault(),
		OrgPrivate:   opts.flags.GetFlagOrgPrivate(),
		ReleaseNotes: opts.flags.GetFlagReleaseNotes(),
	}, nil
}

func idVersionFromRequest(req *skillcatalogpb.CreateSkillRequest) (string, error) {
	if req.GetProcessedSkillManifest() != nil {
		id := req.GetProcessedSkillManifest().GetMetadata().GetId()
		return idutils.IDVersionFrom(id.GetPackage(), id.GetName(), req.GetVersion())
	}
	id := req.GetManifest().GetId()
	return idutils.IDVersionFrom(id.GetPackage(), id.GetName(), req.GetVersion())
}

func remoteOpt() remote.Option {
	return remote.WithAuthFromKeychain(google.Keychain)
}

var releaseExamples = strings.Join(
	[]string{
		`Build a skill then upload and release it to the skill catalog:
  $ inctl skill release --type=build //abc:skill_bundle ...`,
		`Upload and release a skill image to the skill catalog:
  $ inctl skill release --type=archive /path/to/skill.bundle.tar ...`,
	},
	"\n\n",
)

func releaseRequest(ps *skillio.ProcessedSkill) (*skillcatalogpb.CreateSkillRequest, error) {
	if ps.ProcessedManifest != nil {
		return &skillcatalogpb.CreateSkillRequest{
			ManifestType: &skillcatalogpb.CreateSkillRequest_ProcessedSkillManifest{
				ProcessedSkillManifest: ps.ProcessedManifest,
			},
			Version:      cmdFlags.GetFlagVersion(),
			Default:      cmdFlags.GetFlagDefault(),
			OrgPrivate:   cmdFlags.GetFlagOrgPrivate(),
			ReleaseNotes: cmdFlags.GetFlagReleaseNotes(),
		}, nil
	}

	if ps.Image != nil && ps.Manifest != nil {
		return &skillcatalogpb.CreateSkillRequest{
			ManifestType: &skillcatalogpb.CreateSkillRequest_Manifest{
				Manifest: ps.Manifest,
			},
			DeploymentType: &skillcatalogpb.CreateSkillRequest_Image{
				Image: ps.Image,
			},
			Version:      cmdFlags.GetFlagVersion(),
			ReleaseNotes: cmdFlags.GetFlagReleaseNotes(),
			Default:      cmdFlags.GetFlagDefault(),
			OrgPrivate:   cmdFlags.GetFlagOrgPrivate(),
		}, nil
	}

	return nil, fmt.Errorf("could not build a complete create skill request: missing required information")
}

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

		var transferer imagetransfer.Transferer
		if targetType != "pbt" {
			transferer = imageTransferer(imageTransfererOpts{
				cmd:             cmd,
				conn:            conn,
				useDirectUpload: useDirectUpload,
			})
		}

		psOpts := skillio.ProcessSkillOpts{
			Target:           target,
			ManifestFilePath: cmdFlags.GetString(cmdutils.KeyManifestFile),
			ManifestTarget:   cmdFlags.GetString(cmdutils.KeyManifestTarget),
			Version:          cmdFlags.GetFlagVersion(),
			RegistryOpts: imageutils.RegistryOptions{
				URI:        imageutils.GetRegistry(project),
				Transferer: transferer,
			},
			DryRun: dryRun,
		}

		// Functions to prepare each install type.
		archivePreparer := func() (*skillcatalogpb.CreateSkillRequest, error) {
			ps, err := skillio.ProcessFile(psOpts)
			if err != nil {
				return nil, err
			}
			return releaseRequest(ps)
		}
		buildPreparer := func() (*skillcatalogpb.CreateSkillRequest, error) {
			ps, err := skillio.ProcessBuildTarget(psOpts)
			if err != nil {
				return nil, err
			}
			return releaseRequest(ps)
		}

		releasePreparers := map[string]func() (*skillcatalogpb.CreateSkillRequest, error){
			"archive": archivePreparer,
			"build":   buildPreparer,
		}

		// Prepare the release based on the specified release type.
		prepareRelease, ok := releasePreparers[targetType]
		if !ok {
			return fmt.Errorf("unknown release type %q", targetType)
		}
		req, err := prepareRelease()
		if err != nil {
			return err
		}

		idVersion, err := idVersionFromRequest(req)
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
