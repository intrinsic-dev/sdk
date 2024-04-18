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
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	imagepb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
)

// PushOptions is used to configure Push
type PushOptions struct {
	// AuthUser is the optional username used to access the registry.
	AuthUser string
	// AuthPwd is the optional password used to authenticate registry access.
	AuthPwd string
	// Registry is the container registry to which to push the image.
	Registry string
	// Tag is the optional image tag to use.
	//
	// If empty, then imageutils.WithDefaultTag is used to determine the tag.
	Tag string
	// Type is the target type. See --type flag definition in start.go for info.
	Type string
	//
	Transferer imagetransfer.Transferer
}

func pushImage(image containerregistry.Image, imageName string, opts PushOptions) (*imagepb.Image, error) {
	reg := imageutils.RegistryOptions{
		URI:        opts.Registry,
		Transferer: opts.Transferer,
		BasicAuth: imageutils.BasicAuth{
			User: opts.AuthUser,
			Pwd:  opts.AuthPwd,
		},
	}

	var imgOpts imageutils.ImageOptions
	if opts.Tag == "" {
		var err error
		imgOpts, err = imageutils.WithDefaultTag(imageName)
		if err != nil {
			return nil, fmt.Errorf("could not create a tag for the image %q: %v", imageName, err)
		}
	} else {
		imgOpts = imageutils.ImageOptions{
			Name: imageName,
			Tag:  opts.Tag,
		}
	}

	return imageutils.PushImage(image, imgOpts, reg)
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
	targetType := imageutils.TargetType(opts.Type)
	switch targetType {
	case imageutils.Build, imageutils.Archive:
		return pushImage(image, imageName, opts)
	case imageutils.Image:
		imageProto, err := imagePbFromRef(target, imageName, opts)
		if err != nil {
			return nil, err
		}

		sourceRegistry := imageProto.GetRegistry()
		targetRegistry := opts.Registry
		if strings.HasSuffix(targetRegistry, "/") {
			targetRegistry = targetRegistry[:len(targetRegistry)-1]
		}
		if sourceRegistry == targetRegistry || targetRegistry == "" {
			// Target image is already in the specified registry, so nothing to do.
			return imageProto, nil
		}

		if opts.Tag == "" {
			// We could probably recover the original tag, given the digest, but won't implement unless we
			// need to.
			if strings.HasPrefix(imageProto.GetTag(), "@") {
				return nil, fmt.Errorf("tag is required when pushing an image with digest tag to a different registry")
			}
			if !strings.HasSuffix(imageProto.GetTag(), ":") {
				return nil, fmt.Errorf("unexpected image proto tag: %s", imageProto.GetTag())
			}
			opts.Tag = imageProto.GetTag()[1:]
		}

		// Target is in a different registry, so we need to push the image to the specified registry.
		return pushImage(image, imageName, opts)
	}
	return nil, fmt.Errorf("unimplemented target type: %v", targetType)
}

// PushSkill is a helper function that takes a target string and pushes the
// skill image to the container registry.
//
// Returns the image and associated SkillInstallerParams.
func PushSkill(target string, opts PushOptions) (*imagepb.Image, *imageutils.SkillInstallerParams, error) {
	targetType := imageutils.TargetType(opts.Type)
	if targetType != imageutils.Build && targetType != imageutils.Archive && targetType != imageutils.Image {
		return nil, nil, fmt.Errorf("type must be in {%s,%s,%s}", imageutils.Build, imageutils.Archive, imageutils.Image)
	}

	image, err := imageutils.GetImage(target, targetType, opts.Transferer)
	if err != nil {
		return nil, nil, fmt.Errorf("could not read image: %v", err)
	}
	installerParams, err := imageutils.GetSkillInstallerParams(image)
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
	targetType := imageutils.TargetType(opts.Type)
	if targetType != imageutils.Archive {
		return nil, fmt.Errorf("type must be in {%s}", imageutils.Archive)
	}

	thunk := func() (io.ReadCloser, error) {
		return io.NopCloser(bytes.NewBuffer(archive)), nil
	}
	image, err := tarball.Image(thunk, nil)
	if err != nil {
		return nil, fmt.Errorf("could not create tarball image from byte array: %v", err)
	}
	installerParams, err := imageutils.GetSkillInstallerParams(image)
	if err != nil {
		return nil, fmt.Errorf("could not extract labels from image object: %v", err)
	}
	imgpb, err := pushImage(image, installerParams.ImageName, opts)
	if err != nil {
		return nil, err
	}
	return imgpb, err
}
