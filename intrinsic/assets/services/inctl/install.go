// Copyright 2023 Intrinsic Innovation LLC

// Package install defines the service install command that sideloads a service.
package install

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"google.golang.org/protobuf/proto"
	"intrinsic/assets/bundleio"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	installergrpcpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	"intrinsic/skills/tools/resource/cmd/bundleimages"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/auth"
)

// GetCommand returns a command to install (sideload) the service bundle.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{
		Use:   "install bundle",
		Short: "Install service",
		Example: `
	Upload the relevant artifacts to a container registry and CAS, and then install the service
	$ inctl service install abc/service_bundle.tar --registry=gcr.io/my-registry --context=minikube
		--project=my_project
	`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			target := args[0]

			opts := bundleio.ProcessServiceOpts{
				ImageProcessor: bundleimages.CreateImageProcessor(flags.CreateRegistryOpts(ctx)),
			}

			manifest, err := bundleio.ProcessService(target, opts)
			if err != nil {
				return fmt.Errorf("could not read bundle file %q: %v", target, err)
			}
			manifestBytes, err := proto.Marshal(manifest)
			if err != nil {
				return fmt.Errorf("could not marshal manifest: %v", err)
			}
			version, err := idutils.UnreleasedVersion(idutils.UnreleasedAssetKindSideloaded, manifestBytes)
			if err != nil {
				return fmt.Errorf("could not create version: %v", err)
			}

			// Install the service to the registry
			ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
				Address:  flags.GetFlagInstallerAddress(),
				Cluster:  flags.GetFlagSideloadContext(),
				CredName: flags.GetFlagProject(),
				CredOrg:  flags.GetFlagOrganization(),
			})
			if err != nil {
				return fmt.Errorf("could not create connection options for the installer: %v", err)
			}

			log.Printf("Installing service using the installer at %q", flags.GetFlagInstallerAddress())

			client := installergrpcpb.NewInstallerServiceClient(conn)
			installerCtx := ctx
			if dialerutil.UseInsecureCredentials(flags.GetFlagInstallerAddress()) {
				// This returns a valid context at all times. We only log any errors here because we will
				// also install without authorization. This may mean that some features (namely persistence)
				// will not work as expected.
				if installerCtx, err = auth.NewStore().AuthorizeContext(ctx, flags.GetFlagProject()); err != nil {
					log.Printf("Warning: Could not find authentication information. Some features (such as persistence) may not work correctly. Try running 'inctl auth login --project %s' to authenticate.", flags.GetFlagProject())
				}
			}
			resp, err := client.InstallService(installerCtx, &installerpb.InstallServiceRequest{
				Manifest: manifest,
				Version:  version,
			})
			if err != nil {
				return fmt.Errorf("could not install the service: %v", err)
			}
			log.Printf("Finished installing the service: %q", resp.GetIdVersion())

			return nil
		},
	}

	flags.SetCommand(cmd)
	flags.AddFlagsRegistryAuthUserPassword()
	flags.AddFlagsProjectOrg()
	flags.AddFlagSideloadContext()
	flags.AddFlagInstallerAddress()
	flags.AddFlagRegistry()

	return cmd
}
