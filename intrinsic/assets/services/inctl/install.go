// Copyright 2023 Intrinsic Innovation LLC

// Package install defines the service install command that sideloads a service.
package install

import (
	"fmt"
	"log"
	"time"

	lrogrpcpb "cloud.google.com/go/longrunning/autogen/longrunningpb"
	lropb "cloud.google.com/go/longrunning/autogen/longrunningpb"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/spf13/cobra"
	"google.golang.org/grpc/status"
	"intrinsic/assets/bundleio"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	iagrpcpb "intrinsic/assets/proto/installed_assets_go_grpc_proto"
	iapb "intrinsic/assets/proto/installed_assets_go_grpc_proto"
	"intrinsic/skills/tools/resource/cmd/bundleimages"
	"intrinsic/skills/tools/skill/cmd/directupload"
)

const (
	policyList = "\"add_new_only\", \"update_unused\", and \"update_compatible\""
)

func asPolicy(value string) (iapb.UpdatePolicy, error) {
	switch value {
	case "":
		return iapb.UpdatePolicy_UPDATE_POLICY_UNSPECIFIED, nil
	case "add_new_only":
		return iapb.UpdatePolicy_UPDATE_POLICY_ADD_NEW_ONLY, nil
	case "update_unused":
		return iapb.UpdatePolicy_UPDATE_POLICY_UPDATE_UNUSED, nil
	case "update_compatible":
		return iapb.UpdatePolicy_UPDATE_POLICY_UPDATE_COMPATIBLE, nil
	}
	return iapb.UpdatePolicy_UPDATE_POLICY_UNSPECIFIED, fmt.Errorf("%q provided for --%v is invalid; valid values are %v", value, cmdutils.KeyPolicy, policyList)
}

// GetCommand returns a command to install (sideload) the service bundle.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{
		Use:   "install bundle",
		Short: "Install service",
		Example: `
	Install a service to the specified solution:
	$ inctl service install abc/service_bundle.tar \
			--org my_org \
			--solution my_solution_id

	To find a running solution's id, run:
	$ inctl solution list --project my-project --filter "running_on_hw,running_in_sim" --output json

	The service can also be installed by specifying the cluster on which the solution is running:
	$ inctl service install abc/service_bundle.tar \
			--org my_org \
			--cluster my_cluster
	`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			target := args[0]

			policy, err := asPolicy(flags.GetFlagPolicy())
			if err != nil {
				return err
			}

			ctx, conn, address, err := clientutils.DialClusterFromInctl(ctx, flags)
			if err != nil {
				return err
			}
			defer conn.Close()

			// Determine the image transferer to use. Default to direct injection into the cluster.
			registry := flags.GetFlagRegistry()
			remoteOpt, err := clientutils.RemoteOpt(flags)
			if err != nil {
				return err
			}
			transfer := imagetransfer.RemoteTransferer(remote.WithContext(ctx), remoteOpt)
			if !flags.GetFlagSkipDirectUpload() {
				opts := []directupload.Option{
					directupload.WithDiscovery(directupload.NewFromConnection(conn)),
					directupload.WithOutput(cmd.OutOrStdout()),
				}
				if registry != "" {
					// User set external registry, so we can use it as failover.
					opts = append(opts, directupload.WithFailOver(transfer))
				} else {
					// Fake name that ends in .local in order to indicate that this is local, directly
					// uploaded image.
					registry = "direct.upload.local"
				}
				transfer = directupload.NewTransferer(ctx, opts...)
			}

			opts := bundleio.ProcessServiceOpts{
				ImageProcessor: bundleimages.CreateImageProcessor(flags.CreateRegistryOptsWithTransferer(ctx, transfer, registry)),
			}
			manifest, err := bundleio.ProcessService(target, opts)
			if err != nil {
				return fmt.Errorf("could not read bundle file %q: %v", target, err)
			}

			id, err := idutils.IDFromProto(manifest.GetMetadata().GetId())
			if err != nil {
				return fmt.Errorf("invalid id: %v", err)
			}
			log.Printf("Installing service %q", id)

			client := iagrpcpb.NewInstalledAssetsClient(conn)
			authCtx := clientutils.AuthInsecureConn(ctx, address, flags.GetFlagProject())

			// This needs an authorized context to pull from the catalog if not available.
			op, err := client.CreateInstalledAssets(authCtx, &iapb.CreateInstalledAssetsRequest{
				Policy: policy,
				Assets: []*iapb.CreateInstalledAssetsRequest_Asset{
					&iapb.CreateInstalledAssetsRequest_Asset{
						Variant: &iapb.CreateInstalledAssetsRequest_Asset_Service{
							Service: manifest,
						},
					},
				},
			})
			if err != nil {
				return fmt.Errorf("could not install the service: %v", err)
			}

			log.Printf("Awaiting completion of the installation")
			lroClient := lrogrpcpb.NewOperationsClient(conn)
			for !op.GetDone() {
				time.Sleep(15 * time.Millisecond)
				op, err = lroClient.GetOperation(ctx, &lropb.GetOperationRequest{
					Name: op.GetName(),
				})
				if err != nil {
					return fmt.Errorf("unable to check status of installation: %v", err)
				}
			}

			if err := status.ErrorProto(op.GetError()); err != nil {
				return fmt.Errorf("installation failed: %w", err)
			}

			log.Printf("Finished installing %q", id)

			return nil
		},
	}

	flags.SetCommand(cmd)
	flags.AddFlagsAddressClusterSolution()
	flags.AddFlagsProjectOrg()
	flags.AddFlagRegistry()
	flags.AddFlagsRegistryAuthUserPassword()
	flags.AddFlagSkipDirectUpload("service")
	flags.OptionalString(cmdutils.KeyPolicy, "", fmt.Sprintf("The update policy to be used to install the provided asset. Can be %v", policyList))

	return cmd
}
