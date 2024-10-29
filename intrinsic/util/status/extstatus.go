// Copyright 2023 Intrinsic Innovation LLC

// Package extstatus provides a wrapper for extended status.
//
// See go/intrinsic-extended-status-design for more details.
package extstatus

import (
	"fmt"
	"time"

	statuspb "google.golang.org/genproto/googleapis/rpc/status"
	timestamppb "google.golang.org/protobuf/types/known/timestamppb"
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
	Timestamp            *time.Time
	Title                string
	InternalMessage      string
	InternalInstructions string
	ExternalMessage      string
	ExternalInstructions string
	Context              []*estpb.ExtendedStatus
	ContextFromErrors    []error
	LogContext           *ctxpb.Context
}

// New creates an ExtendedStatus with the given StatusCode (component + numeric code).
func New(component string, code uint32, info *Info) *ExtendedStatus {
	p := &estpb.ExtendedStatus{StatusCode: &estpb.StatusCode{
		Code: code, Component: component}}
	if info.Title != "" {
		p.Title = info.Title
	}
	if info.InternalMessage != "" || info.InternalInstructions != "" {
		p.InternalReport = &estpb.ExtendedStatus_Report{
			Message:      info.InternalMessage,
			Instructions: info.InternalInstructions,
		}
	}
	if info.ExternalMessage != "" || info.ExternalInstructions != "" {
		p.ExternalReport = &estpb.ExtendedStatus_Report{
			Message:      info.ExternalMessage,
			Instructions: info.ExternalInstructions,
		}
	}
	if info.Timestamp != nil {
		p.Timestamp = timestamppb.New(*info.Timestamp)
	} else {
		p.Timestamp = timestamppb.Now()
	}
	for _, context := range info.Context {
		p.Context = append(p.Context, context)
	}
	for _, errContext := range info.ContextFromErrors {
		context, ok := FromError(errContext)
		if !ok {
			// Failed to convert error to extended status, do it the
			// "old-fashioned" way from the error interface
			context = New("unknown-downstream", 0, &Info{Title: errContext.Error()})
		}
		p.Context = append(p.Context, context.Proto())
	}
	if info.LogContext != nil {
		p.RelatedTo = &estpb.ExtendedStatus_Relations{LogContext: info.LogContext}
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

// FromError tries to convert an error to an ExtendedStatus. This may fail (and
// ok will be false) if the error was not created from an ExtendedStatus.
func FromError(err error) (es *ExtendedStatus, ok bool) {
	e, ok := err.(*Error)
	if ok {
		return e.es, true
	}

	return nil, false
}

// FromGRPCError tries to convert an error to a new ExtendedStatus. This may
// fail (and ok will be false) if the error is not a gRPC status/error or if the
// gRPC status does not have an ExtendedStatus detail.
//
// Use this, for example, if you called a gRPC service as a client and want to
// use extended status information for more specific handling of a returned
// error. To just pass an error as context use ContextFromErrors when creating
// the caller component's extended status to pass on the error.
func FromGRPCError(err error) (es *ExtendedStatus, ok bool) {
	grpcStatus, ok := status.FromError(err)
	if !ok {
		return nil, false
	}
	return FromGRPCStatus(grpcStatus)
}

// FromGRPCStatusProto tries to convert a gRPC Status proto to a new ExtendedStatus.
// This may fail (and ok will be false) if the gRPC status does not have an
// ExtendedStatus detail.
//
// Use this, for example, if you received an error result from a long-running
// operation on a gRPC service and want to use extended status information for
// more specific handling of the returned error.
func FromGRPCStatusProto(s *statuspb.Status) (es *ExtendedStatus, ok bool) {
	return FromGRPCStatus(status.FromProto(s))
}

// FromGRPCStatus tries to convert a gRPC Status to a new ExtendedStatus. This
// may fail (and ok will be false) if the gRPC status does not have an
// ExtendedStatus detail.
func FromGRPCStatus(s *status.Status) (es *ExtendedStatus, ok bool) {
	details := s.Details()
	if len(details) == 0 {
		return nil, false
	}
	for _, detail := range details {
		extendedStatus, ok := detail.(*estpb.ExtendedStatus)
		if !ok {
			continue
		}
		return FromProto(extendedStatus), true
	}

	return nil, false
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
