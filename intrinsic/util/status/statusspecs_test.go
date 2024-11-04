// Copyright 2023 Intrinsic Innovation LLC

package statusspecs

import (
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/testing/protocmp"
	timestamppb "google.golang.org/protobuf/types/known/timestamppb"
	specpb "intrinsic/assets/proto/status_spec_go_proto"
	ctxpb "intrinsic/logging/proto/context_go_proto"
	espb "intrinsic/util/status/extended_status_go_proto"
	"intrinsic/util/status/extstatus"
)

func TestInitFromList(t *testing.T) {
	err := InitFromList("ai.intrinsic.test", []*specpb.StatusSpec{
		&specpb.StatusSpec{
			Code:                 10001,
			Title:                "Error 1",
			RecoveryInstructions: "Test instructions 1",
		},
		&specpb.StatusSpec{
			Code:                 10002,
			Title:                "Error 2",
			RecoveryInstructions: "Test instructions 2",
		},
	})
	if err != nil {
		t.Fatalf("Failed InitFromList: %v", err)
	}

	timestamp, _ := time.Parse(time.RFC3339, "2024-03-26T11:51:13Z")

	tests := []struct {
		name string
		got  *extstatus.ExtendedStatus
		want *espb.ExtendedStatus
	}{
		{"Create10001",
			Create(10001, "Ext 1", WithTimestamp(timestamp)),
			&espb.ExtendedStatus{
				StatusCode: &espb.StatusCode{
					Component: "ai.intrinsic.test", Code: 10001,
				},
				Title:     "Error 1",
				Timestamp: &timestamppb.Timestamp{Seconds: 1711453873},
				ExternalReport: &espb.ExtendedStatus_Report{
					Message:      "Ext 1",
					Instructions: "Test instructions 1",
				},
			},
		},
		{"Create10002",
			Create(10002, "Ext 2", WithTimestamp(timestamp)),
			&espb.ExtendedStatus{
				StatusCode: &espb.StatusCode{
					Component: "ai.intrinsic.test", Code: 10002,
				},
				Title:     "Error 2",
				Timestamp: &timestamppb.Timestamp{Seconds: 1711453873},
				ExternalReport: &espb.ExtendedStatus_Report{
					Message:      "Ext 2",
					Instructions: "Test instructions 2",
				},
			},
		},
		{"Create20001NotDeclared",
			Create(20001, "Ext 2", WithTimestamp(timestamp)),
			&espb.ExtendedStatus{
				StatusCode: &espb.StatusCode{
					Component: "ai.intrinsic.test", Code: 20001,
				},
				Timestamp: &timestamppb.Timestamp{Seconds: 1711453873},
				ExternalReport: &espb.ExtendedStatus_Report{
					Message: "Ext 2",
				},
				Title: "Undeclared error ai.intrinsic.test:20001",
				Context: []*espb.ExtendedStatus{
					{
						StatusCode: &espb.StatusCode{
							Component: "ai.intrinsic.errors", Code: 604,
						},
						Title:    "Error code not declared",
						Severity: espb.ExtendedStatus_WARNING,
						ExternalReport: &espb.ExtendedStatus_Report{
							Message:      "The code ai.intrinsic.test:20001 has not been declared by the component.",
							Instructions: "Inform the owner of ai.intrinsic.test to add error 20001 to the status specs file.",
						},
					},
				},
			},
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if diff := cmp.Diff(test.want, test.got.Proto(), protocmp.Transform()); diff != "" {
				t.Errorf("%s returned unexpected diff (-want +got):\n%s", test.name, diff)
			}
		})
	}
}

func TestCreateOptions(t *testing.T) {
	err := InitFromList("ai.intrinsic.test", []*specpb.StatusSpec{
		&specpb.StatusSpec{
			Code:                 10001,
			Title:                "Error 1",
			RecoveryInstructions: "Test instructions 1",
		},
	})
	if err != nil {
		t.Fatalf("Failed InitFromList: %v", err)
	}

	timestamp, _ := time.Parse(time.RFC3339, "2024-03-26T11:51:13Z")
	logContext := &ctxpb.Context{
		ExecutiveSessionId:    1,
		ExecutivePlanId:       2,
		ExecutivePlanActionId: 3,
	}

	got := Create(10001, "Ext 1",
		WithTimestamp(timestamp),
		WithInternalReportMessage("Int message"),
		WithInternalReportInstructions("Int instructions"),
		WithLogContext(logContext),
		WithContext(extstatus.New("ai.intrinsic.context1", 1234,
			extstatus.WithTitle("Foo"),
			extstatus.WithTimestamp(timestamp))),
		WithContextProto(&espb.ExtendedStatus{
			StatusCode: &espb.StatusCode{
				Component: "ai.intrinsic.context2",
				Code:      2345,
			},
			Title: "Bar",
		}))

	want := &espb.ExtendedStatus{
		StatusCode: &espb.StatusCode{
			Component: "ai.intrinsic.test", Code: 10001,
		},
		Title:     "Error 1",
		Timestamp: &timestamppb.Timestamp{Seconds: 1711453873},
		ExternalReport: &espb.ExtendedStatus_Report{
			Message:      "Ext 1",
			Instructions: "Test instructions 1",
		},
		InternalReport: &espb.ExtendedStatus_Report{
			Message:      "Int message",
			Instructions: "Int instructions",
		},
		RelatedTo: &espb.ExtendedStatus_Relations{
			LogContext: &ctxpb.Context{
				ExecutiveSessionId:    1,
				ExecutivePlanId:       2,
				ExecutivePlanActionId: 3,
			},
		},
		Context: []*espb.ExtendedStatus{
			{
				StatusCode: &espb.StatusCode{
					Component: "ai.intrinsic.context1",
					Code:      1234,
				},
				Title:     "Foo",
				Timestamp: &timestamppb.Timestamp{Seconds: 1711453873},
			},
			{
				StatusCode: &espb.StatusCode{
					Component: "ai.intrinsic.context2",
					Code:      2345,
				},
				Title: "Bar",
			},
		},
	}

	if diff := cmp.Diff(want, got.Proto(), protocmp.Transform()); diff != "" {
		t.Errorf("CreateWithOptions returned unexpected diff (-want +got):\n%s", diff)
	}
}
