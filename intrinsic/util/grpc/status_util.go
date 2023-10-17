// Copyright 2023 Intrinsic Innovation LLC

// Package statusutil provides helper function for dealing with gRPC statuses
// and errors.
package statusutil

import (
	log "github.com/golang/glog"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Wrap generates a new gRPC status with the provided context.  The error code
// is unchanged.
func Wrap(err error, format string, a ...any) error {
	if err == nil {
		return nil
	}
	s := status.Convert(err)
	a = append(a, s.Message())
	return status.Errorf(s.Code(), format+": %v", a...)
}

// Obscure will generate a new error with the given format.  The original
// message details will be removed from the message, but will be logged with
// the appropriate context (at the calling location).  A nil error returns a
// nil.
func Obscure(err error, format string, a ...any) error {
	if err == nil {
		return nil
	}
	s := status.Convert(err)
	ns := status.Errorf(s.Code(), format, a...)

	a = append(a, s.Message())
	log.InfoDepthf(1, format+": %v", a...)

	return ns
}

// NewInternalError creates a new status with an internal error code and the
// provided message.
func NewInternalError(format string, a ...any) error {
	return status.Errorf(codes.Internal, format, a...)
}
