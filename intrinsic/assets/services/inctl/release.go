// Copyright 2023 Intrinsic Innovation LLC

// Package release defines the service release command which releases a service to the catalog.
package release

import (
	"context"

	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
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
	"intrinsic/skills/tools/resource/cmd/bundleimages"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

func authOpt() remote.Option {
	return remote.WithAuthFromKeychain(google.Keychain)
}

func release(ctx context.Context, client acgrpcpb.AssetCatalogClient, req *acpb.CreateAssetRequest, ignoreExisting bool, printer printer.Printer) error {
	if _, err := client.CreateAsset(ctx, req); err != nil {
		if s, ok := status.FromError(err); ok && ignoreExisting && s.Code() == codes.AlreadyExists {
			printer.PrintS("Skipping release: service already exists in the catalog")
			return nil
		}
		return errors.Wrap(err, "could not release the service")
	}
	printer.PrintS("Finished releasing the service")
	return nil
}

func buildCreateAssetRequest(ctx context.Context, target string, flags *cmdutils.CmdFlags) (*acpb.CreateAssetRequest, error) {
	version := flags.GetFlagVersion()
	opts := bundleio.ProcessServiceOpts{
		ImageProcessor: bundleimages.CreateImageProcessor(imageutils.RegistryOptions{
			Transferer: imagetransfer.RemoteTransferer(remote.WithContext(ctx), authOpt()),
			URI:        imageutils.GetRegistry(clientutils.ResolveCatalogProjectFromInctl(flags)),
		}),
	}

	manifest, err := bundleio.ProcessService(target, opts)
	if err != nil {
		return nil, errors.Wrap(err, "could not read bundle file "+target)
	}
	metadata := manifest.GetMetadata()
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
				AssetType:     atpb.AssetType_ASSET_TYPE_SERVICE,
				AssetTag:      metadata.GetAssetTag(),
				DisplayName:   metadata.GetDisplayName(),
				Documentation: metadata.GetDocumentation(),
				Vendor:        metadata.GetVendor(),
				ReleaseNotes:  flags.GetFlagReleaseNotes(),
				ReleaseTag:    releaseTag,
			},
			AssetSpecificMetadata: &acpb.Asset_ServiceSpecificMetadata{
				ServiceSpecificMetadata: &acpb.Asset_ServiceMetadata{
					ServiceProtoPrefixes: manifest.GetServiceDef().GetServiceProtoPrefixes(),
				},
			},
			DeploymentData: &acpb.Asset_AssetDeploymentData{
				AssetSpecificDeploymentData: &acpb.Asset_AssetDeploymentData_ServiceSpecificDeploymentData{
					ServiceSpecificDeploymentData: &acpb.Asset_ServiceDeploymentData{
						Manifest: manifest,
					},
				},
			},
		},
		OrgPrivate: proto.Bool(flags.GetFlagOrgPrivate()),
	}, nil
}

// GetCommand returns command to release services.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()

	cmd := &cobra.Command{
		Use:   "release bundle.tar",
		Short: "Release a service to the catalog",
		Example: `
	Release a service to the catalog
	$ service release abc/bundle.tar --version=0.0.1
	`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			req, err := buildCreateAssetRequest(cmd.Context(), args[0], flags)
			if err != nil {
				return err
			}
			printer, err := printer.NewPrinter(root.FlagOutput)
			if err != nil {
				return err
			}
			idVersion, err := idutils.IDVersionFromProto(req.GetAsset().GetMetadata().GetIdVersion())
			if err != nil {
				return err
			}
			printer.PrintSf("Releasing service %q to the service catalog", idVersion)
			conn, err := clientutils.DialCatalogFromInctl(cmd, flags)
			if err != nil {
				return errors.Wrap(err, "could not dial catalog")
			}
			client := acgrpcpb.NewAssetCatalogClient(conn)
			if flags.GetFlagDryRun() {
				printer.PrintS("Skipping call to service catalog (dry-run)")
				return nil
			}
			return release(cmd.Context(), client, req, flags.GetFlagIgnoreExisting(), printer)
		},
	}
	flags.SetCommand(cmd)
	flags.AddFlagDefault("service")
	flags.AddFlagDryRun()
	flags.AddFlagIgnoreExisting("service")
	flags.AddFlagOrgPrivate()
	flags.AddFlagReleaseNotes("service")
	flags.AddFlagVersion("service")

	return cmd
}
