// Copyright 2023 Intrinsic Innovation LLC

// Package install defines the skill command which installs a skill.
package install

import (
	"fmt"
	"log"

	lrogrpcpb "cloud.google.com/go/longrunning/autogen/longrunningpb"
	lropb "cloud.google.com/go/longrunning/autogen/longrunningpb"
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
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/directupload"
	"intrinsic/skills/tools/skill/cmd/waitforskill"
)

func getCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{
		Use:   "install TARGET",
		Short: "Install a skill",
		Example: `Upload skill image to a container registry, and install the skill
$ inctl skill install abc/skill.bundle.tar --registry=gcr.io/my-registry --cluster=my_cluster

Use the solution flag to automatically resolve the cluster (requires the solution to run)
$ inctl skill install abc/skill.bundle.tar --solution=my-solution
`,
		Args: cobra.ExactArgs(1),
		Aliases: []string{
			"load",
			"start",
		},
		RunE: func(command *cobra.Command, args []string) error {
			ctx := command.Context()
			target := args[0]

			policy, err := flags.GetFlagPolicy()
			if err != nil {
				return err
			}

			timeout, timeoutStr, err := flags.GetFlagSideloadStartTimeout()
			if err != nil {
				return err
			}

			ctx, conn, address, err := clientutils.DialClusterFromInctl(ctx, flags)
			if err != nil {
				return err
			}
			defer conn.Close()

			// Install the skill to the registry
			registry := flags.GetFlagRegistry()

			// Upload skill, directly, to workcell, with fail-over legacy transfer if possible
			remoteOpt, err := clientutils.RemoteOpt(flags)
			if err != nil {
				return err
			}
			transfer := imagetransfer.RemoteTransferer(remoteOpt)
			if !flags.GetFlagSkipDirectUpload() {
				opts := []directupload.Option{
					directupload.WithDiscovery(directupload.NewFromConnection(conn)),
					directupload.WithOutput(command.OutOrStdout()),
				}
				if registry != "" {
					// User set external registry, so we can use it as failover.
					opts = append(opts, directupload.WithFailOver(transfer))
				} else {
					// Fake name that ends in .local in order to indicate that this is local, directly uploaded
					// image.
					registry = "direct.upload.local"
				}
				transfer = directupload.NewTransferer(ctx, opts...)
			}
			manifest, err := bundleio.ProcessSkill(target, bundleio.ProcessSkillOpts{
				ImageProcessor: bundleimages.CreateImageProcessor(flags.CreateRegistryOptsWithTransferer(ctx, transfer, registry)),
			})
			if err != nil {
				return fmt.Errorf("could not read bundle file %q: %v", target, err)
			}

			id, err := idutils.IDFromProto(manifest.GetMetadata().GetId())
			if err != nil {
				return fmt.Errorf("invalid id: %v", err)
			}
			log.Printf("Installing skill %q", id)

			client := iagrpcpb.NewInstalledAssetsClient(conn)
			authCtx := clientutils.AuthInsecureConn(ctx, address, flags.GetFlagProject())

			// This needs an authorized context to pull from the catalog if not available.
			op, err := client.CreateInstalledAsset(authCtx, &iapb.CreateInstalledAssetRequest{
				Policy: policy,
				Asset: &iapb.CreateInstalledAssetRequest_Asset{
					Variant: &iapb.CreateInstalledAssetRequest_Asset_Skill{
						Skill: manifest,
					},
				},
			})
			if err != nil {
				return fmt.Errorf("could not install the skill: %v", err)
			}

			log.Printf("Awaiting completion of the installation")
			lroClient := lrogrpcpb.NewOperationsClient(conn)
			for !op.GetDone() {
				op, err = lroClient.WaitOperation(ctx, &lropb.WaitOperationRequest{
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

			if timeout == 0 {
				return nil
			}

			asset := &iapb.InstalledAsset{}
			if err := op.GetResponse().UnmarshalTo(asset); err != nil {
				return fmt.Errorf("unable to interpret the response: %w", err)
			}

			log.Printf("Waiting for the skill to be available for a maximum of %s", timeoutStr)
			if err := waitforskill.WaitForSkill(ctx, &waitforskill.Params{
				Connection:     conn,
				SkillID:        idutils.IDFromProtoUnchecked(asset.GetMetadata().GetIdVersion().GetId()),
				SkillIDVersion: idutils.IDVersionFromProtoUnchecked(asset.GetMetadata().GetIdVersion()),
				WaitDuration:   timeout,
			}); err != nil {
				return fmt.Errorf("failed waiting for skill: %w", err)
			}
			log.Printf("The skill is now available.")

			return nil
		},
	}

	flags.SetCommand(cmd)
	flags.AddFlagsAddressClusterSolution()
	flags.AddFlagPolicy("skill")
	flags.AddFlagsProjectOrg()
	flags.AddFlagRegistry()
	flags.AddFlagsRegistryAuthUserPassword()
	flags.AddFlagSideloadStartTimeout("skill")
	flags.AddFlagSkipDirectUpload("skill")

	return cmd
}

func init() {
	cmd.SkillCmd.AddCommand(getCommand())
}
