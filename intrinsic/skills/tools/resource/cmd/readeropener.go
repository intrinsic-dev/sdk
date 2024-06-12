// Copyright 2023 Intrinsic Innovation LLC

// Package readeropener contains a function that takes an io.Reader and returns
// an Opener function that can be called multiple times.
package readeropener

import (
	"bytes"
	"fmt"
	"io"
	"os"
)

// Opener is a function that returns an io.ReadCloser. It can be called
// multiple times.
type Opener func() (io.ReadCloser, error)

// Cleanup is a function that does cleanup work.
type Cleanup func()

// New takes an io.Reader and returns an Opener function that can be called
// multiple times. This is done by reading its contents into a byte slice. If
// the size of the byte slice becomes too large (>maxInMemorySize), then this
// function writes it out to disk in a temp file. Cleanup should be called once
// the returned Opener and any of its readers are done.
func New(r io.Reader, maxInMemorySize int64) (Opener, Cleanup, error) {
	bb := bytes.NewBuffer(nil)
	_, err := io.CopyN(bb, r, maxInMemorySize)
	if err == io.EOF {
		// If we receive an EOF error then the reader's size is deemed small enough
		// to fit in a byte buffer.
		opener := func() (io.ReadCloser, error) {
			// We create a new byte buffer each time to allow multiple reads.
			return io.NopCloser(bytes.NewBuffer(bb.Bytes())), nil
		}
		cleanup := func() {}
		return opener, cleanup, nil
	} else if err != nil {
		return nil, nil, err
	}

	// For larger data we write it out to disk to avoid out-of-memory errors.
	f, err := os.CreateTemp(os.TempDir(), "read-opener-")
	if err != nil {
		return nil, nil, fmt.Errorf("could not create temp file %q: %v", f.Name(), err)
	}
	io.Copy(f, bb)
	io.Copy(f, r)

	opener := func() (io.ReadCloser, error) {
		return os.Open(f.Name())
	}
	cleanup := func() {
		os.Remove(f.Name())
	}
	return opener, cleanup, nil
}
