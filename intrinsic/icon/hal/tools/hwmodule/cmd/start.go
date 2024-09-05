// Copyright 2023 Intrinsic Innovation LLC

// Package start defines the hwmodule start command which installs an ICON hardware module.
package start

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	imagepb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	installerservicegrpcpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"

	"github.com/google/go-containerregistry/pkg/authn"
	"github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	"intrinsic/icon/hal/tools/hwmodule/cmd"
	"intrinsic/icon/hal/tools/hwmodule/cmd/imageutil"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/directupload"
)

var (
	flagAuthUser         string
	flagAuthPassword     string
	flagInstallerAddress string
	flagRegistryName     string
	flagTargetType       string
	flagSkipDirectUpload bool

	flagRtpcHostname            string
	flagHardwareModuleName      string
	flagHardwareModuleConfig    string
	flagRequiresAtemsys         bool
	flagRunningEthercatOss      bool
	flagRunWithRealtimePriority bool
	flagIsolateNetwork          bool
)

type installHardwareModuleParams struct {
	address      string
	registryName string
	authUser     string
	authPassword string
	image        v1.Image

	moduleName              string
	hardwareModuleConfig    *installerpb.IconHardwareModuleOptions_HardwareModuleConfig
	rtpcHostname            string
	requiresAtemsys         bool
	runningEthercatOss      bool
	runWithRealtimePriority bool
	isolateNetwork          bool
}

func installHardwareModule(params installHardwareModuleParams) error {
	installerParams, err := imageutil.GetIconHardwareModuleInstallerParams(params.image)
	if err != nil {
		return errors.Wrap(err, "could not extract installer labels from image object")
	}

	log.Printf("Installing hardware module %q using the installer service at %q", params.moduleName, params.address)
	conn, err := grpc.Dial(params.address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return fmt.Errorf("could not establish connection at address %s: %w", params.address, err)
	}
	defer conn.Close()

	// Get the sha256 hash string from the digest
	digest, err := params.image.Digest()
	if err != nil {
		return fmt.Errorf("could not get the sha256 of the image: %w", err)
	}

	if len(params.authUser) != 0 && len(params.authPassword) != 0 {
		log.Printf("Private registry username and password given: auth_username is %q", params.authUser)
	}

	client := installerservicegrpcpb.NewInstallerServiceClient(conn)
	ctx := context.Background()
	request := &installerpb.InstallContainerAddonRequest{
		Name: params.moduleName,
		Type: installerpb.AddonType_ADDON_TYPE_ICON_HARDWARE_MODULE,
		Images: []*imagepb.Image{
			&imagepb.Image{
				Registry:     params.registryName,
				Name:         installerParams.ImageName,
				Tag:          "@" + digest.String(),
				AuthUser:     params.authUser,
				AuthPassword: params.authPassword,
			},
		},
		AddonOptions: &installerpb.InstallContainerAddonRequest_IconHardwareModuleOptions{
			IconHardwareModuleOptions: &installerpb.IconHardwareModuleOptions{
				HardwareModuleConfig:    params.hardwareModuleConfig,
				RequiresAtemsys:         params.requiresAtemsys,
				RunningEthercatOss:      params.runningEthercatOss,
				RtpcNodeHostname:        params.rtpcHostname,
				RunWithRealtimePriority: params.runWithRealtimePriority,
				IsolateNetwork:          params.isolateNetwork,
			},
		},
	}
	_, err = client.InstallContainerAddon(ctx, request)
	if status.Code(err) == codes.Unimplemented {
		return fmt.Errorf("installer service not implemented at server side (is it running and accessible at %s): %w", params.address, err)
	} else if err != nil {
		return fmt.Errorf("could not install the hardware module: %w", err)
	}
	log.Printf("Finished installing the hardware module: image name is %q", installerParams.ImageName)
	return nil
}

func remoteOpts(authUser, authPassword string) remote.Option {
	if len(authUser) != 0 && len(authPassword) != 0 {
		return remote.WithAuth(authn.FromConfig(authn.AuthConfig{
			Username: authUser,
			Password: authPassword,
		}))
	}
	return remote.WithAuthFromKeychain(google.Keychain)
}

var startCmd = &cobra.Command{
	Use:   "start [target]",
	Short: "Install an ICON hardware module",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		target := args[0]

		installerAddress := flagInstallerAddress
		targetType := imageutils.TargetType(flagTargetType)
		authUser := flagAuthUser
		authPassword := flagAuthPassword
		skipDirectUpload := flagSkipDirectUpload

		if len(authUser) != 0 && len(authPassword) == 0 {
			return fmt.Errorf("--auth_username given with empty --auth_password")
		} else if len(authUser) == 0 && len(authPassword) != 0 {
			return fmt.Errorf("--auth_password given with empty --auth_username")
		}

		registryName := strings.TrimSuffix(flagRegistryName, "/")
		ctx := cmd.Context()

		// Get the path to the image's tarball.
		imagePath, err := imageutils.GetImagePath(target, targetType)
		if err != nil {
			return fmt.Errorf("could not find valid image path: %w", err)
		}
		image, err := imageutils.ReadImage(imagePath)
		if err != nil {
			return fmt.Errorf("could not read image: %w", err)
		}

		remoteAuth := remoteOpts(authUser, authPassword)

		// Set the default transfer via container registry.
		transfer := imagetransfer.RemoteTransferer(remoteAuth)

		if !skipDirectUpload {
			// Try to directly upload the image to the cluster's artifacts service (bypassing the cloud
			// container registry).

			ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
				Address: installerAddress,
			})
			if err != nil {
				return fmt.Errorf("could not establish connection: %w", err)
			}
			defer conn.Close()

			uploadOpts := []directupload.Option{
				directupload.WithDiscovery(directupload.NewFromConnection(conn)),
				directupload.WithOutput(cmd.OutOrStdout()),
				directupload.WithFailOver(imagetransfer.RemoteTransferer(remoteAuth)),
			}
			// Overwrite the default transferer.
			transfer = directupload.NewTransferer(ctx, uploadOpts...)
		}

		installerParams, err := imageutil.GetIconHardwareModuleInstallerParams(image)
		if err != nil {
			return errors.Wrap(err, "could not extract labels from image object")
		}
		imgOpts, err := imageutils.WithDefaultTag(installerParams.ImageName)
		if err != nil {
			return fmt.Errorf("could not create a tag for the image %q: %v", installerParams.ImageName, err)
		}
		reg := imageutils.RegistryOptions{
			URI:        registryName,
			Transferer: transfer,
			BasicAuth: imageutils.BasicAuth{
				User: authUser,
				Pwd:  authPassword,
			},
		}

		_, err = imageutils.PushImage(image, imgOpts, reg)
		if err != nil {
			return fmt.Errorf("could not push target %q to the container registry: %v", target, err)
		}

		// Read config file if available.
		hardwareModuleConfig := installerpb.IconHardwareModuleOptions_HardwareModuleConfig{
			Content: []byte{},
		}
		if flagHardwareModuleConfig != "" {
			if hardwareModuleConfig.Content, err = os.ReadFile(flagHardwareModuleConfig); err != nil {
				return fmt.Errorf("unable to read config file: %w", err)
			}
		}
		// Install the hardware module on the server.
		if err := installHardwareModule(installHardwareModuleParams{
			address:                 installerAddress,
			registryName:            registryName,
			authUser:                authUser,
			authPassword:            authPassword,
			image:                   image,
			moduleName:              flagHardwareModuleName,
			hardwareModuleConfig:    &hardwareModuleConfig,
			requiresAtemsys:         flagRequiresAtemsys,
			rtpcHostname:            flagRtpcHostname,
			runWithRealtimePriority: flagRunWithRealtimePriority,
			isolateNetwork:          flagIsolateNetwork}); err != nil {
			return fmt.Errorf("could not install the hardware module: %w", err)
		}

		return nil
	},
}

func init() {
	cmd.RootCmd.AddCommand(startCmd)

	startCmd.PersistentFlags().StringVar(&flagAuthUser, "auth_user", "", "(optional) The username used to access the private container registry.")
	startCmd.PersistentFlags().StringVar(&flagAuthPassword, "auth_password", "", "(optional) The password used to authenticate private container registry access.")
	startCmd.PersistentFlags().StringVar(&flagInstallerAddress, "installer_address", "xfa.lan:17080", "The address of the installer service.")
	startCmd.PersistentFlags().StringVar(&flagRegistryName, "registry_name", "", "The name of the registry where the hardware module image is to be pushed.")
	startCmd.PersistentFlags().StringVar(&flagTargetType, "target_type", "build", `The target type {"archive","build"}:
  "archive" expects a file path pointing to an already-built image.
  "build" expects a build target which this tool will use to create a docker container image.`)
	startCmd.PersistentFlags().BoolVar(&flagSkipDirectUpload, "skip_direct_upload", false, "If true, the module will first be uploaded to a container registry before it is downloaded and installed on the cluster.")
	startCmd.PersistentFlags().StringVar(&flagRtpcHostname, "rtpc_hostname", "", "The hostname of the rtpc node to install this module on.")
	startCmd.PersistentFlags().StringVar(&flagHardwareModuleName, "hardware_module_name", "", "The name of the hw module, which should match the machine.xml config.")
	startCmd.PersistentFlags().StringVar(&flagHardwareModuleConfig, "hardware_module_config", "", "Path to the config file (.pbtxt) associated with the hardware module.")
	startCmd.PersistentFlags().BoolVar(&flagRequiresAtemsys, "requires_atemsys", false, "If true, then the module requires an atemsys device to run.")
	startCmd.PersistentFlags().BoolVar(&flagRunWithRealtimePriority, "run_with_realtime_priority", true, "If true, then the module runs with realtime priority.")
	startCmd.PersistentFlags().BoolVar(&flagIsolateNetwork, "isolate_network", false, "If true, then the module runs with an isolated cluster network.")

	startCmd.MarkPersistentFlagRequired("install_address")
	startCmd.MarkPersistentFlagRequired("rtpc_hostname")
	startCmd.MarkPersistentFlagRequired("registry_name")
}
