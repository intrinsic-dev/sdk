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
}

var defaultOptions = uploaderOptions{
	maxNumberOfUploads: 4,
	maxCheckWaitTime:   5 * time.Minute,
}

// UploadParallelism sets the maximum number of parallel uploads.
func UploadParallelism(value int) UploaderOption {
	return func(options uploaderOptions) uploaderOptions {
		options.maxNumberOfUploads = value
		return options
	}
}

// MaxCheckWaitTime sets the maximum time various availability checks
// will wait before failing
func MaxCheckWaitTime(value time.Duration) UploaderOption {
	return func(options uploaderOptions) uploaderOptions {
		options.maxCheckWaitTime = value
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
	if response.Available {
		log.Infof("image %s is already available upstream, skipping", response.Ref)
		return nil
	}

	taskGroup, _ := errgroup.WithContext(ctx)
	taskGroup.SetLimit(h.maxNumberOfUploads)

	log.Infof("uploading image %s to upstream...", response.Ref)
	missingRefs := asRefMap(response.MissingRefs...)
	maxUpdateSize := response.MaxUpdateSize
	if len(missingRefs) > 0 {

		// if check image returns image name as missing reference, we need
		// to upload everything.
		imgDigest, err := image.Digest()
		if err != nil {
			return fmt.Errorf("system error: %w", err)
		}
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
				log.Infof("uploading layer %s (%s) ", digest, mediaType)
				delete(missingRefs, digest.String())
				task, err := newTask(ctx, h.client, maxUpdateSize, asDigestNamed(layer), layer.Compressed)
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
			log.Infof("uploading config for %s: ", response.Ref)
			delete(missingRefs, configRef)
			task, err := newTask(ctx, h.client, maxUpdateSize, asDigestNamed(descWrap{value: manifest.Config}), bytesReader(image.RawConfigFile))
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
	log.Infof("uploading manifest for %s", response.Ref)
	task, err := newTask(ctx, h.client, maxUpdateSize, asSimplyNamed(response.Ref, image), bytesReader(image.RawManifest))
	if err != nil {
		return err
	}

	return task.runWithCtx(ctx)
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
