// Copyright 2023 Intrinsic Innovation LLC

// Package install defines the service install command that sideloads a service.
package install

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"google.golang.org/protobuf/proto"
	"intrinsic/assets/bundleio"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	installergrpcpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	"intrinsic/skills/tools/resource/cmd/bundleimages"
)

// GetCommand returns a command to install (sideload) the service bundle.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{
		Use:   "install bundle",
		Short: "Install service",
		Example: `
	Upload the relevant artifacts to a container registry and CAS, and then install the service
	$ inctl service install abc/service_bundle.tar \
			--registry gcr.io/my-registry \
			--project my_project \
			--solution my_solution_id

			To find a running solution's id, run:
			$ inctl solution list --project my-project --filter "running_on_hw,running_in_sim" --output json

	`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			target := args[0]

			ctx, conn, _, err := clientutils.DialClusterFromInctl(ctx, flags)
			if err != nil {
				return err
			}
			defer conn.Close()

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

			pkg := manifest.GetMetadata().GetId().GetPackage()
			name := manifest.GetMetadata().GetId().GetName()
			// No deterministic data is available for generating the sideloaded version here. Use a random
			// string instead to keep the version unique. Ideally we would probably use the digest of the
			// skill image or similar.
			version, err := idutils.UnreleasedVersion(idutils.UnreleasedAssetKindSideloaded, manifestBytes)
			if err != nil {
				return fmt.Errorf("could not create version: %v", err)
			}
			idVersion, err := idutils.IDVersionFrom(pkg, name, version)
			if err != nil {
				return fmt.Errorf("could not create id_version: %w", err)
			}
			log.Printf("Installing service %q", idVersion)

			client := installergrpcpb.NewInstallerServiceClient(conn)
			installerCtx := ctx

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
	flags.AddFlagsAddressClusterSolution()
	flags.AddFlagsProjectOrg()
	flags.AddFlagRegistry()
	flags.AddFlagsRegistryAuthUserPassword()

	return cmd
}
