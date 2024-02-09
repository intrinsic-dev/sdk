// Copyright 2023 Intrinsic Innovation LLC

package tartooling

import (
	"io"
	"os"
	"path/filepath"
	"testing"

	"archive/tar"
	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/testing/protocmp"
	dpb "intrinsic/util/proto/testing/diamond_a_go_proto"
)

type AddFileTest struct {
	// Content of file or files to add
	Content [][]byte
	// Filenames of the files to add (files are created by prepare)
	Filenames []string
	// names/paths to use in tar instead of files' real names
	OverwriteNames []string

	// temporary files set by prepare
	Files []string
}

func mustPrepareTest(t *testing.T, test *AddFileTest) string {
	tmpDir, err := os.MkdirTemp("", "")
	if err != nil {
		t.Fatal(err)
	}
	for i, fn := range test.Filenames {
		fp := filepath.Join(tmpDir, fn)
		if err := os.WriteFile(fp, test.Content[i], 0644); err != nil {
			t.Fatal(err)
		}
		test.Files = append(test.Files, fp)
	}
	return tmpDir
}

func prepareForFiles(test *AddFileTest) func(t *testing.T, w *tar.Writer) {
	return func(t *testing.T, w *tar.Writer) {
		for i, f := range test.Files {
			if err := AddFile(f, w, test.OverwriteNames[i]); err != nil {
				t.Fatal(err)
			}
		}
	}
}

func mustPrepareTar(t *testing.T, prepare func(t *testing.T, w *tar.Writer)) *os.File {
	b, err := os.CreateTemp("", "")
	if err != nil {
		t.Fatal(err)
	}
	w := tar.NewWriter(b)
	prepare(t, w)

	if err := w.Close(); err != nil {
		t.Fatal(err)
	}
	b.Seek(0, 0)
	return b
}

func mustPrepareTarFromDir(t *testing.T, dir string) *os.File {
	b, err := os.CreateTemp("", "")
	if err != nil {
		t.Fatal(err)
	}
	w := tar.NewWriter(b)
	if err := AddDir(dir, w); err != nil {
		t.Fatal(err)
	}

	if err := w.Close(); err != nil {
		t.Fatal(err)
	}
	b.Seek(0, 0)
	return b
}

func mustHaveNoMoreEntries(t *testing.T, r *tar.Reader) {
	// no other content
	_, err := r.Next()
	if err != io.EOF {
		t.Fatalf("tar next, got error %v, want it exhausted with %v", err, io.EOF)
	}
}

// check size header
func TestFilesSize(t *testing.T) {
	test := &AddFileTest{
		Content:        [][]byte{[]byte("content")},
		Filenames:      []string{"secret.txt"},
		OverwriteNames: []string{""},
	}
	mustPrepareTest(t, test)
	b := mustPrepareTar(t, prepareForFiles(test))
	defer b.Close()
	r := tar.NewReader(b)
	// check size header
	for _, content := range test.Content {
		h, err := r.Next()
		if err != nil {
			t.Fatal(err)
		}
		if int(h.Size) < len(content) {
			t.Fatalf("tar content, size header: got %d, want at least %d", int(h.Size), len(content))
		}
	}
	mustHaveNoMoreEntries(t, r)
}

// check filenames of files in tar
func TestFilesFilenames(t *testing.T) {
	test := &AddFileTest{
		Content:        [][]byte{[]byte("content-a"), []byte("content-b"), []byte("content-c")},
		Filenames:      []string{"secret-a.txt", "secret-b.txt", "secret-c.txt"},
		OverwriteNames: []string{"newname-a.txt", "", "path/newname-c.txt"},
	}
	mustPrepareTest(t, test)
	b := mustPrepareTar(t, prepareForFiles(test))
	defer b.Close()
	// check filenames
	r := tar.NewReader(b)
	for i, wantFilename := range test.Filenames {
		if test.OverwriteNames[i] != "" {
			wantFilename = test.OverwriteNames[i]
		}
		h, err := r.Next()
		if err != nil {
			t.Fatal(err)
		}
		if h.Name != wantFilename {
			t.Fatalf("tar content [%d], name: got %q, want %q", i, h.Name, wantFilename)
		}
	}
	mustHaveNoMoreEntries(t, r)
}

func TestFilesSizeUsingDir(t *testing.T) {
	test := &AddFileTest{
		Content:        [][]byte{[]byte("content")},
		Filenames:      []string{"secret.txt"},
		OverwriteNames: []string{""},
	}
	dir := mustPrepareTest(t, test)
	b := mustPrepareTarFromDir(t, dir)
	defer b.Close()
	r := tar.NewReader(b)
	// check size header
	for _, content := range test.Content {
		h, err := r.Next()
		if err != nil {
			t.Fatal(err)
		}
		if int(h.Size) < len(content) {
			t.Fatalf("tar content, size header: got %d, want at least %d", int(h.Size), len(content))
		}
	}
	mustHaveNoMoreEntries(t, r)
}

func TestFilesContent(t *testing.T) {
	test := &AddFileTest{
		Content:        [][]byte{[]byte("content-a"), []byte("content-b")},
		Filenames:      []string{"secret-a.txt", "secret-b.txt"},
		OverwriteNames: []string{"", ""},
	}
	mustPrepareTest(t, test)
	b := mustPrepareTar(t, prepareForFiles(test))
	defer b.Close()
	// check content
	r := tar.NewReader(b)
	for i, wantContent := range test.Content {
		_, err := r.Next()
		if err != nil {
			t.Fatal(err)
		}
		gotContent, err := io.ReadAll(r)
		if err != nil {
			t.Fatal(err)
		}
		if string(gotContent) != string(wantContent) {
			t.Fatalf("tar content [%d], got %v, want %v,", i, gotContent, wantContent)
		}
	}
	mustHaveNoMoreEntries(t, r)
}

func TestSeekTo(t *testing.T) {
	test := &AddFileTest{
		Content:        [][]byte{[]byte("content-a"), []byte("content-b")},
		Filenames:      []string{"secret-a.txt", "secret-b.txt"},
		OverwriteNames: []string{"", ""},
	}
	mustPrepareTest(t, test)
	b := mustPrepareTar(t, prepareForFiles(test))
	defer b.Close()
	// check content
	r := tar.NewReader(b)
	if err := SeekTo(r, "secret-b.txt"); err != nil {
		t.Fatalf("SeekTo returned unexpected error: %v", err)
	}
	got, err := io.ReadAll(r)
	if err != nil {
		t.Fatalf("ReadAll returned unexpected error: %v", err)
	}
	want := "content-b"
	if string(got) != want {
		t.Fatalf("ReadAll returned unexpected contents, got %q, want %q", got, want)
	}
	mustHaveNoMoreEntries(t, r)
}

func TestFilesUsingDir(t *testing.T) {
	test := &AddFileTest{
		Content:        [][]byte{[]byte("content-a"), []byte("content-b")},
		Filenames:      []string{"secret-a.txt", "secret-b.txt"},
		OverwriteNames: []string{"", ""},
	}
	dir := mustPrepareTest(t, test)
	b := mustPrepareTarFromDir(t, dir)
	defer b.Close()
	// check content
	r := tar.NewReader(b)
	for i, wantContent := range test.Content {
		_, err := r.Next()
		if err != nil {
			t.Fatal(err)
		}
		gotContent, err := io.ReadAll(r)
		if err != nil {
			t.Fatal(err)
		}
		if string(gotContent) != string(wantContent) {
			t.Fatalf("tar content [%d], got %v, want %v,", i, gotContent, wantContent)
		}
	}
	mustHaveNoMoreEntries(t, r)
}

func TestAddBinaryProto(t *testing.T) {
	tests := []struct {
		desc string
		path string
		msg  proto.Message
	}{
		{
			desc: "nil message",
			path: "doesn't matter that this is invalid",
		},
		{
			desc: "some message",
			path: "some_data.binarypb",
			msg: &dpb.A{
				Value: "Baby Shark, doo-doo, doo-doo",
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			got := proto.Clone(tc.msg)
			if got != nil {
				proto.Reset(got)
			}

			b := mustPrepareTar(t, func(t *testing.T, w *tar.Writer) {
				if err := AddBinaryProto(tc.msg, w, tc.path); err != nil {
					t.Fatal(err)
				}
			})
			defer b.Close()
			r := tar.NewReader(b)
			if _, err := r.Next(); err != nil {
				if tc.msg == nil && err == io.EOF {
					// This is expected, but none of the remaining validation
					// is valid.
					return
				}
				t.Fatal(err)
			}
			gotContent, err := io.ReadAll(r)
			if err != nil {
				t.Fatal(err)
			}
			proto.Unmarshal(gotContent, got)
			if err := proto.Unmarshal(gotContent, got); err != nil {
				t.Fatalf("proto.Unmarshal() returned unexpected error: %v", err)
			}

			if diff := cmp.Diff(tc.msg, got, protocmp.Transform()); diff != "" {
				t.Errorf("AddBinaryProto(%v) did not create a matching proto (-want +got):\n%s", tc.msg, diff)
			}
			mustHaveNoMoreEntries(t, r)
		})
	}
}
