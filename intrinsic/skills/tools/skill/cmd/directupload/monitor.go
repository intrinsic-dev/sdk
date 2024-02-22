// Copyright 2023 Intrinsic Innovation LLC

package directupload

import (
	"fmt"
	"io"
	"strings"

	"intrinsic/storage/artifacts/client"
)

const (
	// shortNameLength defines the length of SHA section to display, matches docker
	shortNameLength = 13
	// shortNameWithPrefixLength defines minimal length of reference name string to be considered as
	// valid digest
	shortNameWithPrefixLength = shortNameLength + 6
)

// uploadMonitor is simple tool for output progress of the object upload into the provided writer
// in text format.
type uploadMonitor struct {
	writer io.Writer
	refMap map[string]any
}

func newMonitor(w io.Writer) client.ProgressMonitor {
	return &uploadMonitor{
		writer: w,
		refMap: make(map[string]any, 16),
	}
}

func (u *uploadMonitor) UpdateProgress(ref string, update client.ProgressUpdate) {
	shortRef := asShortName(ref)
	status := update.Status
	if status == client.StatusUndetermined || status == client.StatusContinue {
		if _, ok := u.refMap[ref]; !ok {
			u.refMap[ref] = nil // value does not matter
			if len(shortRef) < shortNameLength {
				fmt.Fprintf(u.writer, "%s: uploading...\n", shortRef)
			} else {
				fmt.Fprintf(u.writer, "writing image %q\n", ref)
			}
		}
		// we do not report upload progress
	} else if status == client.StatusSuccess {
		if len(shortRef) < shortNameLength {
			fmt.Fprintf(u.writer, "%s: done\n", shortRef)
		} else {
			fmt.Fprintf(u.writer, "finished writing image %q\n", ref)
		}
		delete(u.refMap, ref)
	} else if status == client.StatusFailure {
		if update.Err != nil {
			fmt.Fprintf(u.writer, "%s FAILED: %s (%s)\n", shortRef, update.Message, update.Err)
		} else {
			fmt.Fprintf(u.writer, "%s FAILED: %s\n", shortRef, update.Message)
		}
		delete(u.refMap, ref)
	}
}

func asShortName(name string) string {
	if strings.HasPrefix(name, "sha") {
		// shaXYZ:IDENTIFIER
		if len(name) > shortNameWithPrefixLength {
			return name[7:shortNameWithPrefixLength]
		}
	}
	return name
}
