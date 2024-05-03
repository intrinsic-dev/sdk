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
	"intrinsic/skills/tools/skill/cmd/solutionutil"
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

			project := flags.GetFlagProject()
			org := flags.GetFlagOrganization()
			cluster, solution, err := flags.GetFlagsListClusterSolution()
			if err != nil {
				return fmt.Errorf("could not get flags (ie. address, cluster, solution): %v", err)
			}

			if solution != "" {
				// attempt to get cluster name from solution id
				ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
					CredName: project,
					CredOrg:  org,
				})
				if err != nil {
					return fmt.Errorf("could not create connection options for install service: %v", err)
				}
				defer conn.Close()

				cluster, err = solutionutil.GetClusterNameFromSolution(ctx, conn, solution)
				if err != nil {
					return fmt.Errorf("could not get cluster name from solution: %v", err)
				}
			}

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
				Cluster:  cluster,
				CredName: project,
				CredOrg:  org,
			})
			if err != nil {
				return fmt.Errorf("could not create connection options for the installer: %v", err)
			}


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
	flags.AddFlagsRegistryAuthUserPassword()
	flags.AddFlagsProjectOrg()
	flags.AddFlagRegistry()
	flags.AddFlagsListClusterSolution("service")

	return cmd
}
