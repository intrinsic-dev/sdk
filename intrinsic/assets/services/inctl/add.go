// Copyright 2023 Intrinsic Innovation LLC

// Package add defines the command which adds a service instance to the
// solution.
package add

import (
	"fmt"
	"log"
	"os"
	"time"

	oppb "cloud.google.com/go/longrunning/autogen/longrunningpb"
	"github.com/spf13/cobra"
	"google.golang.org/protobuf/proto"
	anypb "google.golang.org/protobuf/types/known/anypb"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	adgrpcpb "intrinsic/assets/proto/asset_deployment_go_grpc_proto"
	adpb "intrinsic/assets/proto/asset_deployment_go_grpc_proto"
	atpb "intrinsic/assets/proto/asset_type_go_proto"
	"intrinsic/assets/version"
	rrgrpcpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
)

const (
	keyConfig = "config"
	keyName   = "name"
)

// GetCommand returns a command to add a service instance to a solution.
func GetCommand() *cobra.Command {
	var flags = cmdutils.NewCmdFlags()
	var cmd = &cobra.Command{
		Use:   "add id|id_version",
		Short: "Add a service instance to a solution",
		Example: `
Add a particular service with a given name and configuration
$ inctl service add ai.intrinsic.basler_camera \
      --cluster=some_cluster_id \
      --name=my_instance --config=some_file.binpb"
`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			idOrIDVersion := args[0]
			name := flags.GetString(keyName)

			idv, err := idutils.IDOrIDVersionProtoFrom(idOrIDVersion)
			if err != nil {
				return fmt.Errorf("invalid identifier: %v", err)
			}
			if name == "" {
				name = idv.GetId().GetName()
			}

			var cfg *anypb.Any
			if f := flags.GetString(keyConfig); f != "" {
				content, err := os.ReadFile(f)
				if err != nil {
					return fmt.Errorf("failed to read configuration proto file %s: %v", f, err)
				}
				cfg = &anypb.Any{}
				if err := proto.Unmarshal(content, cfg); err != nil {
					return fmt.Errorf("could not unmarshal configuration proto: %v", err)
				}
			}

			ctx, conn, address, err := clientutils.DialClusterFromInctl(ctx, flags)
			if err != nil {
				return fmt.Errorf("could not create connection to cluster: %w", err)
			}
			defer conn.Close()

			if err := version.Autofill(ctx, rrgrpcpb.NewResourceRegistryClient(conn), idv); err != nil {
				return err
			}
			idVersion, err := idutils.IDVersionFromProto(idv)
			if err != nil {
				return err
			}

			log.Printf("Requesting %q be added as a service instance", name)
			client := adgrpcpb.NewAssetDeploymentServiceClient(conn)
			authCtx := clientutils.AuthInsecureConn(ctx, address, flags.GetFlagProject())

			// This needs an authorized context to pull from the catalog if not available.
			op, err := client.CreateResourceFromCatalog(authCtx, &adpb.CreateResourceFromCatalogRequest{
				TypeIdVersion: idVersion,
				Configuration: &adpb.ResourceInstanceConfiguration{
					Name:          name,
					Configuration: cfg,
				},
				AssetType: atpb.AssetType_ASSET_TYPE_SERVICE,
			})
			if err != nil {
				return fmt.Errorf("could not create service %q of id version %q: %v", name, idVersion, err)
			}

			log.Printf("Awaiting completion of the add operation")
			for !op.GetDone() {
				time.Sleep(15 * time.Millisecond)
				op, err = client.GetOperation(ctx, &oppb.GetOperationRequest{
					Name: op.GetName(),
				})
				if err != nil {
					return fmt.Errorf("unable to check status of create operation for %q: %v", name, err)
				}
			}

			if err := op.GetError(); err != nil {
				return fmt.Errorf("failed to add %q: %v", name, err)
			}

			log.Printf("Finished adding service %q", name)
			return nil
		},
	}

	flags.SetCommand(cmd)
	flags.AddFlagsAddressClusterSolution()
	flags.AddFlagsProjectOrg()
	flags.OptionalString(keyConfig, "", "The filename of a binary-serialized Any proto containing this services's configuration.")
	flags.OptionalString(keyName, "", "The name of this service instance.")

	return cmd
}
