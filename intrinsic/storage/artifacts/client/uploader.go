// Copyright 2023 Intrinsic Innovation LLC

// Package client contains client helpers for ArtifactsApiService
package client

import (
	"context"
	"fmt"
	"io"
	"os"
	"time"

	log "github.com/golang/glog"
	"github.com/google/go-containerregistry/pkg/name"
	crv1 "github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/tarball"
	"golang.org/x/sync/errgroup"
	artifactgrpcpb "intrinsic/storage/artifacts/proto/artifact_go_grpc_proto"
	artifactpb "intrinsic/storage/artifacts/proto/artifact_go_grpc_proto"
)

// UploaderOption is an option for the Uploader.
type UploaderOption func(options uploaderOptions) uploaderOptions

type uploaderOptions struct {
	maxNumberOfUploads int
	maxCheckWaitTime   time.Duration
	strategy           uploadStrategy
	alignForK8s        bool
}

var defaultOptions = uploaderOptions{
	maxNumberOfUploads: 4,
	maxCheckWaitTime:   5 * time.Minute,
	strategy:           nonStreamingUpload,
	alignForK8s:        true,
}

// WithUploadParallelism sets the maximum number of parallel uploads.
func WithUploadParallelism(value int) UploaderOption {
	return func(options uploaderOptions) uploaderOptions {
		options.maxNumberOfUploads = value
		return options
	}
}

// WithMaxCheckWaitTime sets the maximum time various availability checks
// will wait before failing
func WithMaxCheckWaitTime(value time.Duration) UploaderOption {
	return func(options uploaderOptions) uploaderOptions {
		options.maxCheckWaitTime = value
		return options
	}
}

// WithStreamingUpload option instructs uploader to use streaming type
// tasks. While more performant, this type of tasks may run into various
// reverse-proxy upload limits. Looking at you cloud-relay nginx ingress!
func WithStreamingUpload() UploaderOption {
	return func(options uploaderOptions) uploaderOptions {
		options.strategy = streamingUpload
		return options
	}
}

// WithSequentialUpload option instructs uploader to use non-streaming type
// of tasks. This is currently default as we have issues with nginx streaming
// configuration
func WithSequentialUpload() UploaderOption {
	return func(options uploaderOptions) uploaderOptions {
		options.strategy = nonStreamingUpload
		return options
	}
}

// WithAlignForK8sDeployments controls if uploader will align manifest names
// with K8s deployment needs. In order for K8s to correctly load images
// locally, we need to create several extra indexes for manifests.
// Default value is true.
func WithAlignForK8sDeployments(align bool) UploaderOption {
	return func(options uploaderOptions) uploaderOptions {
		options.alignForK8s = align
		return options
	}
}

// ContentReader allows access to the underlying reader. Every time this
// function is called, new fresh io.ReaderCloser is expected by caller.
type ContentReader tarball.Opener

// ContentFromPath creates ContentReader from local filesystem path
func ContentFromPath(path string) ContentReader {
	return func() (io.ReadCloser, error) {
		return os.Open(path)
	}
}

// Uploader is an interface for the Artifact Service client.
type Uploader interface {
	// UploadImageFromArchive reads image from local tar file and uploads it to server
	UploadImageFromArchive(ctx context.Context, imageName string, reader ContentReader) error

	// UploadImage reads provided image object and uploads required components.
	//
	// Returns error on any failure
	UploadImage(ctx context.Context, imageName string, image crv1.Image) error
}

// NewUploader creates a new Uploader.
func NewUploader(client artifactgrpcpb.ArtifactServiceApiClient, opts ...UploaderOption) (Uploader, error) {
	options := defaultOptions
	for _, opt := range opts {
		options = opt(options)
	}

	return &defaultHelper{uploaderOptions: options, client: client}, nil
}

type defaultHelper struct {
	uploaderOptions
	client artifactgrpcpb.ArtifactServiceApiClient
}

func (h *defaultHelper) UploadImageFromArchive(ctx context.Context, imageName string, reader ContentReader) error {
	// tar file will have only ONE manifest, so we are going to load it
	// while ignoring its originating tag.
	image, err := tarball.Image(tarball.Opener(reader), nil)
	if err != nil {
		return fmt.Errorf("invalid image tar: %w", err)
	}

	return h.UploadImage(ctx, imageName, image)
}

func (h *defaultHelper) UploadImage(ctx context.Context, imageName string, image crv1.Image) error {
	imageManifest, err := toImageManifest(image)
	if err != nil {
		return fmt.Errorf("error reading image: %w", err)
	}

	request := &artifactpb.ImageRequest{
		Name:     imageName,
		Manifest: imageManifest,
	}
	response, err := h.client.CheckImage(ctx, request)
	if err != nil {
		return fmt.Errorf("check image failed: %w", err)
	}

	return h.uploadImageParts(ctx, image, response)
}

func (h *defaultHelper) uploadImageParts(ctx context.Context, image crv1.Image, response *artifactpb.ArtifactResponse) error {
	taskGroup, _ := errgroup.WithContext(ctx)
	taskGroup.SetLimit(h.maxNumberOfUploads)

	log.InfoContextf(ctx, "uploading image %s to upstream...", response.Ref)
	missingRefs := asRefMap(response.MissingRefs...)
	maxUpdateSize := response.MaxUpdateSize
	// if check image returns image name as missing reference, we need
	// to upload everything.
	imgDigest, err := image.Digest()
	if err != nil {
		return fmt.Errorf("system error: %w", err)
	}

	if len(missingRefs) > 0 {

		fullUpload := len(missingRefs) == 1 && response.MissingRefs[0] == imgDigest.String()

		// we are missing some references, let's start by uploading layers
		layers, err := image.Layers()
		if err != nil {
			return fmt.Errorf("cannot read layers: %w", err)
		}

		for _, layer := range layers {
			digest, err := layer.Digest()
			if err != nil {
				return err
			}

			if _, missing := missingRefs[digest.String()]; missing || fullUpload {
				mediaType, _ := layer.MediaType()
				log.InfoContextf(ctx, "uploading layer %s (%s) ", digest, mediaType)
				delete(missingRefs, digest.String())
				task, err := newTask(ctx, h.strategy, h.client, maxUpdateSize, asDigestNamed(layer), layer.Compressed)
				if err != nil {
					return err
				}
				taskGroup.Go(runWithContext(ctx, task))
			}
		}

		// upload container config
		manifest, err := image.Manifest()
		if err != nil {
			return err
		}
		configRef := manifest.Config.Digest.String()
		if _, missing := missingRefs[configRef]; missing || fullUpload {
			log.InfoContextf(ctx, "uploading config for %s: ", response.Ref)
			delete(missingRefs, configRef)
			task, err := newTask(ctx, h.strategy, h.client, maxUpdateSize, asDigestNamed(descWrap{value: manifest.Config}), bytesReader(image.RawConfigFile))
			if err != nil {
				return err
			}
			taskGroup.Go(runWithContext(ctx, task))
		}
	}

	if err := taskGroup.Wait(); err != nil {
		return fmt.Errorf("error uploading image: %w", err)
	}

	// this needs to be last step to tie together all previously uploaded blobs under image name
	log.InfoContextf(ctx, "uploading manifest for %s", response.Ref)
	manifestNames := []namedObject{asSimplyNamed(response.Ref, image)}
	if h.alignForK8s {
		// In order to allow k8s to identify locally sourced image correctly
		// we need to store manifest under few alternative names...
		manifestNames = append(manifestNames,
			asDigestNamed(image),
			asSimplyNamed(getDigestReference(response.Ref, imgDigest.String()), image))
	}

	for _, named := range manifestNames {
		task, err := newTask(ctx, h.strategy, h.client, maxUpdateSize, named, bytesReader(image.RawManifest))
		if err != nil {
			return err
		}
		if err = task.runWithCtx(ctx); err != nil {
			reference, _ := named.Name()
			return fmt.Errorf("error uploading manifest (%s): %w", reference, err)
		}
	}

	return nil
}

func getDigestReference(imgName string, digest string) string {
	reference, err := name.ParseReference(imgName, name.WeakValidation)
	if err != nil {
		panic(fmt.Errorf("cannot parse reference, this is programmer error: %w", err))
	}

	return reference.Context().Digest(digest).Name()
}

func asRefMap(refs ...string) map[string]string {
	result := make(map[string]string, len(refs))

	for _, ref := range refs {
		result[ref] = ""
	}

	return result
}

func toImageManifest(image crv1.Image) (*artifactpb.ImageManifest, error) {

	manifest, err := image.Manifest()
	if err != nil {
		return nil, err
	}

	hash, err := image.Digest()
	if err != nil {
		return nil, err
	}

	size, err := image.Size()
	if err != nil {
		return nil, err
	}

	data, err := image.RawManifest()
	if err != nil {
		return nil, err
	}

	config, err := image.ConfigFile()
	if err != nil {
		return nil, err
	}

	ociDescriptor := &artifactpb.ImageManifest{
		MediaType:   string(manifest.MediaType),
		Digest:      hash.String(),
		Size:        size,
		Data:        data,
		Annotations: manifest.Annotations,
	}

	if platform := config.Platform(); platform != nil {
		platformStr := platform.String()
		ociDescriptor.Platform = &platformStr
	}

	return ociDescriptor, nil

}
