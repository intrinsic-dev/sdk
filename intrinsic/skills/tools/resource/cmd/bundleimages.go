// Copyright 2023 Intrinsic Innovation LLC

// Package bundleimages has utilities to push images from a resource bundle.
package bundleimages

import (
	"bytes"
	"fmt"
	"io"
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
		// Read the file into an internal buffer, since PushArchive will
		// attempt to read the buffer more than once and tar files don't have a
		// way to seek backwards (tape only ran one direction after all).  If
		// this becomes problematic due to massive image sizes, a temporary
		// file could be used here instead.
		b, err := io.ReadAll(r)
		if err != nil {
			return nil, fmt.Errorf("unable to read from tar: %v", err)
		}
		opener := func() (io.ReadCloser, error) {
			return io.NopCloser(bytes.NewBuffer(b)), nil
		}
		return imageutils.PushArchive(opener, opts, reg)
	}
}
