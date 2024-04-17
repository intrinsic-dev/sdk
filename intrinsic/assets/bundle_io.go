// Copyright 2023 Intrinsic Innovation LLC

// Package bundleio contains a function that reads a bundle archive file.
package bundleio

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"archive/tar"
	descriptorpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"google.golang.org/protobuf/proto"
	anypb "google.golang.org/protobuf/types/known/anypb"
	idpb "intrinsic/assets/proto/id_go_proto"
	smpb "intrinsic/assets/services/proto/service_manifest_go_proto"
	ipb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	"intrinsic/util/archive/tartooling"
)

const (
	serviceManifestPathInTar  = "service_manifest.binarypb"
)

type handler func(io.Reader) error
type fallbackHandler func(string, io.Reader) error

// walkTarFile walks through a tar file and invokes handlers on specific
// filenames.  fallback can be nil.  Returns an error if all handlers in
// handlers are not invoked.  It ignores all non-regular files.
func walkTarFile(t *tar.Reader, handlers map[string]handler, fallback fallbackHandler) error {
	for len(handlers) > 0 || fallback != nil {
		hdr, err := t.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("getting next file failed: %v", err)
		}
		if hdr.Typeflag != tar.TypeReg {
			continue
		}

		n := hdr.Name
		if h, ok := handlers[n]; ok {
			delete(handlers, n)
			if err := h(t); err != nil {
				return fmt.Errorf("error processing file %q: %v", n, err)
			}
		} else if fallback != nil {
			if err := fallback(n, t); err != nil {
				return fmt.Errorf("error processing file %q: %v", n, err)
			}
		}
	}
	if len(handlers) != 0 {
		keys := make([]string, 0, len(handlers))
		for k := range handlers {
			keys = append(keys, k)
		}
		return fmt.Errorf("missing expected files %s", keys)
	}
	return nil
}

// ignoreHandler is a function that can be used as a handler to ignore specific
// files.
func ignoreHandler(r io.Reader) error {
	return nil
}

// makeBinaryProtoHandler creates a handler that reads a binary proto file and
// unmarshals it into a file.  The proto must not be nil.
func makeBinaryProtoHandler(p proto.Message) handler {
	return func(r io.Reader) error {
		b, err := io.ReadAll(r)
		if err != nil {
			return fmt.Errorf("error reading: %v", err)
		}
		if err := proto.Unmarshal(b, p); err != nil {
			return fmt.Errorf("error parsing proto: %v", err)
		}
		return nil
	}
}

// makeCollectInlinedFallbackHandler constructs a default handler that collects
// all of the unknown files and reads their bytes into a map.  The key of the
// map is the filename, and the value is the file contents.
func makeCollectInlinedFallbackHandler() (map[string][]byte, fallbackHandler) {
	inlined := map[string][]byte{}
	fallback := func(n string, r io.Reader) error {
		b, err := io.ReadAll(r)
		if err != nil {
			return fmt.Errorf("error reading: %v", err)
		}
		inlined[n] = b
		return nil
	}
	return inlined, fallback
}

// makeOnlyServiceManifestHandlers returns a map of handlers that only pull out
// the service manifest from the tar file into the returned proto.  Can be used
// with a fallback handler.
func makeOnlyServiceManifestHandlers() (*smpb.ServiceManifest, map[string]handler) {
	manifest := new(smpb.ServiceManifest)
	handlers := map[string]handler{
		serviceManifestPathInTar: makeBinaryProtoHandler(manifest),
	}
	return manifest, handlers
}

// makeServiceAssetHandlers returns handlers for all assets listed in the
// service manifest.  This will be at most:
// * An handler that ignores the manifest
// * A binary proto handler for the default configuration file
// * A binary proto handler for the file descriptor set file
// * A handler that wraps opts.ImageProcessor to be called on every image
func makeServiceAssetHandlers(manifest *smpb.ServiceManifest, opts ProcessServiceOpts) (*smpb.ProcessedServiceAssets, map[string]handler) {
	handlers := map[string]handler{
		serviceManifestPathInTar: ignoreHandler, // already read this.
	}
	// Don't generate an empty assets message if there wasn't one to begin
	// with.  This is a slightly odd state, but Process is not doing validation
	// of the manifest.  This also protects against nil access of
	// manifest.GetAssets().{MemberVariable}, which is required for checking
	// the "optional" piece of "optional string" fields in this version of the
	// golang proto API.
	if manifest.GetAssets() == nil {
		return nil, handlers
	}

	processedAssets := new(smpb.ProcessedServiceAssets)
	if p := manifest.GetAssets().DefaultConfigurationFilename; p != nil {
		processedAssets.DefaultConfiguration = new(anypb.Any)
		handlers[*p] = makeBinaryProtoHandler(processedAssets.DefaultConfiguration)
	}
	if p := manifest.GetAssets().ParameterDescriptorFilename; p != nil {
		processedAssets.FileDescriptorSet = new(descriptorpb.FileDescriptorSet)
		handlers[*p] = makeBinaryProtoHandler(processedAssets.FileDescriptorSet)
	}
	for _, p := range manifest.GetAssets().GetImageFilenames() {
		if opts.ImageProcessor == nil {
			handlers[p] = ignoreHandler
		} else {
			handlers[p] = func(r io.Reader) error {
				img, err := opts.ImageProcessor(manifest.GetMetadata().GetId(), p, r)
				if err != nil {
					return fmt.Errorf("error processing image: %v", err)
				}
				if processedAssets.Images == nil {
					processedAssets.Images = make(map[string]*ipb.Image)
				}
				processedAssets.Images[p] = img
				return nil
			}
		}
	}
	return processedAssets, handlers
}

// ReadService reads the service bundle archive from path. It returns the
// service manifest and a mapping between bundle filenames and their contents.
func ReadService(path string) (*smpb.ServiceManifest, map[string][]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, nil, fmt.Errorf("could not open %q: %v", path, err)
	}
	defer f.Close()

	m, handlers := makeOnlyServiceManifestHandlers()
	inlined, fallback := makeCollectInlinedFallbackHandler()
	if err := walkTarFile(tar.NewReader(f), handlers, fallback); err != nil {
		return nil, nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}
	return m, inlined, nil
}

// ReadServiceManifest reads the bundle archive from path. It returns only
// service manifest.
func ReadServiceManifest(path string) (*smpb.ServiceManifest, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("could not open %q: %v", path, err)
	}
	defer f.Close()

	m, handlers := makeOnlyServiceManifestHandlers()
	if err := walkTarFile(tar.NewReader(f), handlers, nil); err != nil {
		return nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}
	return m, nil
}

// ImageProcessor is a closure that pushes an image and returns the resulting
// pointer to the container registry.  It is provided the id of the bundle being
// processed as well as the name of the specific image.  It is expected to
// upload the image and produce a usable image spec.  The reader points to an
// image archive.  This may be invoked multiple times.  Images are ignored if it
// is not specified.
type ImageProcessor func(idProto *idpb.Id, filename string, r io.Reader) (*ipb.Image, error)

// ProcessServiceOpts contains the necessary handlers to generate a processed
// service manifest.
type ProcessServiceOpts struct {
	ImageProcessor
}

// ProcessService creates a processed manifest from a bundle on disk using the
// provided processing functions.  It avoids doing any validation except for
// that required to transform the specified files in the bundle into their
// processed variants.
func ProcessService(path string, opts ProcessServiceOpts) (*smpb.ProcessedServiceManifest, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("could not open %q: %v", path, err)
	}
	defer f.Close()

	// Read the manifest and then reset the file once we have the information
	// about the bundle we're going to process.
	manifest, handlers := makeOnlyServiceManifestHandlers()
	if err := walkTarFile(tar.NewReader(f), handlers, nil); err != nil {
		return nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}
	if _, err := f.Seek(0, io.SeekStart); err != nil {
		return nil, fmt.Errorf("could not seek in %q: %v", path, err)
	}

	// Initialize handlers for when we walk through the file again now that we
	// know what we're looking for, but error on unexpected files this time.
	processedAssets, handlers := makeServiceAssetHandlers(manifest, opts)
	fallback := func(n string, r io.Reader) error {
		return fmt.Errorf("unexpected file %q", n)
	}
	if err := walkTarFile(tar.NewReader(f), handlers, fallback); err != nil {
		return nil, fmt.Errorf("error in tar file %q: %v", path, err)
	}

	return &smpb.ProcessedServiceManifest{
		Metadata:   manifest.GetMetadata(),
		ServiceDef: manifest.GetServiceDef(),
		Assets:     processedAssets,
	}, nil
}

// ValidateService checks that the assets of a service bundle are all
// contained within the inlined file map.
func ValidateService(manifest *smpb.ServiceManifest, inlinedFiles map[string][]byte) error {
	files := make([]string, 0, len(inlinedFiles))
	usedFiles := make(map[string]bool)
	for f := range inlinedFiles {
		files = append(files, f)
		usedFiles[f] = true
	}
	fileNames := strings.Join(files, ", ")
	// Check that every defined asset is in the inlined filemap.
	assets := map[string]string{
		"default configuration file": manifest.GetAssets().GetDefaultConfigurationFilename(),
		"parameter descriptor file":  manifest.GetAssets().GetParameterDescriptorFilename(),
		"image tar":                  manifest.GetServiceDef().GetRealSpec().GetImage().GetArchiveFilename(),
		"simulation image tar":       manifest.GetServiceDef().GetSimSpec().GetImage().GetArchiveFilename(),
	}
	for desc, path := range assets {
		if path != "" {
			if _, ok := inlinedFiles[path]; !ok {
				return fmt.Errorf("the resource manifest's %s %q is not in the bundle. files are %s", desc, path, fileNames)
			}
			delete(usedFiles, path)
		}
	}
	for _, path := range manifest.GetAssets().GetImageFilenames() {
		if _, ok := inlinedFiles[path]; !ok {
			return fmt.Errorf("the service manifest's image file %q is not in the bundle. files are %s", path, fileNames)
		}
		delete(usedFiles, path)
	}
	if len(usedFiles) > 0 {
		files := make([]string, 0, len(usedFiles))
		for f := range usedFiles {
			files = append(files, f)
		}
		fileNames := strings.Join(files, ", ")
		return fmt.Errorf("found unexpected files in the archive: %s", fileNames)
	}
	return nil
}

// WriteServiceOpts provides the details to construct a service bundle.
type WriteServiceOpts struct {
	Manifest    *smpb.ServiceManifest
	Descriptors *descriptorpb.FileDescriptorSet
	Config      *anypb.Any
	ImageTars   []string
}

// WriteService creates a tar archive at the specified path with the details
// given in opts.  Only the manifest is required and its assets field will be
// overwritten with what is placed in the archive based on ops.
func WriteService(path string, opts WriteServiceOpts) error {
	if opts.Manifest == nil {
		return fmt.Errorf("opts.Manifest must not be nil")
	}
	var tarBuf bytes.Buffer
	tw := tar.NewWriter(&tarBuf)

	opts.Manifest.Assets = new(smpb.ServiceAssets)
	if opts.Descriptors != nil {
		descriptorName := "descriptors-transitive-descriptor-set.proto.bin"
		opts.Manifest.Assets.ParameterDescriptorFilename = &descriptorName
		if err := tartooling.AddBinaryProto(opts.Descriptors, tw, descriptorName); err != nil {
			return fmt.Errorf("unable to write FileDescriptorSet to bundle: %v", err)
		}
	}
	if opts.Config != nil {
		configName := "default_config.binarypb"
		opts.Manifest.Assets.DefaultConfigurationFilename = &configName
		if err := tartooling.AddBinaryProto(opts.Config, tw, configName); err != nil {
			return fmt.Errorf("unable to write default config to bundle: %v", err)
		}
	}
	for _, path := range opts.ImageTars {
		base := filepath.Base(path)
		opts.Manifest.Assets.ImageFilenames = append(opts.Manifest.Assets.ImageFilenames, base)
		if err := tartooling.AddFile(path, tw, base); err != nil {
			return fmt.Errorf("unable to write %q to bundle: %v", path, err)
		}
	}
	// Now we can write the manifest, since assets have been completed.
	if err := tartooling.AddBinaryProto(opts.Manifest, tw, "service_manifest.binarypb"); err != nil {
		return fmt.Errorf("unable to write FileDescriptorSet to bundle: %v", err)
	}

	if err := tw.Close(); err != nil {
		return err
	}

	if err := os.WriteFile(path, tarBuf.Bytes(), 0644); err != nil {
		return fmt.Errorf("failed to write %q: %w", path, err)
	}
	return nil
}
