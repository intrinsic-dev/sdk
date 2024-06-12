// Copyright 2023 Intrinsic Innovation LLC

// Package bundleimages has utilities to push images from a resource bundle.
package bundleimages

import (
	"fmt"
	"io"
	"path/filepath"
	"strings"

	"intrinsic/assets/bundleio"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imageutils"
	idpb "intrinsic/assets/proto/id_go_proto"
	ipb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	"intrinsic/skills/tools/resource/cmd/readeropener"
)

const (
	// maxInMemorySizeForPushArchive is set to a conservative 100MB for now.
	// Consider raising this value in the future if needed.
	maxInMemorySizeForPushArchive = 100 * 1024 * 1024
)

// CreateImageProcessor returns a closure to handle images within a bundle.  It
// pushes images to the registry using a default tag.  The image is named with
// the id of the resource with the basename image filename appended.
func CreateImageProcessor(reg imageutils.RegistryOptions) bundleio.ImageProcessor {
	return func(idProto *idpb.Id, filename string, r io.Reader) (*ipb.Image, error) {
		id, err := idutils.IDFromProto(idProto)
		if err != nil {
			return nil, fmt.Errorf("unable to get tag for image: %v", err)
		}

		fileNoExt := strings.TrimSuffix(filepath.Base(filename), filepath.Ext(filename))
		name := fmt.Sprintf("%s.%s", id, fileNoExt)
		opts, err := imageutils.WithDefaultTag(name)
		if err != nil {
			return nil, fmt.Errorf("unable to get tag for image: %v", err)
		}

		// Some images can be quite large (>1GB) and cause out-of-memory issues when
		// read into a byte buffer. We use the readeropener utility to use an
		// in-memory buffer when the size is small and to write the contents to disk
		// when large. Note that having some buffer is necessary as PushArchive will
		// attempt to read the buffer more than once and tar files don't have a way
		// to seek backwards (tape only ran one direction after all).
		opener, cleanup, err := readeropener.New(r, maxInMemorySizeForPushArchive)
		if err != nil {
			return nil, fmt.Errorf("could not process tar file %q: %v", filename, err)
		}
		defer cleanup()
		return imageutils.PushArchive(func() (io.ReadCloser, error) { return opener() }, opts, reg)
	}
}
