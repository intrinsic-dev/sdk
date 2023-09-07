// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package imageutil contains docker image utility functions.
package imageutil

import (
	"fmt"
	"log"
	"os/exec"
	"regexp"
	"strings"

	"github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/google/go-containerregistry/pkg/v1/tarball"
	"github.com/pkg/errors"
)

var (
	buildCommand = "bazel"
	build        = BuildExec    // Stubbed out for testing.
	remoteWrite  = remote.Write // Stubbed out for testing.

	validSkillName   = regexp.MustCompile(`^[a-z]([a-z0-9_]*[a-z0-9])?$`)
	validBuildTarget = regexp.MustCompile(`//[^:]*:[^:]*.tar$`)
)

const (
	dockerLabelSkillNameKey                   = "ai.intrinsic.skill-name"
	dockerLabelSkillImageNameKey              = "ai.intrinsic.skill-image-name"
	dockerLabelIconHardwareModuleImageNameKey = "ai.intrinsic.hardware-module-image-name"
)

// SkillInstallerParams contains parameters used to install a docker image that contains a skill.
type SkillInstallerParams struct {
	SkillName string // the skill's name
	ImageName string // the image name of the skill
}

// IconHardwareModuleInstallerParams constains parameters used to install a
// docker image that contains an ICON hardware module.
type IconHardwareModuleInstallerParams struct {
	ImageName string // the image name of the ICON HW Module
}

// TargetType determines how the "target" target command-line argument will be used.
type TargetType string

const (
	// Auto mode tries to infer the target type from the target string.
	Auto TargetType = "auto"
	// Build mode builds the docker container image using the associated build target name
	Build TargetType = "build"
	// Image mode assumes the given target points to an already-built image
	Image TargetType = "image"
	// SkillName mode assumes the target is the skill name (only used for stop)
	SkillName TargetType = "name"
)

// BuildExec runs the build command and captures its output.
func BuildExec(buildCommand string, buildArgs ...string) ([]byte, error) {
	buildCmd := exec.Command(buildCommand, buildArgs...)
	out, err := buildCmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("could not build docker image: %w\n%s", err, out)
	}
	return out, nil
}

// buildImage builds the given target. The built image's file path is returned.
func buildImage(target string) (string, error) {
	log.Printf("Building image %q using build command %q", target, buildCommand)
	buildArgs := []string{"build", "-c", "opt"}
	buildArgs = append(buildArgs, target)
	out, err := build(buildCommand, buildArgs...)
	if err != nil {
		return "", fmt.Errorf("could not build docker image: %w\n%s", err, out)
	}

	// Matches the output path of the respective build tool.
	re := regexp.MustCompile(`(` + buildCommand + `-(out|bin)/.*\.tar)`)
	matches := re.FindAll(out, -1)
	if len(matches) != 1 {
		return "", fmt.Errorf("could not extract target path from build output. Number of matches[%d] parsed with regex[%s] from output:\n%s", len(matches), re.String(), out)
	}
	tarFile := matches[0]
	log.Printf("Finished building and the output filepath is %q", tarFile)
	return string(tarFile), nil
}

func inferTargetType(target string) TargetType {
	if validSkillName.MatchString(target) {
		return SkillName
	} else if validBuildTarget.MatchString(target) {
		return Build
	} else {
		return Image
	}
}

// GetImagePath returns the image path.
func GetImagePath(target string, targetType TargetType) (string, error) {
	if targetType == Auto {
		targetType = inferTargetType(target)
	}
	switch targetType {
	case Build:
		if !strings.HasSuffix(target, ".tar") {
			return "", fmt.Errorf("target should end with .tar")
		}
		return buildImage(target)
	case Image:
		return target, nil
	default:
		return "", fmt.Errorf("unimplemented target type: %v", targetType)
	}
}

// GetSkillNameFromTarget gets the skill name from the given target.
func GetSkillNameFromTarget(target string, targetType TargetType) (string, error) {
	if targetType == Auto {
		targetType = inferTargetType(target)
	}
	switch targetType {
	case Build, Image:
		imagePath, err := GetImagePath(target, TargetType(targetType))
		if err != nil {
			return "", fmt.Errorf("could not find valid image path: %w", err)
		}
		image, err := ReadImage(imagePath)
		if err != nil {
			return "", fmt.Errorf("could not read image: %w", err)
		}
		installerParams, err := GetSkillInstallerParams(image)
		if err != nil {
			return "", fmt.Errorf("could not extract installer parameters: %w", err)
		}
		return installerParams.SkillName, nil
	case SkillName:
		return target, nil
	default:
		return "", fmt.Errorf("unimplemented target type: %v", targetType)
	}
}

// ReadImage reads the image from the given path.
func ReadImage(imagePath string) (v1.Image, error) {
	log.Printf("Reading image tarball %q", imagePath)
	image, err := tarball.ImageFromPath(imagePath, nil)
	if err != nil {
		return nil, errors.Wrapf(err, "creating tarball image from %q", imagePath)
	}
	return image, nil
}

// GetSkillInstallerParams retrieves docker image labels that are needed by the installer.
func GetSkillInstallerParams(image v1.Image) (*SkillInstallerParams, error) {
	configFile, err := image.ConfigFile()
	if err != nil {
		return nil, errors.Wrapf(err, "could not extract installer labels from image file")
	}
	imageLabels := configFile.Config.Labels
	imageName, ok := imageLabels[dockerLabelSkillImageNameKey]
	if !ok {
		return nil, fmt.Errorf("docker container does not have label %q", dockerLabelSkillImageNameKey)
	}
	skillName, ok := imageLabels[dockerLabelSkillNameKey]
	if !ok {
		return nil, fmt.Errorf("docker container does not have label %q", dockerLabelSkillNameKey)
	}
	return &SkillInstallerParams{
		SkillName: skillName,
		ImageName: imageName,
	}, nil
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
		return nil, fmt.Errorf("docker container does not have label %q", dockerLabelIconHardwareModuleImageNameKey)
	}
	return &IconHardwareModuleInstallerParams{
		ImageName: imageName,
	}, nil
}
