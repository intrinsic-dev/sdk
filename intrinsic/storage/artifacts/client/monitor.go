// Copyright 2023 Intrinsic Innovation LLC

package client

import (
	"context"
	"fmt"
)

// StatusState indicates type of status performed related to update operation on server
type StatusState int

const (
	// StatusUndetermined indicates that nature of action was not known, init state
	StatusUndetermined StatusState = iota
	// StatusContinue indicates in flying status update
	StatusContinue
	// StatusSuccess indicates that update operation finished successfully
	StatusSuccess
	// StatusFailure indicates that update operation finished unsuccessfully
	StatusFailure
)

var names = []string{"Undetermined", "Continue", "Success", "Failure"}

func (s StatusState) String() string {
	return names[s]
}

// ProgressUpdate represents information about upload update.
type ProgressUpdate struct {
	Status  StatusState
	Current int64
	Total   int64
	Err     error
	Message string
}

func (p ProgressUpdate) String() string {
	return fmt.Sprintf("%s: (%d/%d); Err: %v; msg: %s",
		p.Status, p.Current, p.Total, p.Err, p.Message)
}

// ProgressMonitor allows callers to receive update about uploads.
type ProgressMonitor interface {
	// UpdateProgress is called every time there is update received from server
	UpdateProgress(ref string, update ProgressUpdate)
}

type progressMonitorKeyType string

const progressMonitorCtxKey = progressMonitorKeyType("progressMonitor")

// SetProgressMonitor attaches progress monitor implementation to context
func SetProgressMonitor(ctx context.Context, monitor ProgressMonitor) context.Context {
	return context.WithValue(ctx, progressMonitorCtxKey, monitor)
}

func getProgressMonitor(ctx context.Context) ProgressMonitor {
	if monitor := ctx.Value(progressMonitorCtxKey); monitor != nil {
		return monitor.(ProgressMonitor)
	}
	return nil
}
