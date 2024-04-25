// Copyright 2023 Intrinsic Innovation LLC

// Package extstatus provides a wrapper for extended status.
//
// See go/intrinsic-extended-status-design for more details.
package extstatus

import (
	"errors"
	"fmt"

	ctxpb "intrinsic/logging/proto/context_go_proto"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	estpb "intrinsic/util/status/extended_status_go_proto"
)

// The ExtendedStatus wrapper implements a builder pattern to collect status information.
//
// Use the Err() function to create an error to return in functions.
//
// Example:
//
//	return nil, extstatus.NewError("ai.intrinsic.my_service", 2343,
//	              &extstatus.Info{Title: "Failed to ...",
//	                              ExternalMessage: "External report"})
type ExtendedStatus struct {
	s *estpb.ExtendedStatus
}

// The Info struct enables to pass additional information for an ExtendedStatus.
//
// It is strongly advised to always set Title and ExternalMessage if the error
// is expected to reach an end user (really, just always set this to something
// legible). The InternalMessage can contain more detailed information which
// potentially only developers require to analyze an error. Whenever you have
// access to a LogContext add it to the status to enable querying additional
// data.
type Info struct {
	Title             string
	InternalMessage   string
	ExternalMessage   string
	Context           []*estpb.ExtendedStatus
	ContextFromErrors []error
	LogContext        *ctxpb.Context
}

// New creates an ExtendedStatus with the given StatusCode (component + numeric code).
func New(component string, code uint32, info *Info) *ExtendedStatus {
	p := &estpb.ExtendedStatus{StatusCode: &estpb.StatusCode{
		Code: code, Component: component}}
	if info.Title != "" {
		p.Title = info.Title
	}
	if info.InternalMessage != "" {
		p.InternalReport = &estpb.ExtendedStatus_Report{Message: info.InternalMessage}
	}
	if info.ExternalMessage != "" {
		p.ExternalReport = &estpb.ExtendedStatus_Report{Message: info.ExternalMessage}
	}
	for _, context := range info.Context {
		p.Context = append(p.Context, context)
	}
	for _, errContext := range info.ContextFromErrors {
		context, err := FromError(errContext)
		if err != nil {
			// Failed to convert error to extended status, do it the
			// "old-fashioned" way from the error interface
			context = New("unknown-downstream", 0,
				&Info{Title: errContext.Error()})
		}
		p.Context = append(p.Context, context.Proto())
	}
	if info.LogContext != nil {
		p.LogContext = info.LogContext
	}
	return &ExtendedStatus{s: p}
}

// NewError creates an ExtendedStatus wrapped in an error.
func NewError(component string, code uint32, info *Info) error {
	return New(component, code, info).Err()
}

// FromProto creates a new ExtendedStatus from a given ExtendedStatus proto.
func FromProto(es *estpb.ExtendedStatus) *ExtendedStatus {
	return &ExtendedStatus{s: proto.Clone(es).(*estpb.ExtendedStatus)}
}

// FromError converts an error to an ExtendedStatus. This may fail if the error
// was not created from an ExtendedStatus.
func FromError(err error) (*ExtendedStatus, error) {
	e, ok := err.(*Error)
	if ok {
		return e.es, nil
	}

	return nil, errors.New("Failed to convert error to ExtendedStatus")
}

// FromGRPCError converts an error that originated from a gRPC function call to
// a new ExtendedStatus. This is called on the client side, i.e., a gRPC client
// that received an error when invoking a service. This may fail if the error is
// not a gRPC status/error (but some arbitrary error) or if the gRPC status does
// not have an ExtendedStatus detail.
// Use this, for example,  if you called a gRPC service as a client and want to
// use extended status information for more specific handling of the error.
// To just pass an error as context use ContextFromErrors when creating the
// caller component's extended status to pass on the error.
func FromGRPCError(err error) (*ExtendedStatus, error) {
	grpcStatus, ok := status.FromError(err)
	if !ok {
		return nil, fmt.Errorf("Failed to convert error to gRPC status")
	}
	details := grpcStatus.Details()
	if len(details) == 0 {
		return nil, fmt.Errorf("gRPC status has no error details")
	}
	for _, detail := range details {
		extendedStatus, ok := detail.(*estpb.ExtendedStatus)
		if !ok {
			continue
		}
		return FromProto(extendedStatus), nil
	}

	return nil, fmt.Errorf("No extended status error detail on error")
}

// GRPCStatus converts to and returns a gRPC status.
func (e *ExtendedStatus) GRPCStatus() *status.Status {
	st := status.New(codes.Internal, e.s.GetTitle())
	ds, err := st.WithDetails(e.s)
	if err != nil {
		return st
	}
	return ds
}

// Proto returns the contained ExtendedStatus proto.
func (e *ExtendedStatus) Proto() *estpb.ExtendedStatus {
	return e.s
}

// Err converts to an error.
func (e *ExtendedStatus) Err() error {
	return &Error{es: e}
}

// Error wraps an ExtendedStatus. It implements error and gRPC's Status.
type Error struct {
	es *ExtendedStatus
}

// Error implements error interface and returns the title as error string.
func (e *Error) Error() string {
	return fmt.Sprintf("%s:%d: %s", e.es.Proto().GetStatusCode().GetComponent(),
		e.es.Proto().GetStatusCode().GetCode(),
		e.es.Proto().GetTitle())
}

// GRPCStatus implements the golang grpc status interface and returns a gRPC status.
func (e *Error) GRPCStatus() *status.Status {
	return e.es.GRPCStatus()
}

// Is implements future error.Is functionality.
// A Error is equivalent if StatusCodes are identical.
func (e *Error) Is(target error) bool {
	tse, ok := target.(*Error)
	if !ok {
		return false
	}
	return proto.Equal(e.es.s.GetStatusCode(), tse.es.s.GetStatusCode())
}
