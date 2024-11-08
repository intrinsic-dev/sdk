// Copyright 2023 Intrinsic Innovation LLC

package extstatus

import (
	"context"
	"errors"
	"fmt"
	"testing"

	"github.com/google/go-cmp/cmp"
	epb "google.golang.org/genproto/googleapis/rpc/errdetails"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/local"
	grpcstatus "google.golang.org/grpc/status"
	"google.golang.org/protobuf/testing/protocmp"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	ctxpb "intrinsic/logging/proto/context_go_proto"
	"intrinsic/testing/grpctest"
	estpb "intrinsic/util/status/extended_status_go_proto"
	testsvcgrpcpb "intrinsic/util/status/test_service_go_grpc_proto"
)

func TestExtendedStatus(t *testing.T) {
	tests := []struct {
		name string
		got  *ExtendedStatus
		want *estpb.ExtendedStatus
	}{
		{"New",
			New("ai.intrinsic.test", 2342),
			&estpb.ExtendedStatus{StatusCode: &estpb.StatusCode{
				Component: "ai.intrinsic.test", Code: 2342}}},
		{"FromProto",
			FromProto(&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Title: "title",
				UserReport: &estpb.ExtendedStatus_UserReport{
					Message: "Ext Msg",
				}}),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Title: "title",
				UserReport: &estpb.ExtendedStatus_UserReport{
					Message: "Ext Msg",
				}}},
		{"SetTitle",
			New("ai.intrinsic.test", 2342, WithTitle("title")),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Title: "title"}},
		{"SetTitleFormat",
			New("ai.intrinsic.test", 2342, WithTitle(fmt.Sprintf("title %s", "foo"))),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Title: "title foo"}},
		{"SetUserReportMessage",
			New("ai.intrinsic.test", 2342, WithUserMessage("m1")),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				UserReport: &estpb.ExtendedStatus_UserReport{Message: "m1"}}},
		{"SetUserReportMessageFormat",
			New("ai.intrinsic.test", 2342, WithUserMessage(fmt.Sprintf("msg %s", "foo"))),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				UserReport: &estpb.ExtendedStatus_UserReport{Message: "msg foo"}}},
		{"SetDebugReportMessage",
			New("ai.intrinsic.test", 2342, WithDebugMessage("m2")),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				DebugReport: &estpb.ExtendedStatus_DebugReport{Message: "m2"}}},
		{"SetDebugReportMessageFormat",
			New("ai.intrinsic.test", 2342, WithDebugMessage(fmt.Sprintf("msg %s", "bar"))),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				DebugReport: &estpb.ExtendedStatus_DebugReport{Message: "msg bar"}}},
		{"AddContext",
			New("ai.intrinsic.test", 2342, WithContextProto(&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.backend_service", Code: 4534},
				UserReport: &estpb.ExtendedStatus_UserReport{Message: "backend unhappy"}})),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Context: []*estpb.ExtendedStatus{
					{StatusCode: &estpb.StatusCode{
						Component: "ai.intrinsic.backend_service", Code: 4534},
						UserReport: &estpb.ExtendedStatus_UserReport{Message: "backend unhappy"}},
				}}},
		{"AddMultipleContexts",
			New("ai.intrinsic.test", 2342, WithContextProtos([]*estpb.ExtendedStatus{
				{StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.backend_service", Code: 4534},
					UserReport: &estpb.ExtendedStatus_UserReport{Message: "backend unhappy"}},
				{StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.backend_service_2", Code: 4444},
					UserReport: &estpb.ExtendedStatus_UserReport{Message: "other backend unhappy"}}})),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Context: []*estpb.ExtendedStatus{
					{StatusCode: &estpb.StatusCode{
						Component: "ai.intrinsic.backend_service", Code: 4534},
						UserReport: &estpb.ExtendedStatus_UserReport{Message: "backend unhappy"}},
					{StatusCode: &estpb.StatusCode{
						Component: "ai.intrinsic.backend_service_2", Code: 4444},
						UserReport: &estpb.ExtendedStatus_UserReport{Message: "other backend unhappy"}},
				}}},
		{"AddContextFromError",
			New("ai.intrinsic.test", 2342, WithContextFromError(
				NewError("ai.intrinsic.backend_service", 4534,
					WithUserMessage("backend unhappy")))),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Context: []*estpb.ExtendedStatus{
					{StatusCode: &estpb.StatusCode{
						Component: "ai.intrinsic.backend_service", Code: 4534},
						UserReport: &estpb.ExtendedStatus_UserReport{Message: "backend unhappy"}},
				}}},
		{"AddContextFromMultipleErrors",
			New("ai.intrinsic.test", 2342, WithContextFromErrors([]error{
				NewError("ai.intrinsic.backend_service", 4534,
					WithUserMessage("backend unhappy")),
				NewError("ai.intrinsic.backend_service_2", 4444,
					WithUserMessage("other backend unhappy"))})),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				Context: []*estpb.ExtendedStatus{
					{StatusCode: &estpb.StatusCode{
						Component: "ai.intrinsic.backend_service", Code: 4534},
						UserReport: &estpb.ExtendedStatus_UserReport{Message: "backend unhappy"}},
					{StatusCode: &estpb.StatusCode{
						Component: "ai.intrinsic.backend_service_2", Code: 4444},
						UserReport: &estpb.ExtendedStatus_UserReport{Message: "other backend unhappy"}},
				}}},
		{"SetLogContext",
			New("ai.intrinsic.test", 2342, WithLogContext(&ctxpb.Context{
				ExecutiveSessionId:    1,
				ExecutivePlanId:       2,
				ExecutivePlanActionId: 3})),
			&estpb.ExtendedStatus{
				StatusCode: &estpb.StatusCode{
					Component: "ai.intrinsic.test", Code: 2342},
				RelatedTo: &estpb.ExtendedStatus_Relations{
					LogContext: &ctxpb.Context{
						ExecutiveSessionId:    1,
						ExecutivePlanId:       2,
						ExecutivePlanActionId: 3}}}},
	}

	for _, test := range tests {
		// Note the subtest here
		t.Run(test.name, func(t *testing.T) {
			if diff := cmp.Diff(test.want, test.got.Proto(),
				protocmp.Transform(),
				protocmp.IgnoreFields(&estpb.ExtendedStatus{}, "timestamp"),
			); diff != "" {
				t.Errorf("%s returned unexpected diff (-want +got):\n%s", test.name, diff)
			}
		})
	}

}

func TestErrorInterface(t *testing.T) {
	es := New("ai.intrinsic.test", 3465, WithTitle("test error"))
	err := es.Err()

	if err.Error() != "ai.intrinsic.test:3465: test error" {
		t.Errorf("Got error %s, want: test error", err.Error())
	}
}

func TestNewError(t *testing.T) {
	err := NewError("ai.intrinsic.test", 3465, WithTitle("test error"), WithDebugMessage("Something went wrong"))

	if err.Error() != "ai.intrinsic.test:3465: test error" {
		t.Errorf("Got error %s, want: test error", err.Error())
	}
	want := &estpb.ExtendedStatus{
		StatusCode: &estpb.StatusCode{
			Component: "ai.intrinsic.test", Code: 3465},
		Title: "test error", DebugReport: &estpb.ExtendedStatus_DebugReport{Message: "Something went wrong"}}

	es, ok := FromError(err)
	if !ok {
		t.Fatalf("Failed to convert error back to ExtendedStatus.")
	}

	if diff := cmp.Diff(want, es.Proto(),
		protocmp.Transform(),
		protocmp.IgnoreFields(&estpb.ExtendedStatus{}, "timestamp"),
	); diff != "" {
		t.Errorf("NewError/FromError returned unexpected diff (-want +got):\n%s", diff)
	}

}

func TestErrorGRPCStatus(t *testing.T) {
	es := New("ai.intrinsic.test", 3465, WithTitle("test error"))
	gs := es.Err().(*Error).GRPCStatus()

	if len(gs.Details()) != 1 {
		t.Errorf("Got %d details, want 1", len(gs.Details()))
	}

	got := gs.Details()[0].(*estpb.ExtendedStatus)
	want := &estpb.ExtendedStatus{
		StatusCode: &estpb.StatusCode{
			Component: "ai.intrinsic.test", Code: 3465},
		Title: "test error"}

	if diff := cmp.Diff(want, got,
		protocmp.Transform(),
		protocmp.IgnoreFields(&estpb.ExtendedStatus{}, "timestamp"),
	); diff != "" {
		t.Errorf("GRPCStatus returned unexpected diff (-want +got):\n%s", diff)
	}
}

func TestErrorGRPCStatusCustomCode(t *testing.T) {
	es := New("ai.intrinsic.test", 3465,
		WithTitle("test error"), WithGrpcCode(codes.InvalidArgument))
	gs := es.Err().(*Error).GRPCStatus()

	if gs.Code() != codes.InvalidArgument {
		t.Errorf("Got code %v, want %v", gs.Code(), codes.InvalidArgument)
	}

	if len(gs.Details()) != 1 {
		t.Errorf("Got %d details, want 1", len(gs.Details()))
	}
}

func TestErrorIs(t *testing.T) {
	err := New("ai.intrinsic.test", 3465, WithTitle("test error")).Err()
	err1 := &Error{es: &ExtendedStatus{s: &estpb.ExtendedStatus{
		StatusCode: &estpb.StatusCode{
			Component: "ai.intrinsic.test", Code: 3465},
		Title: "test error"}}}
	if !errors.Is(err, err1) {
		t.Errorf("Error did not recognize same error code")
	}

	err2 := &Error{es: &ExtendedStatus{s: &estpb.ExtendedStatus{
		StatusCode: &estpb.StatusCode{
			Component: "ai.intrinsic.test", Code: 2}}}}
	if errors.Is(err, err2) {
		t.Errorf("Error did recognize wrong error code")
	}

	err3 := fmt.Errorf("test error")
	if errors.Is(err, err3) {
		t.Errorf("Error did recognize wrong error type")
	}
}

func TestFromGRPCFunctionsSkipUnrelatedDetails(t *testing.T) {
	extStatusProto := &estpb.ExtendedStatus{
		StatusCode: &estpb.StatusCode{
			Component: "ai.intrinsic.test", Code: 2342},
		Title: "title",
		UserReport: &estpb.ExtendedStatus_UserReport{
			Message: "Ext Msg",
		},
	}
	grpcStatus, err := grpcstatus.New(codes.ResourceExhausted, "Request limit exceeded.").
		WithDetails(
			&epb.QuotaFailure{
				Violations: []*epb.QuotaFailure_Violation{{
					Subject:     "Test subject",
					Description: "Limit",
				}}},
			extStatusProto)
	if err != nil {
		t.Fatalf("Failed to create GRPC status: %v", err)
	}

	// FromGRPCError()
	gotExtStatus, ok := FromGRPCError(grpcStatus.Err())
	if !ok {
		t.Errorf("FromGRPCError(%v) did not return ok", grpcStatus.Err())
	}

	if diff := cmp.Diff(extStatusProto, gotExtStatus.Proto(), protocmp.Transform()); diff != "" {
		t.Errorf("FromGRPCError(%v) returned unexpected diff (-want +got):\n%s", grpcStatus.Err(), diff)
	}

	// FromGRPCStatus()
	gotExtStatus, ok = FromGRPCStatus(grpcStatus)
	if !ok {
		t.Errorf("FromGRPCStatus(%v) did not return ok", grpcStatus.Err())
	}

	if diff := cmp.Diff(extStatusProto, gotExtStatus.Proto(), protocmp.Transform()); diff != "" {
		t.Errorf(
			"FromGRPCStatus(%v) returned unexpected diff (-want +got):\n%s", grpcStatus.Err(), diff,
		)
	}

	// FromGRPCStatusProto()
	gotExtStatus, ok = FromGRPCStatusProto(grpcStatus.Proto())
	if !ok {
		t.Errorf("FromGRPCStatusProto(%v) did not return ok", grpcStatus.Err())
	}

	if diff := cmp.Diff(extStatusProto, gotExtStatus.Proto(), protocmp.Transform()); diff != "" {
		t.Errorf(
			"FromGRPCStatusProto(%v) returned unexpected diff (-want +got):\n%s", grpcStatus.Err(), diff,
		)
	}
}

type failService struct{}

func (s *failService) FailingMethod(ctx context.Context, req *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, New("ai.intrinsic.test", 9876, WithTitle("Error Title")).Err()
}

func TestGrpcServiceCall(t *testing.T) {
	server := grpc.NewServer()
	svc := &failService{}

	testsvcgrpcpb.RegisterStatusTestServiceServer(server, svc)
	srvAddr := grpctest.StartServerT(t, server)
	conn, err := grpc.NewClient(srvAddr, grpc.WithTransportCredentials(local.NewCredentials()))
	if err != nil {
		t.Fatalf("failed to create fail service client: %v", err)
	}

	t.Cleanup(func() { conn.Close() })

	client := testsvcgrpcpb.NewStatusTestServiceClient(conn)

	ctx := context.Background()
	_, err = client.FailingMethod(ctx, &emptypb.Empty{})
	if err == nil {
		t.Fatalf("Expected error from FailingMethod")
	}
	extSt, ok := FromGRPCError(err)
	if !ok {
		t.Errorf("FromGRPCError(%v) did not return ok", err)
	}

	want := &estpb.ExtendedStatus{
		StatusCode: &estpb.StatusCode{
			Component: "ai.intrinsic.test", Code: 9876},
		Title: "Error Title"}
	if diff := cmp.Diff(want, extSt.Proto(),
		protocmp.Transform(),
		protocmp.IgnoreFields(&estpb.ExtendedStatus{}, "timestamp"),
	); diff != "" {
		t.Errorf("FromGRPCError(%v) returned unexpected diff (-want +got):\n%s", err, diff)
	}
}
