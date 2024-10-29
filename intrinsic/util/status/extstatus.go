// Copyright 2023 Intrinsic Innovation LLC

// Package extstatus provides a wrapper for extended status.
//
// See go/intrinsic-extended-status-design for more details.
package extstatus

import (
	"fmt"
	"time"

	statuspb "google.golang.org/genproto/googleapis/rpc/status"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	timestamppb "google.golang.org/protobuf/types/known/timestamppb"
	contextpb "intrinsic/logging/proto/context_go_proto"
	espb "intrinsic/util/status/extended_status_go_proto"
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
	s        *espb.ExtendedStatus
	grpcCode codes.Code
}

// The newOptions struct enables to pass additional information for New*.
//
// It is strongly advised to always set Title and ExternalMessage if the error
// is expected to reach an end user (really, just always set this to something
// legible). The InternalMessage can contain more detailed information which
// potentially only developers require to analyze an error. Whenever you have
// access to a LogContext add it to the status to enable querying additional
// data. You may use the GrpcCode in the context of a GrpcCall, i.e., if the
// exxtended status is expected to be converted to a GRPCStatus eventually.
type newOptions struct {
	timestamp            *time.Time
	title                string
	internalMessage      string
	internalInstructions string
	externalMessage      string
	externalInstructions string
	context              []*espb.ExtendedStatus
	logContext           *contextpb.Context
	grpcCode             codes.Code
}

// NewOption is a function type for modifying newOptions.
type NewOption func(*newOptions)

// WithTimestamp returns an option function to set the timestamp on the created extended status.
func WithTimestamp(timestamp time.Time) NewOption {
	return func(o *newOptions) {
		o.timestamp = &timestamp
	}
}

// WithTitle returns an option function to set the title on the created extended status.
func WithTitle(title string) NewOption {
	return func(o *newOptions) {
		o.title = title
	}
}

// WithInternalMessage returns an option function to set the internal report message on the created extended status.
func WithInternalMessage(message string) NewOption {
	return func(o *newOptions) {
		o.internalMessage = message
	}
}

// WithInternalInstructions returns an option function to set the internal instructions on the created extended status.
func WithInternalInstructions(instructions string) NewOption {
	return func(o *newOptions) {
		o.internalInstructions = instructions
	}
}

// WithExternalMessage returns an option function to set the external report message on the created extended status.
func WithExternalMessage(message string) NewOption {
	return func(o *newOptions) {
		o.externalMessage = message
	}
}

// WithExternalInstructions returns an option function to set the external instructions on the created extended status.
func WithExternalInstructions(instructions string) NewOption {
	return func(o *newOptions) {
		o.externalInstructions = instructions
	}
}

// WithLogContext returns an option function to set the log context extended status.
func WithLogContext(logContext *contextpb.Context) NewOption {
	return func(o *newOptions) {
		o.logContext = proto.Clone(logContext).(*contextpb.Context)
	}
}

// WithContextProto returns an option function to add a context from proto to the created extended status.
func WithContextProto(context *espb.ExtendedStatus) NewOption {
	return func(o *newOptions) {
		o.context = append(o.context, proto.Clone(context).(*espb.ExtendedStatus))
	}
}

// WithContext returns an option function to add a context to the created extended status.
func WithContext(context *ExtendedStatus) NewOption {
	return func(o *newOptions) {
		o.context = append(o.context, proto.Clone(context.Proto()).(*espb.ExtendedStatus))
	}
}

// WithContexts returns an option function to add contexts to the created extended status.
func WithContexts(contexts []*ExtendedStatus) NewOption {
	return func(o *newOptions) {
		for _, context := range contexts {
			o.context = append(o.context, proto.Clone(context.Proto()).(*espb.ExtendedStatus))
		}
	}
}

// WithContextProtos returns an option function to add context protos to the created extended status.
func WithContextProtos(contexts []*espb.ExtendedStatus) NewOption {
	return func(o *newOptions) {
		for _, context := range contexts {
			o.context = append(o.context, proto.Clone(context).(*espb.ExtendedStatus))
		}
	}
}

// WithContextFromError returns an option function to add an error as context to the created extended status.
func WithContextFromError(err error) NewOption {
	return func(o *newOptions) {
		context, ok := FromError(err)
		if !ok {
			// Failed to convert error to extended status, do it the
			// "old-fashioned" way from the error interface
			context = New("unknown-downstream", 0, WithTitle(err.Error()))
		}
		o.context = append(o.context, context.Proto())
	}
}

// WithContextFromErrors returns an option function to add errors as context to the created extended status.
func WithContextFromErrors(errs []error) NewOption {
	return func(o *newOptions) {
		for _, err := range errs {
			context, ok := FromError(err)
			if !ok {
				// Failed to convert error to extended status, do it the
				// "old-fashioned" way from the error interface
				context = New("unknown-downstream", 0, WithTitle(err.Error()))
			}
			o.context = append(o.context, context.Proto())
		}
	}
}

// WithGrpcCode sets code to be used when the error is used in a gRPC context.
// If this is set, calling GRPCStatus on the error will use the given code as
// the generic gRPC error code.
func WithGrpcCode(code codes.Code) NewOption {
	return func(o *newOptions) {
		o.grpcCode = code
	}
}

// New creates an ExtendedStatus with the given StatusCode (component + numeric code).
func New(component string, code uint32, options ...NewOption) *ExtendedStatus {
	p := &espb.ExtendedStatus{StatusCode: &espb.StatusCode{
		Code: code, Component: component}}

	opts := newOptions{grpcCode: codes.Internal}

	for _, optFunc := range options {
		optFunc(&opts)
	}

	p.Title = opts.title
	if opts.internalMessage != "" || opts.internalInstructions != "" {
		p.InternalReport = &espb.ExtendedStatus_Report{
			Message:      opts.internalMessage,
			Instructions: opts.internalInstructions,
		}
	}
	if opts.externalMessage != "" || opts.externalInstructions != "" {
		p.ExternalReport = &espb.ExtendedStatus_Report{
			Message:      opts.externalMessage,
			Instructions: opts.externalInstructions,
		}
	}
	if opts.timestamp != nil {
		p.Timestamp = timestamppb.New(*opts.timestamp)
	} else {
		p.Timestamp = timestamppb.Now()
	}
	for _, context := range opts.context {
		p.Context = append(p.Context, context)
	}
	if opts.logContext != nil {
		p.RelatedTo = &espb.ExtendedStatus_Relations{LogContext: opts.logContext}
	}
	return &ExtendedStatus{s: p, grpcCode: opts.grpcCode}
}

// NewError creates an ExtendedStatus wrapped in an error.
func NewError(component string, code uint32, options ...NewOption) error {
	return New(component, code, options...).Err()
}

// FromProto creates a new ExtendedStatus from a given ExtendedStatus proto.
func FromProto(es *espb.ExtendedStatus) *ExtendedStatus {
	return &ExtendedStatus{s: proto.Clone(es).(*espb.ExtendedStatus)}
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
		extendedStatus, ok := detail.(*espb.ExtendedStatus)
		if !ok {
			continue
		}
		return FromProto(extendedStatus), true
	}

	return nil, false
}

// GRPCStatus converts to and returns a gRPC status.
func (e *ExtendedStatus) GRPCStatus() *status.Status {
	st := status.New(e.grpcCode, e.s.GetTitle())
	ds, err := st.WithDetails(e.s)
	if err != nil {
		return st
	}
	return ds
}

// Proto returns the contained ExtendedStatus proto.
func (e *ExtendedStatus) Proto() *espb.ExtendedStatus {
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
