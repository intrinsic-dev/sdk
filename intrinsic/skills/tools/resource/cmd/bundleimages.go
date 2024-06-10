// Copyright 2023 Intrinsic Innovation LLC

// Package bundleimages has utilities to push images from a resource bundle.
package bundleimages

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"intrinsic/assets/bundleio"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imageutils"
	idpb "intrinsic/assets/proto/id_go_proto"
	ipb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
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

		// We write the file out to a temp file to avoid having to read its entire
		// contents into memory. Some images can be >1GB and cause out-of-memory
		// issues when read into a byte buffer. Note that having some buffer is
		// necessary as PushArchive will attempt to read the buffer more than once
		// and tar files don't have a way to seek backwards (tape only ran one
		// direction after all). In the future we might consider using memory for
		// smaller images to minimize disk usage.
		f, err := os.CreateTemp(os.TempDir(), "image-processor-")
		if err != nil {
			return nil, fmt.Errorf("could not create temp file %q: %v", f.Name(), err)
		}
		defer os.Remove(f.Name())
		if _, err := io.Copy(f, r); err != nil {
			return nil, fmt.Errorf("could not write image to temp file %q: %v", f.Name(), err)
		}

		opener := func() (io.ReadCloser, error) {
			return os.Open(f.Name())
		}
		return imageutils.PushArchive(opener, opts, reg)
	}
}
