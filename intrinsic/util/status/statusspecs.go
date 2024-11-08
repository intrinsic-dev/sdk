// Copyright 2023 Intrinsic Innovation LLC

// Package statusspecs provides easy creation of extended status from declarations.
//
// Extended Status are a way to provide error information in the system and to a
// user eventually. The API in this file enables to read declaration and static
// information of errors from a binary proto file. The proto file must contain a
// message of type intrinsic_proto.assets.StatusSpecs (alternatively, this can
// also be provided as a static list once during initialization).
//
// General use is to call InitFromFile() once per process in its main()
// function. After that, Create() can be used to create errors easily.
// Referencing the respective error code, static information such as
// title and recovery instructions are read from the file. Errors which are not
// declared will raise a warning. The proto file can also be used to generate
// documentation.
//
// This API is intended to be used for a specific component which is run as a
// process, it is not to be used in API libraries. Call this in a process's
// main() function, not in a library. This must finish before calling any other
// function, in particular before any call to Create!
package statusspecs

import (
	"fmt"
	"os"
	"time"

	log "github.com/golang/glog"
	"google.golang.org/protobuf/proto"
	"intrinsic/util/status/extstatus"

	specpb "intrinsic/assets/proto/status_spec_go_proto"
	contextpb "intrinsic/logging/proto/context_go_proto"
	espb "intrinsic/util/status/extended_status_go_proto"
)

type initData struct {
	component string
	specs     map[uint32]*specpb.StatusSpec
}

var (
	pkgData initData
)

// InitFromFile initializes status specs from a file.
func InitFromFile(component string, filename string) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}

	specFile := &specpb.StatusSpecs{}

	if err = proto.Unmarshal(data, specFile); err != nil {
		return err
	}

	specs := map[uint32]*specpb.StatusSpec{}
	for _, spec := range specFile.StatusInfo {
		specs[spec.GetCode()] = spec
	}

	pkgData = initData{
		component: component,
		specs:     specs,
	}

	return nil
}

// InitFromList initializes status specs from a given list.
func InitFromList(component string, statusSpecs []*specpb.StatusSpec) error {
	specs := map[uint32]*specpb.StatusSpec{}
	for _, spec := range statusSpecs {
		specs[spec.GetCode()] = spec
	}

	pkgData = initData{
		component: component,
		specs:     specs,
	}

	return nil
}

// createOptions defines optional arguments to the Create call.
type createOptions struct {
	timestamp    *time.Time
	debugMessage string
	logContext   *contextpb.Context
	context      []*espb.ExtendedStatus
}

// CreateOption is a function type for modifying createOptions.
type CreateOption func(*createOptions)

// WithTimestamp returns an option function to set the timestamp on the created extended status.
func WithTimestamp(timestamp time.Time) CreateOption {
	return func(o *createOptions) {
		o.timestamp = &timestamp
	}
}

// WithDebugMessage returns an option function to set the debug report message on the created extended status.
func WithDebugMessage(message string) CreateOption {
	return func(o *createOptions) {
		o.debugMessage = message
	}
}

// WithLogContext returns an option function to set the log context extended status.
func WithLogContext(logContext *contextpb.Context) CreateOption {
	return func(o *createOptions) {
		o.logContext = proto.Clone(logContext).(*contextpb.Context)
	}
}

// WithContextProto returns an option function to add a context from proto to the created extended status.
func WithContextProto(context *espb.ExtendedStatus) CreateOption {
	return func(o *createOptions) {
		o.context = append(o.context, proto.Clone(context).(*espb.ExtendedStatus))
	}
}

// WithContext returns an option function to add a context from an ExtendedStatus wrapper to the created extended status.
func WithContext(context *extstatus.ExtendedStatus) CreateOption {
	return func(o *createOptions) {
		o.context = append(o.context, proto.Clone(context.Proto()).(*espb.ExtendedStatus))
	}
}

// Create creates an ExtendedStatus based on information initialized from specs.
func Create(code uint32, userMessage string, options ...CreateOption) *extstatus.ExtendedStatus {
	opts := createOptions{}
	for _, optFunc := range options {
		optFunc(&opts)
	}

	if pkgData.component == "" {
		log.Warningf("No component specified when populating error %d, call an Init* function.", code)
	}

	title := ""
	userInstructions := ""
	spec, ok := pkgData.specs[code]

	if ok {
		title = spec.GetTitle()
		userInstructions = spec.GetRecoveryInstructions()
	} else {
		title = fmt.Sprintf("Undeclared error %s:%d", pkgData.component, code)
		opts.context = append(opts.context, &espb.ExtendedStatus{
			StatusCode: &espb.StatusCode{
				Component: "ai.intrinsic.errors",
				Code:      604,
			},
			Severity: espb.ExtendedStatus_WARNING,
			Title:    "Error code not declared",
			UserReport: &espb.ExtendedStatus_UserReport{
				Message:      fmt.Sprintf("The code %s:%d has not been declared by the component.", pkgData.component, code),
				Instructions: fmt.Sprintf("Inform the owner of %s to add error %d to the status specs file.", pkgData.component, code),
			},
		})

	}

	return extstatus.New(pkgData.component, code,
		extstatus.WithTimestamp(*opts.timestamp),
		extstatus.WithTitle(title),
		extstatus.WithUserMessage(userMessage),
		extstatus.WithUserInstructions(userInstructions),
		extstatus.WithDebugMessage(opts.debugMessage),
		extstatus.WithContextProtos(opts.context),
		extstatus.WithLogContext(opts.logContext),
	)
}
