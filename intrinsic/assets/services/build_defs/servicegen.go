// Copyright 2023 Intrinsic Innovation LLC

// Package servicegen implements creation of the service type bundle.
package servicegen

import (
	"fmt"
	"path/filepath"
	"slices"
	"strings"

	anypb "google.golang.org/protobuf/types/known/anypb"
	"intrinsic/assets/bundleio"
	"intrinsic/assets/idutils"
	smpb "intrinsic/assets/services/proto/service_manifest_go_proto"
	"intrinsic/util/proto/protoio"
	"intrinsic/util/proto/registryutil"
)

// ServiceData holds the data needed to create a service bundle.
type ServiceData struct {
	// Optional path to default config proto.
	DefaultConfig string
	// Comma separated paths to binary file descriptor set protos to be used to resolve the configuration and behavior tree messages.
	FileDescriptorSets string
	// Comma separated full paths to tar archives for images.
	ImageTars string
	// Path to a ServiceManifest pbtxt file.
	Manifest string
	// Bundle tar path.
	OutputBundle string
}

func validateManifest(m *smpb.ServiceManifest) error {
	if err := idutils.ValidateIDProto(m.GetMetadata().GetId()); err != nil {
		return fmt.Errorf("invalid name or package: %v", err)
	}
	if m.GetMetadata().GetVendor().GetDisplayName() == "" {
		return fmt.Errorf("vendor.display_name must be specified")
	}
	if m.GetServiceDef() != nil && m.GetServiceDef().GetSimSpec() == nil {
		return fmt.Errorf("a sim_spec must be specified if a service_def is provided;  see go/intrinsic-specifying-sim for more information")
	}
	return nil
}

func setDifference(slice1, slice2 []string) []string {
	var difference []string
	for _, val := range slice1 {
		if !slices.Contains(slice2, val) {
			difference = append(difference, val)
		}
	}
	return difference
}

// validateImageTars validates the provided images from the BUILD rule match the correct
// images specified in the manifest.
func validateImageTars(manifest *smpb.ServiceManifest, imgTarsList []string) error {
	imagesInManifest := []string{
		manifest.GetServiceDef().GetSimSpec().GetImage().GetArchiveFilename(),
		manifest.GetServiceDef().GetRealSpec().GetImage().GetArchiveFilename(),
	}
	basenameImageTarsList := []string{}
	for _, val := range imgTarsList {
		basenameImageTarsList = append(basenameImageTarsList, filepath.Base(val))
	}
	if diff := setDifference(basenameImageTarsList, imagesInManifest); len(diff) != 0 {
		return fmt.Errorf("images listed in the BUILD rule are not provided in the manifest: %v", diff)
	}
	if diff := setDifference(imagesInManifest, basenameImageTarsList); len(diff) != 0 {
		return fmt.Errorf("images listed in the manifest are not provided in the BUILD rule: %v", diff)
	}
	return nil
}

// CreateService bundles the data needed for software services.
func CreateService(d *ServiceData) error {
	m := new(smpb.ServiceManifest)
	if err := protoio.ReadTextProto(d.Manifest, m); err != nil {
		return fmt.Errorf("failed to read manifest: %v", err)
	}

	if err := validateManifest(m); err != nil {
		return fmt.Errorf("invalid manifest: %v", err)
	}

	var fds []string
	if d.FileDescriptorSets != "" {
		fds = strings.Split(d.FileDescriptorSets, ",")
	}
	set, err := registryutil.LoadFileDescriptorSets(fds)
	if err != nil {
		return fmt.Errorf("unable to build FileDescriptorSet: %v", err)
	}

	types, err := registryutil.NewTypesFromFileDescriptorSet(set)
	if err != nil {
		return fmt.Errorf("failed to populate the registry: %v", err)
	}

	var defaultConfig *anypb.Any
	if d.DefaultConfig != "" {
		defaultConfig = &anypb.Any{}
		if err := protoio.ReadTextProto(d.DefaultConfig, defaultConfig, protoio.WithResolver(types)); err != nil {
			return fmt.Errorf("failed to read default config proto: %v", err)
		}
	}

	var imageTarsList []string
	if d.ImageTars != "" {
		imageTarsList = strings.Split(d.ImageTars, ",")
	}

	if err := validateImageTars(m, imageTarsList); err != nil {
		return fmt.Errorf("unable to retrieve image tars: %v", err)
	}

	if err := bundleio.WriteService(d.OutputBundle, bundleio.WriteServiceOpts{
		Manifest:    m,
		Descriptors: set,
		Config:      defaultConfig,
		ImageTars:   imageTarsList,
	}); err != nil {
		return fmt.Errorf("unable to write service bundle: %v", err)
	}

	return nil
}
