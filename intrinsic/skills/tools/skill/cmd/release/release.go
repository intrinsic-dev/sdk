// Copyright 2023 Intrinsic Innovation LLC

// Package release defines the command that releases skills to the catalog.
package release

import (
	"fmt"
	"log"
	"strings"

	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
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
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/directupload"
	"intrinsic/skills/tools/skill/cmd/skillio"
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

func idVersionFromRequest(req *skillcatalogpb.CreateSkillRequest) (string, error) {
	id := req.GetProcessedSkillManifest().GetMetadata().GetId()
	return idutils.IDVersionFrom(id.GetPackage(), id.GetName(), req.GetVersion())
}

func remoteOpt() remote.Option {
	return remote.WithAuthFromKeychain(google.Keychain)
}

var releaseExamples = strings.Join(
	[]string{
		`Upload and release a skill image to the skill catalog:
  $ inctl skill release /path/to/skill.bundle.tar ...`,
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
		project := clientutils.ResolveCatalogProjectFromInctl(cmdFlags)

		useDirectUpload := true

		conn, err := clientutils.DialCatalogFromInctl(cmd, cmdFlags)
		if err != nil {
			return fmt.Errorf("failed to create client connection: %v", err)
		}
		defer conn.Close()

		transferer := imageTransferer(imageTransfererOpts{
			cmd:             cmd,
			conn:            conn,
			useDirectUpload: useDirectUpload,
		})

		ps, err := skillio.ProcessFile(skillio.ProcessSkillOpts{
			Target:  target,
			Version: cmdFlags.GetFlagVersion(),
			RegistryOpts: imageutils.RegistryOptions{
				URI:        imageutils.GetRegistry(project),
				Transferer: transferer,
			},
			DryRun: dryRun,
		})
		if err != nil {
			return err
		}
		req := &skillcatalogpb.CreateSkillRequest{
			ManifestType: &skillcatalogpb.CreateSkillRequest_ProcessedSkillManifest{
				ProcessedSkillManifest: ps.ProcessedManifest,
			},
			Version:      cmdFlags.GetFlagVersion(),
			Default:      cmdFlags.GetFlagDefault(),
			OrgPrivate:   cmdFlags.GetFlagOrgPrivate(),
			ReleaseNotes: cmdFlags.GetFlagReleaseNotes(),
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
	cmdFlags.AddFlagReleaseNotes("skill")
	cmdFlags.AddFlagVersion("skill")

}
