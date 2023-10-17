// Copyright 2023 Intrinsic Innovation LLC

// Package registry defines functions that push skill images to a container registry.
package registry

import (
	"bytes"
	"fmt"
	"io"
	"strings"

	"github.com/google/go-containerregistry/pkg/name"
	containerregistry "github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/tarball"
	imagepb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	"intrinsic/skills/tools/skill/cmd/imagetransfer"
	"intrinsic/skills/tools/skill/cmd/imageutil"
)

// PushOptions is used to configure Push
type PushOptions struct {
	// AuthUser is the optional username used to access the registry.
	AuthUser string
	// AuthPwd is the optional password used to authenticate registry access.
	AuthPwd string
	// Registry is the container registry (ignored with Type is image).
	Registry string
	// Type is the target type. See --type flag definition in start.go for info.
	Type string
	//
	Transferer imagetransfer.Transferer
}

func imageSpec(image containerregistry.Image, imageName string, opts PushOptions) (*imagepb.Image, error) {
	digest, err := image.Digest()
	if err != nil {
		return nil, fmt.Errorf("could not get the sha256 of the image: %v", err)
	}
	return &imagepb.Image{
		Registry:     strings.TrimSuffix(opts.Registry, "/"),
		Name:         imageName,
		Tag:          "@" + digest.String(),
		AuthUser:     opts.AuthUser,
		AuthPassword: opts.AuthPwd,
	}, nil
}

func pushBuildOrArchiveTypes(image containerregistry.Image, imageName string, opts PushOptions) (*imagepb.Image, error) {
	registry := strings.TrimSuffix(opts.Registry, "/")
	if len(registry) == 0 {
		return nil, fmt.Errorf("registry is empty")
	}

	if err := imageutil.PushImage(registry, image, imageName, opts.Transferer); err != nil {
		return nil, fmt.Errorf("could not push the image to registry %q: %v", registry, err)
	}
	imgpb, err := imageSpec(image, imageName, opts)
	if err != nil {
		return nil, fmt.Errorf("could not create image spec: %v", err)
	}
	return imgpb, nil
}

// imagePbFromRef returns an Image proto constructed from the target and
// other configuration data.
func imagePbFromRef(imageRef string, imageName string, opts PushOptions) (*imagepb.Image, error) {
	ref, err := name.ParseReference(imageRef)
	if err != nil {
		return nil, fmt.Errorf("could not parse image reference %q: %v", ref, err)
	}

	repo := ref.Context().RepositoryStr()
	fields := strings.Split(repo, "/")
	var registry, name string
	if len(fields) == 2 {
		// If the repo has a project (e.g., my-project/say_skill_image), then pull
		// that out and add it to the registry field. This is needed because the
		// installer service expects this format.
		registry = ref.Context().RegistryStr() + "/" + fields[0]
		name = fields[1]
	} else if len(fields) == 1 {
		registry = ref.Context().RegistryStr()
		name = fields[0]
	} else {
		return nil, fmt.Errorf("could not split out project from repository: %s", repo)
	}

	tag := ref.Identifier()
	if strings.HasPrefix(tag, "sha256:") {
		tag = "@" + tag
	} else {
		tag = ":" + tag
	}

	return &imagepb.Image{
		Registry:     registry,
		Name:         name,
		Tag:          tag,
		AuthUser:     opts.AuthUser,
		AuthPassword: opts.AuthPwd,
	}, nil
}

func push(target string, image containerregistry.Image, imageName string, opts PushOptions) (*imagepb.Image, error) {
	targetType := imageutil.TargetType(opts.Type)
	switch targetType {
	case imageutil.Build, imageutil.Archive:
		return pushBuildOrArchiveTypes(image, imageName, opts)
	case imageutil.Image:
		return imagePbFromRef(target, imageName, opts)
	}
	return nil, fmt.Errorf("unimplemented target type: %v", targetType)
}

// PushSkill is a helper function that takes a target string and pushes the
// skill image to the container registry.
//
// Returns the image and associated SkillInstallerParams.
func PushSkill(target string, opts PushOptions) (*imagepb.Image, *imageutil.SkillInstallerParams, error) {
	targetType := imageutil.TargetType(opts.Type)
	if targetType != imageutil.Build && targetType != imageutil.Archive && targetType != imageutil.Image {
		return nil, nil, fmt.Errorf("type must be in {%s,%s,%s}", imageutil.Build, imageutil.Archive, imageutil.Image)
	}

	image, err := imageutil.GetImage(target, targetType, opts.Transferer)
	if err != nil {
		return nil, nil, fmt.Errorf("could not read image: %v", err)
	}
	installerParams, err := imageutil.GetSkillInstallerParams(image)
	if err != nil {
		return nil, nil, fmt.Errorf("could not extract labels from image object: %v", err)
	}
	imgpb, err := push(target, image, installerParams.ImageName, opts)
	if err != nil {
		return nil, nil, err
	}
	return imgpb, installerParams, err
}

// PushSkillFromBytes is a helper function that takes an image archive file
// as a byte array and pushes the skill image to the container registry.
//
// Returns the image.
func PushSkillFromBytes(archive []byte, opts PushOptions) (*imagepb.Image, error) {
	targetType := imageutil.TargetType(opts.Type)
	if targetType != imageutil.Archive {
		return nil, fmt.Errorf("type must be in {%s}", imageutil.Archive)
	}

	thunk := func() (io.ReadCloser, error) {
		return io.NopCloser(bytes.NewBuffer(archive)), nil
	}
	image, err := tarball.Image(thunk, nil)
	if err != nil {
		return nil, fmt.Errorf("could not create tarball image from byte array: %v", err)
	}
	installerParams, err := imageutil.GetSkillInstallerParams(image)
	if err != nil {
		return nil, fmt.Errorf("could not extract labels from image object: %v", err)
	}
	imgpb, err := pushBuildOrArchiveTypes(image, installerParams.ImageName, opts)
	if err != nil {
		return nil, err
	}
	return imgpb, err
}

// PushResource is a helper function that takes a target string and pushes the
// resource image to the container registry.
//
// Returns the image.
func PushResource(target string, imageName string, opts PushOptions) (*imagepb.Image, error) {
	targetType := imageutil.TargetType(opts.Type)
	if targetType != imageutil.Archive && targetType != imageutil.Image {
		return nil, fmt.Errorf("type must be in {%s,%s}", imageutil.Archive, imageutil.Image)
	}

	image, err := imageutil.GetImage(target, targetType, opts.Transferer)
	if err != nil {
		return nil, fmt.Errorf("could not read image: %v", err)
	}
	imgpb, err := push(target, image, imageName, opts)
	if err != nil {
		return nil, err
	}
	return imgpb, err
}

// PushResourceFromBytes is a helper function that takes an image archive file
// as a byte array and pushes the resource image to the container registry.
//
// Returns the image.
func PushResourceFromBytes(archive []byte, imageName string, opts PushOptions) (*imagepb.Image, error) {
	targetType := imageutil.TargetType(opts.Type)
	if targetType != imageutil.Archive {
		return nil, fmt.Errorf("type must be in {%s}", imageutil.Archive)
	}

	thunk := func() (io.ReadCloser, error) {
		return io.NopCloser(bytes.NewBuffer(archive)), nil
	}
	image, err := tarball.Image(thunk, nil)
	if err != nil {
		return nil, fmt.Errorf("could not create tarball image from byte array: %v", err)
	}
	imgpb, err := pushBuildOrArchiveTypes(image, imageName, opts)
	if err != nil {
		return nil, err
	}
	return imgpb, err
}
