// Copyright 2023 Intrinsic Innovation LLC

// Package release defines the command that releases skills to the catalog.
package release

import (
	"context"
	"fmt"
	"strings"

	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	"intrinsic/assets/bundleio"
	acgrpcpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	acpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	atpb "intrinsic/assets/proto/asset_type_go_proto"
	mpb "intrinsic/assets/proto/metadata_go_proto"
	releasetagpb "intrinsic/assets/proto/release_tag_go_proto"
	psmpb "intrinsic/skills/proto/processed_skill_manifest_go_proto"
	"intrinsic/skills/tools/resource/cmd/bundleimages"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/directupload"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
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

func release(ctx context.Context, client acgrpcpb.AssetCatalogClient, req *acpb.CreateAssetRequest, ignoreExisting bool, printer printer.Printer) error {
	if _, err := client.CreateAsset(ctx, req); err != nil {
		if s, ok := status.FromError(err); ok && cmdFlags.GetFlagIgnoreExisting() && s.Code() == codes.AlreadyExists {
			printer.PrintS("Skipping release: skill already exists in the catalog")
			return nil
		}
		return fmt.Errorf("could not release the skill :%w", err)
	}
	printer.PrintS("Finished releasing the skill")
	return nil
}

func processAsset(target string, transferer imagetransfer.Transferer, flags *cmdutils.CmdFlags) (*acpb.Asset, error) {
	releaseTag := releasetagpb.ReleaseTag_RELEASE_TAG_UNSPECIFIED
	if flags.GetFlagDefault() {
		releaseTag = releasetagpb.ReleaseTag_RELEASE_TAG_DEFAULT
	}

	if flags.GetFlagDryRun() {
		manifest, err := bundleio.ReadSkillManifest(target)
		if err != nil {
			return nil, fmt.Errorf("failed to read skill manifest from bundle: %v", err)
		}
		id := manifest.GetId()
		idVersion, err := idutils.IDVersionProtoFrom(id.GetPackage(), id.GetName(), flags.GetFlagVersion())
		if err != nil {
			return nil, err
		}
		return &acpb.Asset{
			Metadata: &mpb.Metadata{
				IdVersion:     idVersion,
				AssetType:     atpb.AssetType_ASSET_TYPE_SKILL,
				DisplayName:   manifest.GetDisplayName(),
				Documentation: manifest.GetDocumentation(),
				Vendor:        manifest.GetVendor(),
				ReleaseNotes:  flags.GetFlagReleaseNotes(),
				ReleaseTag:    releaseTag,
			},
		}, nil
	}

	opts := bundleio.ProcessSkillOpts{
		ImageProcessor: bundleimages.CreateImageProcessor(imageutils.RegistryOptions{
			Transferer: transferer,
			URI:        imageutils.GetRegistry(clientutils.ResolveCatalogProjectFromInctl(flags)),
		}),
	}
	psm, err := bundleio.ProcessSkill(target, opts)
	if err != nil {
		return nil, fmt.Errorf("failed to process skill bundle: %v", err)
	}
	metadata := psm.GetMetadata()
	idVersion, err := idutils.IDVersionProtoFrom(metadata.GetId().GetPackage(), metadata.GetId().GetName(), flags.GetFlagVersion())
	if err != nil {
		return nil, err
	}
	return &acpb.Asset{
		Metadata: &mpb.Metadata{
			IdVersion:     idVersion,
			AssetType:     atpb.AssetType_ASSET_TYPE_SKILL,
			DisplayName:   metadata.GetDisplayName(),
			Documentation: metadata.GetDocumentation(),
			Vendor:        metadata.GetVendor(),
			ReleaseNotes:  flags.GetFlagReleaseNotes(),
			ReleaseTag:    releaseTag,
		},
		DeploymentData: &acpb.Asset_AssetDeploymentData{
			AssetSpecificDeploymentData: &acpb.Asset_AssetDeploymentData_SkillSpecificDeploymentData{
				SkillSpecificDeploymentData: &acpb.Asset_SkillDeploymentData{
					Manifest: psm,
				},
			},
		},
	}, nil
}

func buildCreateAssetRequest(psm *psmpb.ProcessedSkillManifest, flags *cmdutils.CmdFlags) (*acpb.CreateAssetRequest, error) {
	version := flags.GetFlagVersion()
	metadata := psm.GetMetadata()
	idVersion, err := idutils.IDVersionProtoFrom(metadata.GetId().GetPackage(), metadata.GetId().GetName(), version)
	if err != nil {
		return nil, err
	}
	releaseTag := releasetagpb.ReleaseTag_RELEASE_TAG_UNSPECIFIED
	if flags.GetFlagDefault() {
		releaseTag = releasetagpb.ReleaseTag_RELEASE_TAG_DEFAULT
	}
	return &acpb.CreateAssetRequest{
		Asset: &acpb.Asset{
			Metadata: &mpb.Metadata{
				IdVersion:     idVersion,
				AssetType:     atpb.AssetType_ASSET_TYPE_SKILL,
				DisplayName:   metadata.GetDisplayName(),
				Documentation: metadata.GetDocumentation(),
				Vendor:        metadata.GetVendor(),
				ReleaseNotes:  flags.GetFlagReleaseNotes(),
				ReleaseTag:    releaseTag,
			},
			DeploymentData: &acpb.Asset_AssetDeploymentData{
				AssetSpecificDeploymentData: &acpb.Asset_AssetDeploymentData_SkillSpecificDeploymentData{
					SkillSpecificDeploymentData: &acpb.Asset_SkillDeploymentData{
						Manifest: psm,
					},
				},
			},
		},
		OrgPrivate: proto.Bool(flags.GetFlagOrgPrivate()),
	}, nil
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

		useDirectUpload := true

		var conn *grpc.ClientConn
		var transferer imagetransfer.Transferer
		if !dryRun {
			var err error
			conn, err = clientutils.DialCatalogFromInctl(cmd, cmdFlags)
			if err != nil {
				return fmt.Errorf("failed to create client connection: %v", err)
			}
			defer conn.Close()
			transferer = imageTransferer(imageTransfererOpts{
				cmd:             cmd,
				conn:            conn,
				useDirectUpload: useDirectUpload,
			})
		}

		asset, err := processAsset(target, transferer, cmdFlags)
		if err != nil {
			return err
		}
		printer, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}
		idVersion := idutils.IDVersionFromProtoUnchecked(asset.GetMetadata().GetIdVersion())
		printer.PrintSf("Releasing skill %q to the skill catalog", idVersion)
		if dryRun {
			printer.PrintS("Skipping call to skill catalog (dry-run)")
			return nil
		}
		client := acgrpcpb.NewAssetCatalogClient(conn)
		req := &acpb.CreateAssetRequest{
			Asset:      asset,
			OrgPrivate: proto.Bool(cmdFlags.GetFlagOrgPrivate()),
		}
		return release(cmd.Context(), client, req, cmdFlags.GetFlagIgnoreExisting(), printer)
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
