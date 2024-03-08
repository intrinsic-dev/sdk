// Copyright 2023 Intrinsic Innovation LLC

// Package testio provides helper functions for handling files in tests.
package testio

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/bazelbuild/rules_go/go/tools/bazel"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
)

// MustCreateParentDirectory creates the full file path to a specified file
// name.
func MustCreateParentDirectory(t *testing.T, path string) {
	t.Helper()
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		t.Fatalf("Unable to create %q: %v", dir, err)
	}
}

// MustCreateFile creates a file at the given path with the specified content.
func MustCreateFile(t *testing.T, content []byte, path string) {
	t.Helper()
	if err := os.WriteFile(path, content, 0644); err != nil {
		t.Fatalf("Write %q failed: %v", path, err)
	}
}

// MustCreateBinaryProto creates a serialized binary proto file at the given
// path.
func MustCreateBinaryProto(t *testing.T, p proto.Message, path string) {
	t.Helper()
	b, err := proto.Marshal(p)
	if err != nil {
		t.Fatalf("Failed to marshal proto: %v", err)
	}
	MustCreateFile(t, b, path)
}

// MustCreateTextProto creates a textproto file from a given proto message.
// The output is not stable, so should not be relied upon for matching exactly.
// This should only be used to create artifacts that are immediately parsed by
// tests.
func MustCreateTextProto(t *testing.T, p proto.Message, path string) {
	t.Helper()
	b, err := prototext.Marshal(p)
	if err != nil {
		t.Fatalf("Failed to marshal proto: %v", err)
	}
	MustCreateFile(t, b, path)
}

// MustCreateRunfilePath returns an expected path within the expected runfiles
// directory.
func MustCreateRunfilePath(t *testing.T, path string) string {
	t.Helper()
	root, err := bazel.RunfilesPath()
	if err != nil {
		t.Fatalf("bazel.RunfilesPath() failed: %v", err)
	}

	return filepath.Join(root, path)
}
