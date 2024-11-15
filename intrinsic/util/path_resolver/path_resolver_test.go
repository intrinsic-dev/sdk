// Copyright 2023 Intrinsic Innovation LLC

package path_resolver_test

import (
	"io/fs"
	"os"
	"strings"
	"testing"

	"intrinsic/util/path_resolver/pathresolver"
)

const (
	sourcePath = "intrinsic/util/path_resolver/path_resolver_test.go"
	sourceGlob = "intrinsic/*/path_resolver/path_resolver_test.g?"
)

func testThisFileContent(t *testing.T, content []byte) {
	t.Helper()

	if !strings.Contains(string(content), "Shane was here") {
		t.Errorf("Did not find expected content: %v", string(content))
	}
}

func TestResolveRunfilesPath(t *testing.T) {
	path, err := pathresolver.ResolveRunfilesPath(sourcePath)
	if err != nil {
		t.Fatalf("Unable to get location of %v: %v", sourcePath, err)
	}

	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("Unable to read %v: %v", path, err)
	}

	testThisFileContent(t, content)
}

func TestGlob(t *testing.T) {
	rootFs, err := pathresolver.ResolveRunfilesFs()
	if err != nil {
		t.Fatalf("Unable to get runfiles fs: %v", err)
	}
	paths, err := fs.Glob(rootFs, sourceGlob)
	if err != nil {
		t.Fatalf("Unable to glob %v: %v", sourceGlob, err)
	}

	if len(paths) != 1 {
		t.Fatalf("len(paths) = %d , want 1: %v", len(paths), paths)
	}

	content, err := fs.ReadFile(rootFs, paths[0])
	if err != nil {
		t.Fatalf("Unable to read %v: %v", paths[0], err)
	}

	testThisFileContent(t, content)
}
