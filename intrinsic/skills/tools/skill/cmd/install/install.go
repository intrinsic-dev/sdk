// Copyright 2023 Intrinsic Innovation LLC

// Package install defines the skill command which installs a skill.
package install

import (
	"fmt"
	"log"

	"github.com/pborman/uuid"
	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	imagepb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/directupload"
	"intrinsic/skills/tools/skill/cmd/skillio"
	"intrinsic/skills/tools/skill/cmd/waitforskill"
)

var cmdFlags = cmdutils.NewCmdFlags()

func installRequest(ps *skillio.ProcessedSkill, version string) (*installerpb.InstallContainerAddonRequest, error) {
	if ps.ProcessedManifest != nil {
		return &installerpb.InstallContainerAddonRequest{
			Id:      ps.ID,
			Version: version,
			Type:    installerpb.AddonType_ADDON_TYPE_SKILL,
			Images: []*imagepb.Image{
				ps.ProcessedManifest.GetAssets().GetImage(),
			},
		}, nil
	}
	if ps.Image != nil {
		return &installerpb.InstallContainerAddonRequest{
			Id:      ps.ID,
			Version: version,
			Type:    installerpb.AddonType_ADDON_TYPE_SKILL,
			Images: []*imagepb.Image{
				ps.Image,
			},
		}, nil
	}
	return nil, fmt.Errorf("could not build a complete install skill request for %q: missing required information", ps.ID)
}

var installCmd = &cobra.Command{
	Use:   "install --type=TYPE TARGET",
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

		timeout, timeoutStr, err := cmdFlags.GetFlagSideloadStartTimeout()
		if err != nil {
			return err
		}

		ctx, conn, address, err := clientutils.DialClusterFromInctl(ctx, cmdFlags)
		if err != nil {
			return err
		}
		defer conn.Close()

		// Install the skill to the registry
		flagRegistry := cmdFlags.GetFlagRegistry()

		// Upload skill, directly, to workcell, with fail-over legacy transfer if possible
		remoteOpt, err := clientutils.RemoteOpt(cmdFlags)
		if err != nil {
			return err
		}
		transfer := imagetransfer.RemoteTransferer(remoteOpt)
		if !cmdFlags.GetFlagSkipDirectUpload() {
			opts := []directupload.Option{
				directupload.WithDiscovery(directupload.NewFromConnection(conn)),
				directupload.WithOutput(command.OutOrStdout()),
			}
			if flagRegistry != "" {
				// User set external registry, so we can use it as fail-over.
				opts = append(opts, directupload.WithFailOver(transfer))
			} else {
				// Fake name that ends in .local in order to indicate that this is local, directly uploaded
				// image.
				flagRegistry = "direct.upload.local"
			}
			transfer = directupload.NewTransferer(ctx, opts...)
		}

		// No deterministic data is available for generating the sideloaded version here. Use a random
		// string instead to keep the version unique. Ideally we would probably use the digest of the
		// skill image or similar.
		version := fmt.Sprintf("0.0.1+%s", uuid.New())

		authUser, authPwd := cmdFlags.GetFlagsRegistryAuthUserPassword()
		ps, err := skillio.ProcessFile(skillio.ProcessSkillOpts{
			Target:  target,
			Version: version,
			RegistryOpts: imageutils.RegistryOptions{
				URI:        flagRegistry,
				Transferer: transfer,
				BasicAuth: imageutils.BasicAuth{
					User: authUser,
					Pwd:  authPwd,
				},
			},
			AllowMissingManifest: true,
			DryRun:               false,
		})
		if err != nil {
			return err
		}
		req, err := installRequest(ps, version)
		if err != nil {
			return fmt.Errorf("could not generate installer request: %w", err)
		}
		pkg, err := idutils.PackageFrom(req.GetId())
		if err != nil {
			return fmt.Errorf("could not parse package from ID: %w", err)
		}
		name, err := idutils.NameFrom(req.GetId())
		if err != nil {
			return fmt.Errorf("could not parse name from ID: %w", err)
		}
		idVersion, err := idutils.IDVersionFrom(pkg, name, version)
		log.Printf("Installing skill %q", idVersion)

		installerCtx := ctx

		err = imageutils.InstallContainer(installerCtx,
			&imageutils.InstallContainerParams{
				Address:    address,
				Connection: conn,
				Request:    req,
			})
		if err != nil {
			return fmt.Errorf("could not install the skill: %w", err)
		}
		log.Printf("Finished installing, skill container is now starting")

		if timeout == 0 {
			return nil
		}

		log.Printf("Waiting for the skill to be available for a maximum of %s", timeoutStr)
		err = waitforskill.WaitForSkill(ctx,
			&waitforskill.Params{
				Connection:     conn,
				SkillID:        req.GetId(),
				SkillIDVersion: idVersion,
				WaitDuration:   timeout,
			})
		if err != nil {
			return fmt.Errorf("failed waiting for skill: %w", err)
		}
		log.Printf("The skill is now available.")
		return nil
	},
}

func init() {
	cmd.SkillCmd.AddCommand(installCmd)
	cmdFlags.SetCommand(installCmd)

	cmdFlags.AddFlagsAddressClusterSolution()
	cmdFlags.AddFlagsProjectOrg()
	cmdFlags.AddFlagRegistry()
	cmdFlags.AddFlagsRegistryAuthUserPassword()
	cmdFlags.AddFlagSideloadStartTimeout("skill")
	cmdFlags.AddFlagSkipDirectUpload("skill")
}
