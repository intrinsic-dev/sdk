// Copyright 2023 Intrinsic Innovation LLC

// Package imageutils contains docker image utility functions.
package imageutils

import (
	"context"
	"fmt"
	"log"
	"os/exec"
	"strings"

	"github.com/google/go-containerregistry/pkg/name"
	containerregistry "github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/tarball"
	"github.com/pkg/errors"
	"github.com/rs/xid"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	idpb "intrinsic/assets/proto/id_go_proto"
	"intrinsic/kubernetes/workcell_spec/imagetags"
	ipb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	installerservicegrpcpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
)

var (
	buildCommand    = "bazel"
	build           = buildExec // Stubbed out for testing.
	buildConfigArgs = []string{
		"-c", "opt",
	}
)

const (
	// Domain used for images managed by Intrinsic.
	registryDomain = "gcr.io"

	// Number of times to try uploading a container image if we get retriable errors.
	remoteWriteTries = 5

	maxImageTagLength = 128

	dockerLabelSkillIDKey = "ai.intrinsic.asset-id"

	// The following labels are DEPRECATED and should not be used other than for backwards
	// compatibility.
	deprecatedDockerLabelSkillIDProtoKey = "ai.intrinsic.skill-id"
	deprecatedDockerLabelPackageName     = "ai.intrinsic.package-name"
	deprecatedDockerLabelSkillName       = "ai.intrinsic.skill-name"
)

// SkillInstallerParams contains parameters used to install a docker image that
// contains a skill.
type SkillInstallerParams struct {
	SkillID   string // the skill's id
	ImageName string // the image name of the skill
}

// TargetType determines how the "target" target command-line argument will be
// used.
type TargetType string

const (
	// Build mode builds the docker container image using the associated build
	// target name
	Build TargetType = "build"
	// Archive mode assumes the given target points to an already-built image
	Archive TargetType = "archive"
	// Image mode assumes the given target is an image name
	Image TargetType = "image"
	// Name mode assumes the target is the skill name (only used for stop)
	Name TargetType = "name"
	ID TargetType = "id"
)

// buildExec runs the build command and captures its output.
func buildExec(buildCommand string, buildArgs ...string) ([]byte, error) {
	buildCmd := exec.Command(buildCommand, buildArgs...)
	out, err := buildCmd.Output() // Ignore stderr
	if err != nil {
		return nil, fmt.Errorf("could not build docker image: %v\n%s", err, out)
	}
	return out, nil
}

// ValidateImageProto verifies that the specified image proto is valid for the specified project.
func ValidateImageProto(image *ipb.Image, project string) error {
	if err := ValidateRegistry(image.GetRegistry(), project); err != nil {
		return err
	}
	return nil
}

// ValidateRegistry verifies that the specified registry is valid for the specified project.
func ValidateRegistry(registry string, project string) error {
	expectedRegistry := GetRegistry(project)
	if registry != expectedRegistry {
		return status.Errorf(codes.InvalidArgument, "unexpected registry specified (expected %q, got %q)", expectedRegistry, registry)
	}
	return nil
}

// GetRegistry returns the registry to use for images in the specified project.
func GetRegistry(project string) string {
	return fmt.Sprintf("%s/%s", registryDomain, project)
}

// GetAssetVersionImageTag returns the image tag to use for an asset version.
//
// imageType is a user-chosen string that can be used to distinguish different images within the
// same asset version.
func GetAssetVersionImageTag(imageType string, version string) (string, error) {
	tag := ""

	if tag == "" {
		imageTypeVersion := strings.ReplaceAll(fmt.Sprintf("%s.%s", imageType, version), "+", "_")
		imageTypeVersionLabel, err := idutils.ToLabelNonReversible(imageTypeVersion)
		if err != nil {
			return "", fmt.Errorf("could not convert image type + version %q to label: %v", imageTypeVersion, err)
		}
		tag = fmt.Sprintf("%s-%s", imageTypeVersionLabel, xid.New().String())
	}

	if len(tag) > maxImageTagLength {
		return "", fmt.Errorf("tag %q exceeds maximum length %d", tag, maxImageTagLength)
	}

	return tag, nil
}

// buildImage builds the given target. The built image's file path is returned.
func buildImage(target string) (string, error) {
	log.Printf("Building image %q using build command %q", target, buildCommand)
	buildArgs := []string{"build"}
	buildArgs = append(buildArgs, buildConfigArgs...)
	buildArgs = append(buildArgs, target)
	out, err := build(buildCommand, buildArgs...)
	if err != nil {
		return "", fmt.Errorf("could not build docker image: %v\n%s", err, out)
	}

	outputs, err := getOutputFiles(target)
	if err != nil {
		return "", fmt.Errorf("could not determine output files: %v", err)
	}
	// Assume rule has a single output file - the built image
	if len(outputs) != 1 {
		return "", fmt.Errorf("could not determine image from target [%s] output files\n%v", target, outputs)
	}
	tarFile := outputs[0]
	if !strings.HasSuffix(tarFile, ".tar") {
		return "", fmt.Errorf("output file did not have .tar extension\n%s", tarFile)
	}
	log.Printf("Finished building and the output filepath is %q", tarFile)
	return string(tarFile), nil
}

// WithDefaultTag creates ImageOptions with a specific name and a default tag.
func WithDefaultTag(name string) (ImageOptions, error) {
	// Use the rapid candidate name if provided or a placeholder tag otherwise.
	// For Rapid workflows, the deployed chart references the image by
	// candidate name. For dev workflows, we reference by digest.
	tag, err := imagetags.DefaultTag()
	if err != nil {
		return ImageOptions{}, errors.Wrap(err, "generating tag")
	}
	return ImageOptions{
		Name: name,
		Tag:  tag,
	}, nil
}

// ImageOptions is used to configure Push of a specific image.
type ImageOptions struct {
	// The name to be given to the image.
	Name string
	// The tag to be given to the image.
	Tag string
}

// BasicAuth provides the necessary fields to perform basic authentication with
// a resource registry.
type BasicAuth struct {
	// User is the username used to access the registry.
	User string
	// Pwd is the password used to authenticate registry access.
	Pwd string
}

// RegistryOptions is used to configure Push to a specific registry
type RegistryOptions struct {
	// URI of the container registry
	URI string
	// The transferer performs the work to send the container to the registry.
	imagetransfer.Transferer
	// The optional parameters required to perform basic authentication with
	// the registry.
	BasicAuth
}

// PushImage takes an image and pushes it to the specified registry with the
// given options.
func PushImage(img containerregistry.Image, opts ImageOptions, reg RegistryOptions) (*ipb.Image, error) {
	registry := strings.TrimSuffix(reg.URI, "/")
	if len(registry) == 0 {
		return nil, fmt.Errorf("registry is empty")
	}

	// A tag is required for retention.  Infra uses an img being untagged as
	// a signal it can be removed.
	dst := fmt.Sprintf("%s/%s:%s", registry, opts.Name, opts.Tag)
	ref, err := name.NewTag(dst)
	if err != nil {
		return nil, errors.Wrapf(err, "name.NewReference(%q)", dst)
	}

	digest, err := img.Digest()
	if err != nil {
		return nil, fmt.Errorf("could not get the sha256 of the image: %v", err)
	}

	if err := reg.Transferer.Write(ref, img); err != nil {
		return nil, fmt.Errorf("could not write image %q: %v", dst, err)
	}

	// Always provide a spec in terms of the digest, since that is
	// reproducible, while a tag may not be.
	return &ipb.Image{
		Registry:     registry,
		Name:         opts.Name,
		Tag:          "@" + digest.String(),
		AuthUser:     reg.User,
		AuthPassword: reg.Pwd,
	}, nil
}

// PushArchive takes an image archive provided by opener pushes it to the
// specified registry.
func PushArchive(opener tarball.Opener, opts ImageOptions, reg RegistryOptions) (*ipb.Image, error) {
	// tarball.Image optionally takes a name.Tag as the second parameter.
	// That's only needed if there are multiple images in the provided tarball,
	// since it then uses the reference to find it.  This is different than how
	// we use the reference constructed above, which is to specify where we'll
	// push the image we're reading.  We're basically giving ourselves license
	// to rename whatever the image is in the tarball during the push.
	img, err := tarball.Image(opener, nil)
	if err != nil {
		return nil, fmt.Errorf("could not create tarball image: %v", err)
	}
	return PushImage(img, opts, reg)
}

// GetImagePath returns the image path.
func GetImagePath(target string, targetType TargetType) (string, error) {
	switch targetType {
	case Build:
		if !strings.HasSuffix(target, ".tar") {
			return "", fmt.Errorf("target should end with .tar")
		}
		return buildImage(target)
	case Archive:
		return target, nil
	default:
		return "", fmt.Errorf("unimplemented target type: %v", targetType)
	}
}

// GetImage returns an Image from the given target and registry.
func GetImage(target string, targetType TargetType, t imagetransfer.Transferer) (containerregistry.Image, error) {
	switch targetType {
	case Build, Archive:
		imagePath, err := GetImagePath(target, targetType)
		if err != nil {
			return nil, fmt.Errorf("could not find valid image path: %v", err)
		}
		image, err := ReadImage(imagePath)
		if err != nil {
			return nil, fmt.Errorf("could not read image: %v", err)
		}
		return image, nil
	case Image:
		ref, err := name.ParseReference(target)
		if err != nil {
			return nil, fmt.Errorf("could not parse image reference %q: %v", target, err)
		}
		image, err := t.Read(ref)
		if err != nil {
			return nil, fmt.Errorf("could not access image %s: %v", ref.Name(), err)
		}
		return image, nil
	default:
		return nil, fmt.Errorf("unimplemented target type: %v", targetType)
	}
}

func getOutputFiles(target string) ([]string, error) {
	buildArgs := []string{"cquery"}
	buildArgs = append(buildArgs, buildConfigArgs...)
	buildArgs = append(buildArgs, "--output=files", target)
	out, err := build(buildCommand, buildArgs...)
	if err != nil {
		return nil, fmt.Errorf("could not get output files: %v\n%s", err, out)
	}
	return strings.Split(strings.TrimSpace(string(out)), "\n"), nil
}

func getOneOutputFile(target string) (string, error) {
	files, err := getOutputFiles(target)
	if err != nil {
		return "", err
	}
	if len(files) != 1 {
		return "", fmt.Errorf("expected 1 output file, got %d", len(files))
	}
	return files[0], nil
}

// GetArchiveFromBazelLabel takes a bazel label for an image target and gets the path to the created archive in the bazel output files.
func GetArchiveFromBazelLabel(target string) (string, error) {
	log.Printf("Locating archive from target: %s", target)
	// py_skill and cc_skill starlark macros enforce target name ending in _image.
	// They also create a target that builds an archive with the same label + ".tar".
	if strings.HasSuffix(target, "_image.tar") {
		return getOneOutputFile(target)
	}
	if strings.HasSuffix(target, "_image") {
		return getOneOutputFile(strings.Join([]string{target, "tar"}, "."))
	}
	return "", fmt.Errorf("given build target does not appear to be a skill image rule")
}

// SkillIDFromTarget gets the skill ID from the given target and registry.
func SkillIDFromTarget(target string, targetType TargetType, t imagetransfer.Transferer) (string, error) {
	switch targetType {
	case Build:
		archivePath, err := GetArchiveFromBazelLabel(target)
		if err != nil {
			return "", fmt.Errorf("could not extract a skill id from the given build target %s: %v", target, err)
		}
		return SkillIDFromTarget(archivePath, Archive, t)
	case Archive, Image:
		image, err := GetImage(target, targetType, t)
		if err != nil {
			return "", fmt.Errorf("could not read image: %v", err)
		}
		installerParams, err := GetSkillInstallerParams(image)
		if err != nil {
			return "", fmt.Errorf("could not extract installer parameters: %v", err)
		}
		return installerParams.SkillID, nil
	case ID, Name:
		return target, nil
	default:
		return "", fmt.Errorf("unimplemented target type: %v", targetType)
	}
}

// ReadImage reads the image from the given path.
func ReadImage(imagePath string) (containerregistry.Image, error) {
	log.Printf("Reading image tarball %q", imagePath)
	image, err := tarball.ImageFromPath(imagePath, nil)
	if err != nil {
		return nil, errors.Wrapf(err, "creating tarball image from %q", imagePath)
	}
	return image, nil
}

// GetSkillInstallerParams retrieves docker image labels that are needed by the
// installer.
func GetSkillInstallerParams(image containerregistry.Image) (*SkillInstallerParams, error) {
	configFile, err := image.ConfigFile()
	if err != nil {
		return nil, errors.Wrapf(err, "could not extract installer labels from image file")
	}
	imageLabels := configFile.Config.Labels
	skillID, ok := imageLabels[dockerLabelSkillIDKey]
	if !ok {
		// Backward-compatibility for deprecated image labels.
		idProto := &idpb.Id{}
		if skillIDBinary, ok := imageLabels[deprecatedDockerLabelSkillIDProtoKey]; !ok {
			skillName, skillNameOK := imageLabels[deprecatedDockerLabelSkillName]
			skillPackage, skillPackageOK := imageLabels[deprecatedDockerLabelPackageName]
			if !skillNameOK || !skillPackageOK {
				return nil, fmt.Errorf("cannot recover skill ID from image labels")
			} else if skillID, err = idutils.IDFrom(skillPackage, skillName); err != nil {
				return nil, fmt.Errorf("invalid skill ID: %v", err)
			}
		} else if err := proto.Unmarshal([]byte(skillIDBinary), idProto); err != nil {
			return nil, fmt.Errorf("cannot unmarshal Id proto from the label %q: %v", deprecatedDockerLabelSkillIDProtoKey, err)
		} else if skillID, err = idutils.IDFromProto(idProto); err != nil {
			return nil, fmt.Errorf("invalid Id proto: %v", err)
		}
	}
	skillIDLabel, err := idutils.ToLabel(skillID)
	if err != nil {
		return nil, fmt.Errorf("could not convert skill ID %q to label: %v", skillID, err)
	}
	imageName := fmt.Sprintf("skill-%s", skillIDLabel)
	return &SkillInstallerParams{
		SkillID:   skillID,
		ImageName: imageName,
	}, nil
}

// InstallContainerParams holds parameters for InstallContainer.
type InstallContainerParams struct {
	Address    string
	Connection *grpc.ClientConn
	Request    *installerpb.InstallContainerAddonRequest
}

// InstallContainer uses the installer service to install a new container.
func InstallContainer(ctx context.Context, params *InstallContainerParams) error {

	client := installerservicegrpcpb.NewInstallerServiceClient(params.Connection)
	_, err := client.InstallContainerAddon(ctx, params.Request)
	if status.Code(err) == codes.Unimplemented {
		return fmt.Errorf("installer service not implemented at server side (is it running and accessible at %s?): %v", params.Address, err)
	} else if err != nil {
		return fmt.Errorf("InstallContainerAddon failed: %v", err)
	}

	return nil
}

// InstallContainers uses the installer service to install multiple new containers.
func InstallContainers(ctx context.Context, requests []*installerpb.InstallContainerAddonRequest, address string, conn *grpc.ClientConn) error {
	client := installerservicegrpcpb.NewInstallerServiceClient(conn)

	req := &installerpb.InstallContainerAddonsRequest{
		Requests: requests,
	}

	_, err := client.InstallContainerAddons(ctx, req)
	if status.Code(err) == codes.Unimplemented {
		return fmt.Errorf("installer service not implemented at server side (is it running and accessible at %s?): %v", address, err)
	} else if err != nil {
		return fmt.Errorf("InstallContainerAddons failed: %v", err)
	}

	return nil
}

// RemoveContainerParams holds parameters for RemoveContainer.
type RemoveContainerParams struct {
	Address    string
	Connection *grpc.ClientConn
	Request    *installerpb.RemoveContainerAddonRequest
}

// RemoveContainer uses the installer service to remove a new container.
func RemoveContainer(ctx context.Context, params *RemoveContainerParams) error {

	client := installerservicegrpcpb.NewInstallerServiceClient(params.Connection)
	_, err := client.RemoveContainerAddon(ctx, params.Request)
	if status.Code(err) == codes.Unimplemented {
		return fmt.Errorf("installer service not implemented at server side (is it running and accessible at %s?): %v", params.Address, err)
	} else if err != nil {
		return fmt.Errorf("RemoveContainerAddon failed: %v", err)
	}

	return nil
}
