// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

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

	backoff "github.com/cenkalti/backoff/v4"
	"github.com/google/go-containerregistry/pkg/name"
	"github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/google/go-containerregistry/pkg/v1/remote/transport"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"intrinsic/icon/hal/tools/hwmodule/cmd/cmd"
	"intrinsic/icon/hal/tools/hwmodule/cmd/imageutil"
	"intrinsic/kubernetes/workcell_spec/imagetags"
)

var (
	flagAuthUser         string
	flagAuthPassword     string
	flagInstallerAddress string
	flagRegistryName     string
	flagTargetType       string

	flagRtpcHostname            string
	flagHardwareModuleName      string
	flagHardwareModuleConfig    string
	flagRequiresAtemsys         bool
	flagRunWithRealtimePriority bool
	flagIsolateNetwork          bool
)

var (
	remoteWrite = remote.Write // Stubbed out for testing.
)

const (
	// Number of times to try uploading a container image if we get retriable errors.
	remoteWriteTries = 5
)

// pushImage pushes the tarball container image with the given name and path to the given container registry.
func pushImage(registry string, image v1.Image, authOption remote.Option) error {
	// Use the rapid candidate name if provided or a placeholder tag otherwise.
	// For Rapid workflows, the deployed chart references the image by candidate name.
	// For dev workflows, we reference by digest.
	tag, err := imagetags.DefaultTag()
	if err != nil {
		return errors.Wrap(err, "generating tag")
	}

	installerParams, err := imageutil.GetIconHardwareModuleInstallerParams(image)
	if err != nil {
		return errors.Wrap(err, "could not extract labels from image object")
	}

	dst := fmt.Sprintf("%s/%s:%s", registry, installerParams.ImageName, tag)
	dstTag, err := name.NewTag(dst, name.WeakValidation)
	if err != nil {
		return errors.Wrapf(err, "name.NewTag(%q)", dst)
	}
	log.Printf("Writing image to %q", dstTag)
	b := backoff.WithMaxRetries(backoff.NewExponentialBackOff(), remoteWriteTries)
	if err := backoff.Retry(func() error {
		err := remoteWrite(dstTag, image, authOption)
		if err, ok := err.(*transport.Error); ok && err.StatusCode >= 500 {
			// Retry server errors like 504 Gateway Timeout.
			return err
		}
		if err != nil {
			return backoff.Permanent(err)
		}
		return nil
	}, b); err != nil {
		return errors.Wrapf(err, "remote.Write to %q", dstTag)
	}
	log.Printf("Finished pushing image")
	return nil
}

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

var startCmd = &cobra.Command{
	Use:   "start [target]",
	Short: "Install an ICON hardware module",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		target := args[0]

		installerAddress := flagInstallerAddress
		targetType := flagTargetType
		authUser := flagAuthUser
		authPassword := flagAuthPassword

		if len(authUser) != 0 && len(authPassword) == 0 {
			return fmt.Errorf("--auth_username given with empty --auth_password")
		} else if len(authUser) == 0 && len(authPassword) != 0 {
			return fmt.Errorf("--auth_password given with empty --auth_username")
		}

		registryName := strings.TrimSuffix(flagRegistryName, "/")

		imagePath, err := imageutil.GetImagePath(target, imageutil.TargetType(targetType))
		if err != nil {
			return fmt.Errorf("could not find valid image path: %w", err)
		}
		image, err := imageutil.ReadImage(imagePath)
		if err != nil {
			return fmt.Errorf("could not read image: %w", err)
		}

		// Push the newly built image to the registry
		auth := remote.WithAuthFromKeychain(google.Keychain)
		if err := pushImage(registryName, image, auth); err != nil {
			return fmt.Errorf("could not push the image to registry %s: %w", registryName, err)
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
	startCmd.PersistentFlags().StringVar(&flagTargetType, "target_type", "build", `The target type {"build","image"}:
  "build" expects a build target which this tool will use to create a docker container image.
  "image" expects a file path pointing to an already-built image.`)
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
