// Copyright 2023 Intrinsic Innovation LLC

// Package imageutil contains docker image utility functions.
package imageutil

import (
	"fmt"

	"github.com/google/go-containerregistry/pkg/v1"
	"github.com/pkg/errors"
	"intrinsic/assets/imageutils"
)

const (
	dockerLabelIconHardwareModuleImageNameKey = "ai.intrinsic.hardware-module-image-name"
)

// IconHardwareModuleInstallerParams constains parameters used to install a
// docker image that contains an ICON hardware module.
type IconHardwareModuleInstallerParams struct {
	ImageName string // the image name of the ICON HW Module
}

// GetImagePath returns the image path.
func GetImagePath(target string, targetType imageutils.TargetType) (string, error) {
	switch targetType {
	case imageutils.Image:
		return target, nil
	default:
		return imageutils.GetImagePath(target, targetType)
	}
}

// GetIconHardwareModuleInstallerParams retrieves docker image labels that are needed by the installer.
func GetIconHardwareModuleInstallerParams(image v1.Image) (*IconHardwareModuleInstallerParams, error) {
	configFile, err := image.ConfigFile()
	if err != nil {
		return nil, errors.Wrapf(err, "could not extract installer labels from image file")
	}
	imageLabels := configFile.Config.Labels
	imageName, ok := imageLabels[dockerLabelIconHardwareModuleImageNameKey]
	if !ok {
		return nil, fmt.Errorf("docker container does not have label? %q", dockerLabelIconHardwareModuleImageNameKey)
	}
	return &IconHardwareModuleInstallerParams{
		ImageName: imageName,
	}, nil
}
