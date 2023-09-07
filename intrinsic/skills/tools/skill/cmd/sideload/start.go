// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package start defines the skill start command which installs a skill.
package start

import (
	"encoding/base32"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/google/go-containerregistry/pkg/authn"
	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/google/uuid"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	imagepb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd/cmd"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/imagetransfer"
	"intrinsic/skills/tools/skill/cmd/imageutil"
	"intrinsic/skills/tools/skill/cmd/registry"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
	"intrinsic/skills/tools/skill/cmd/waitforskill"
)

const (
	keyAuthUser         = "auth_user"
	keyAuthPassword     = "auth_password"
	keyContext          = "context"
	keyInstallerAddress = "installer_address"
	keyRegistry         = "registry"
	keyType             = "type"
	keyTimeout          = "timeout"
)

var viperLocal = viper.New()

func parseNonNegativeDuration(durationStr string) (time.Duration, error) {
	duration, err := time.ParseDuration(durationStr)
	if err != nil {
		return 0, fmt.Errorf("parsing duration: %w", err)
	}
	if duration < 0 {
		return 0, fmt.Errorf("duration must not be negative, but got %q", durationStr)
	}
	return duration, nil
}

func createSideloadedSkillIDVersion() string {
	id := uuid.New()
	return cmd.SideloadedSkillPrefix + strings.Replace(base32.StdEncoding.EncodeToString(id[:]), "=", "", -1)
}

func remoteOpt() remote.Option {
	if len(viperLocal.GetString(keyAuthUser)) != 0 && len(viperLocal.GetString(keyAuthPassword)) != 0 {
		return remote.WithAuth(authn.FromConfig(authn.AuthConfig{
			Username: viperLocal.GetString(keyAuthUser),
			Password: viperLocal.GetString(keyAuthPassword),
		}))
	}
	return remote.WithAuthFromKeychain(google.Keychain)
}

var startCmd = &cobra.Command{
	Use:   "start --type=TYPE TARGET",
	Short: "Install a skill",
	Example: `Build a skill, upload it to a container registry, and install the skill
$ inctl skill start --type=build //abc:skill.tar --registry=gcr.io/my-registry --context=minikube

Upload skill image to a container registry, and install the skill
$ inctl skill start --type=archive abc/skill.tar --registry=gcr.io/my-registry --context=minikube

Install skill using an image that has already been pushed to the container registry
$ inctl skill start --type=image gcr.io/my-workcell/abc@sha256:20ab4f --context=minikube

Use the solution flag to automatically resolve the context (requires the solution to run)
$ inctl skill start --type=image gcr.io/my-workcell/abc@sha256:20ab4f --solution=my-solution
`,
	Args: cobra.ExactArgs(1),
	RunE: func(command *cobra.Command, args []string) error {
		target := args[0]

		timeoutStr := viperLocal.GetString(keyTimeout)
		timeout, err := parseNonNegativeDuration(timeoutStr)
		if err != nil {
			return fmt.Errorf("invalid value passed for --timeout: %w", err)
		}

		imgpb, installerParams, err := registry.PushSkill(target, registry.PushOptions{
			AuthUser:   viperLocal.GetString(keyAuthUser),
			AuthPwd:    viperLocal.GetString(keyAuthPassword),
			Registry:   viperLocal.GetString(keyRegistry),
			Type:       viperLocal.GetString(keyType),
			Transferer: imagetransfer.RemoteTransferer(remoteOpt()),
		})
		if err != nil {
			return fmt.Errorf("could not push target %q to the container registry: %v", target, err)
		}

		k8sContext := viperLocal.GetString(keyContext)
		installerAddress := viperLocal.GetString(keyInstallerAddress)
		solution := viperLocal.GetString(cmd.KeySolution)
		project := viper.GetString(cmd.KeyProject)

		ctx, conn, err := dialerutil.DialConnectionCtx(command.Context(), dialerutil.DialInfoParams{
			Address:  installerAddress,
			CredName: project,
		})
		if err != nil {
			return fmt.Errorf("could not create connection: %w", err)
		}
		defer conn.Close()

		cluster, err := solutionutil.GetClusterNameFromSolutionOrDefault(
			ctx,
			conn,
			solution,
			k8sContext,
		)
		if err != nil {
			return fmt.Errorf("could not resolve solution to cluster: %w", err)
		}

		// Install the skill to the registry
		ctx, conn, err = dialerutil.DialConnectionCtx(command.Context(), dialerutil.DialInfoParams{
			Address:  installerAddress,
			Cluster:  cluster,
			CredName: project,
		})
		if err != nil {
			return fmt.Errorf("could not establish connection: %w", err)
		}

		skillVersion := "0.0.1+" + createSideloadedSkillIDVersion()
		skillIDVersion := installerParams.SkillID + "." + skillVersion
		log.Printf("Installing skill %q using the installer service at %q", skillIDVersion, viperLocal.GetString(keyInstallerAddress))
		err = imageutil.InstallContainer(ctx,
			&imageutil.InstallContainerParams{
				Address:    viperLocal.GetString(keyInstallerAddress),
				Connection: conn,
				Request: &installerpb.InstallContainerAddonRequest{
					Id:      installerParams.SkillID,
					Version: skillVersion,
					Type:    installerpb.AddonType_ADDON_TYPE_SKILL,
					Images: []*imagepb.Image{
						imgpb,
					},
				},
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
				Address:        installerAddress,
				Connection:     conn,
				SkillID:        installerParams.SkillID,
				SkillIDVersion: skillIDVersion,
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
	cmd.SkillCmd.AddCommand(startCmd)
	startCmd.PersistentFlags().String(keyAuthUser, "", "(optional) The username used to access the private skill registry.")
	startCmd.PersistentFlags().String(keyAuthPassword, "", "(optional) The password used to authenticate private container registry access.")
	startCmd.PersistentFlags().String(cmd.KeySolution, "", `The solution into which the skill should be loaded. Needs to run on a cluster.
You can set the environment variable INTRINSIC_SOLUTION=solution to set a default solution.`)
	startCmd.PersistentFlags().StringP(keyContext, "c", "", `The Kubernetes cluster to use. Not required if using localhost for the installer_address.
You can set the environment variable INTRINSIC_CONTEXT=cluster to set a default cluster.`)
	startCmd.PersistentFlags().String(keyInstallerAddress, "xfa.lan:17080", `The address of the installer service. When not running the cluster on localhost, this should be the address of the relay
(example: dns:///www.endpoints.<gcloud_project_name>.cloud.goog:443).
You can set the environment variable INTRINSIC_INSTALLER_ADDRESS=address to change the default address.`)
	startCmd.PersistentFlags().String(keyRegistry, "", `The container registry. This option is ignored when --type=image.
You can set the environment variable INTRINSIC_REGISTRY=registry to set a default registry.`)
	startCmd.PersistentFlags().String(keyType, "", fmt.Sprintf(`(required) The target's type:
%s	build target that creates a skill image
%s	file path pointing to an already-built image
%s	container image name`, imageutil.Build, imageutil.Archive, imageutil.Image))
	startCmd.PersistentFlags().String(keyTimeout, "180s", "Maximum time to wait for the skill to "+
		"become available in the cluster after starting it. Can be set to any valid duration "+
		"(\"60s\", \"5m\", ...) or to \"0\" to disable waiting.")

	startCmd.MarkPersistentFlagRequired(keyType)
	// Always required to resolve API key for authentication.
	startCmd.MarkPersistentFlagRequired(cmd.KeyProject)
	startCmd.MarkFlagsRequiredTogether(keyAuthUser, keyAuthPassword)
	startCmd.MarkFlagsMutuallyExclusive(keyContext, cmd.KeySolution)

	viperLocal.BindPFlag(keyAuthUser, startCmd.PersistentFlags().Lookup(keyAuthUser))
	viperLocal.BindPFlag(keyAuthPassword, startCmd.PersistentFlags().Lookup(keyAuthPassword))
	viperLocal.BindPFlag(keyContext, startCmd.PersistentFlags().Lookup(keyContext))
	viperLocal.BindPFlag(cmd.KeySolution, startCmd.PersistentFlags().Lookup(cmd.KeySolution))
	viperLocal.BindPFlag(keyInstallerAddress, startCmd.PersistentFlags().Lookup(keyInstallerAddress))
	viperLocal.BindPFlag(keyRegistry, startCmd.PersistentFlags().Lookup(keyRegistry))
	viperLocal.BindPFlag(keyType, startCmd.PersistentFlags().Lookup(keyType))
	viperLocal.BindPFlag(keyTimeout, startCmd.PersistentFlags().Lookup(keyTimeout))
	viperLocal.SetEnvPrefix("intrinsic")
	viperLocal.BindEnv(keyInstallerAddress)
	viperLocal.BindEnv(keyRegistry)
	viperLocal.BindEnv(cmd.KeyProject)
}
