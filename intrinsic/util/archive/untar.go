// Copyright 2023 Intrinsic Innovation LLC

// Package untar provides helper functions for extracting tarballs.
package untar

import (
	"compress/gzip"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"archive/tar"
)

// isPathUnderDir checks if p is under directory dir. Both p and dir are clean
// absolute file paths.
func isPathUnderDir(p, dir string) bool {
	if p == dir {
		return true
	}
	return strings.HasPrefix(p, dir+"/")
}

func writeFile(name string, r io.Reader, perm os.FileMode) error {
	f, err := os.OpenFile(name, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, perm)
	if err != nil {
		return err
	}
	defer f.Close()

	if _, err := io.Copy(f, r); err != nil {
		return err
	}
	return f.Close()
}

// ExtractFile extracts a single file from the tarball from the given reader
// stream.  It skips files from the stream until the file with the provided
// filename is found.
func ExtractFile(r io.Reader, filename string) ([]byte, error) {
	tr := tar.NewReader(r)
	for {
		h, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}

		if h.Name != filename {
			continue
		}
		if h.Typeflag != tar.TypeReg {
			return nil, fmt.Errorf("%q is not a regular file in the tarball", filename)
		}
		return io.ReadAll(tr)
	}

	return nil, fmt.Errorf("%q not found in the tarball", filename)
}

// ExtractAll extracts all files and directories from the tarball stream into
// the given directory. It does not allow creating files that are outside the
// directory (such as ../trying-to-escape).
func ExtractAll(r io.Reader, dir string) error {
	dir, err := filepath.Abs(dir)
	if err != nil {
		return fmt.Errorf("untar destination dir: %s", dir)
	}

	tr := tar.NewReader(r)
	for {
		h, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		name := filepath.Clean(filepath.FromSlash(h.Name))
		target, err := filepath.Abs(filepath.Join(dir, name))
		if err != nil {
			return fmt.Errorf("invalid filename %q: %s", h.Name, err)
		}
		if !isPathUnderDir(target, dir) {
			return fmt.Errorf("%q tries to escape", h.Name)
		}

		switch h.Typeflag {
		case tar.TypeReg:
			if err := writeFile(target, tr, os.FileMode(h.Mode)&os.ModePerm); err != nil {
				return fmt.Errorf("create file %q: %s", h.Name, err)
			}

		case tar.TypeSymlink:
			if err := os.Symlink(h.Linkname, target); err != nil {
				return fmt.Errorf("create symlink %q to %q: %s", h.Name, h.Linkname, err)
			}

		case tar.TypeDir:
			if target == dir {
				continue // Skip the root directory.
			}
			if err := os.MkdirAll(target, os.FileMode(h.Mode)&os.ModePerm); err != nil {
				return fmt.Errorf("create dir %q: %s", h.Name, err)
			}
		default:
			return fmt.Errorf("unsupported type %d for file %q", h.Typeflag, h.Name)
		}
	}
	return nil
}

// ExtractAllGzip uncompresses the stream, extracts all files
// and directories from the tarball stream into the given directory.
func ExtractAllGzip(r io.Reader, dir string) error {
	uncompressedStream, err := gzip.NewReader(r)
	if err != nil {
		return fmt.Errorf("uncompress stream: %s", err)
	}

	err = ExtractAll(uncompressedStream, dir)
	if err != nil {
		return fmt.Errorf("extract stream: %s", err)
	}

	return nil
}
