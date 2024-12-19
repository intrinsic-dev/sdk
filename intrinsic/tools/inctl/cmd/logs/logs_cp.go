// Copyright 2023 Intrinsic Innovation LLC

package logs

import (
	"context"
	"crypto/tls"
	"fmt"
	"os"
	"path"
	"strings"
	"time"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"go.opencensus.io/plugin/ocgrpc"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
	timestamppb "google.golang.org/protobuf/types/known/timestamppb"
	"intrinsic/assets/cmdutils"
	bpb "intrinsic/logging/proto/blob_go_proto"
	dgrpcpb "intrinsic/logging/proto/log_dispatcher_service_go_grpc_proto"
	dpb "intrinsic/logging/proto/log_dispatcher_service_go_grpc_proto"
	"intrinsic/tools/inctl/auth/auth"
)

const (
	defaultLookback    = 10 * time.Minute
	defaultReceiveSize = 100 * 1024 * 1024
	defaultMaxNumItems = 5
)

var (
	flagLookBack               time.Duration
	flagHistoric               bool
	flagHistoricStartTimestamp string
	flagHistoricEndTimestamp   string
)

func newConn(ctx context.Context) (*grpc.ClientConn, error) {
	project := cmdFlags.GetString(cmdutils.KeyProject)
	addr := "www.endpoints." + project + ".cloud.goog:443"

	cfg, err := auth.NewStore().GetConfiguration(project)
	if err != nil {
		return nil, err
	}
	creds, err := cfg.GetDefaultCredentials()
	if err != nil {
		return nil, err
	}

	grpcOpts := []grpc.DialOption{
		grpc.WithPerRPCCredentials(creds),
		grpc.WithStatsHandler(new(ocgrpc.ClientHandler)),
		grpc.WithTransportCredentials(credentials.NewTLS(&tls.Config{})),
	}
	conn, err := grpc.NewClient(addr, grpcOpts...)
	if err != nil {
		return nil, errors.Wrapf(err, "grpc.Dial(%q)", addr)
	}
	return conn, nil
}

func newLogDispatcherClient(ctx context.Context) (dgrpcpb.LogDispatcherClient, error) {
	conn, err := newConn(ctx)
	if err != nil {
		return nil, err
	}
	return dgrpcpb.NewLogDispatcherClient(conn), nil
}

func writeBlob(blob *bpb.Blob, localDir string) error {
	dir := path.Join(localDir, path.Dir(blob.BlobId))
	if err := os.MkdirAll(dir, os.ModePerm); err != nil {
		return errors.Wrapf(err, "os.MkdirAll %s", dir)
	}
	p := path.Join(localDir, blob.BlobId)
	if err := os.WriteFile(p, blob.GetData(), 0644); err != nil {
		return errors.Wrapf(err, "os.WriteFile of blob to %s", p)
	}
	// Clear the blob data so we can write the rest of the response as a textproto.
	blob.Data = []byte{}
	fmt.Printf("file://%s\n", p)
	return nil
}

func getLogsOnprem(ctx context.Context, eventSource string, dir string) error {
	return errors.New("not implemented")
}

func getLogsFromCloud(ctx context.Context, eventSource string, dir string) error {
	client, err := newLogDispatcherClient(ctx)
	if err != nil {
		return errors.Wrap(err, "newLogDispatcherClient")
	}
	orgID := cmdFlags.GetString(cmdutils.KeyOrganization)
	if orgID == "" {
		return errors.Wrap(err, "org should be specificied")
	}
	if flagHistoricStartTimestamp == "" || flagHistoricEndTimestamp == "" {
		return errors.Wrap(err, "historic start timestamp and historic end timestamp should be specified")
	}
	fmt.Println("Creating cloud cache and loading logs...This may take a while.")
	startTime, err := time.Parse(time.RFC3339, flagHistoricStartTimestamp)
	if err != nil {
		return errors.Wrapf(err, "invalid start timestamp: %s", flagHistoricStartTimestamp)
	}
	endTime, err := time.Parse(time.RFC3339, flagHistoricEndTimestamp)
	if err != nil {
		return errors.Wrapf(err, "invalid end timestamp: %s", flagHistoricEndTimestamp)
	}
	loadRequest := &dpb.LoadCloudLogItemsRequest{
		LoadQuery: &dpb.LoadCloudLogItemsRequest_Query{
			LogSource: &dpb.LogSource{
				EventSource:  eventSource,
				WorkcellName: flagContext,
			},
		},
		StartTime:      timestamppb.New(startTime),
		EndTime:        timestamppb.New(endTime),
		OrganizationId: orgID,
	}
	loadResp, err := client.LoadCloudLogItems(ctx, loadRequest)
	if err != nil {
		return errors.Wrap(err, "client.LoadCloudLogItems")
	}
	if loadResp.Metadata.NumItems == 0 {
		fmt.Println("No logs found matched the query")
		return errors.Wrapf(err, "no logs found matched the query")
	}
	fmt.Println("Finished creating cloud cache.")
	fmt.Println("Getting logs from cloud cache and writing to disk...This may take a while.")
	// Initial sleep to allow the logs to be loaded into the cloud cache.
	time.Sleep(30 * time.Second)
	getReq := &dpb.GetCloudLogItemsRequest{
		Query: &dpb.GetCloudLogItemsRequest_GetQuery{
			GetQuery: &dpb.GetCloudLogItemsRequest_Query{
				LogSource: &dpb.LogSource{
					EventSource:  eventSource,
					WorkcellName: flagContext,
				},
				StartTime: timestamppb.New(startTime),
				EndTime:   timestamppb.New(endTime),
			},
		},
		SessionToken:   loadResp.GetSessionToken(),
		MaxNumItems:    proto.Uint32(defaultMaxNumItems),
		OrganizationId: orgID,
	}
	waitTimeForLogs := 5 * time.Second
	waitAttemptsForLogs := 10
	for {
		getResp, err := client.GetCloudLogItems(ctx, getReq, grpc.MaxCallRecvMsgSize(defaultReceiveSize))
		if err != nil {
			if waitAttemptsForLogs > 0 && strings.Contains(err.Error(), "No logs found") {
				waitAttemptsForLogs--
				fmt.Println("No logs found, waiting again for logs to be loaded...")
				time.Sleep(waitTimeForLogs)
				continue
			}
			return errors.Wrap(err, "client.GetCloudLogItems")
		}
		for _, item := range getResp.GetItems() {
			blob := item.GetBlobPayload()
			if blob != nil {
				writeBlob(blob, dir)
			}
			item.BlobPayload = nil
		}
		responseFilename := fmt.Sprintf("response_%d.pbtxt", time.Now().UnixNano())
		p := path.Join(dir, responseFilename)
		if err = os.WriteFile(p, []byte(prototext.Format(getResp)), 0644); err != nil {
			return errors.Wrapf(err, "os.WriteFile of response to %s", p)
		}
		if len(getResp.GetNextPageCursor()) == 0 {
			break
		}
		getReq = &dpb.GetCloudLogItemsRequest{
			Query: &dpb.GetCloudLogItemsRequest_Cursor{
				Cursor: getResp.GetNextPageCursor(),
			},
			SessionToken:   loadResp.GetSessionToken(),
			MaxNumItems:    proto.Uint32(defaultMaxNumItems),
			OrganizationId: orgID,
		}
	}
	return nil
}

var logsCpCmd = &cobra.Command{
	Use:   "cp <event_source> <destination> [--lookback=600] | --historic [--historic_start_timestamp=2024-08-20T12:00:00Z --historic_end_timestamp=2024-08-20T12:00:00Z]",
	Short: "Copies recently logged blobs & logs to a local folder",
	Long:  "Copies recently logged blobs & logs to a local folder",
	Args:  cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		if flagContext == "minikube" && !flagUseLocalhost {
			fmt.Printf("Context is set to \"minikube\". Setting --use_localhost.\n")
			flagUseLocalhost = true
		}

		ctx := cmd.Context()
		if err := os.MkdirAll(args[1], os.ModePerm); err != nil {
			return errors.Wrapf(err, "os.MkdirAll %s", args[1])
		}

		if flagHistoric {
			return getLogsFromCloud(ctx, args[0], args[1])
		}
		return getLogsOnprem(ctx, args[0], args[1])
	}}

func init() {
	showLogs.AddCommand(logsCpCmd)
	logsCpCmd.Flags().DurationVar(&flagLookBack, "lookback", defaultLookback, "The time window to copy logs from")
	logsCpCmd.Flags().StringVarP(&flagContext, "context", "c", "", "The Kubernetes cluster to use.")
	logsCpCmd.Flags().BoolVar(&flagUseLocalhost, "use_localhost", false, "Connect to localhost instead of using SSH to connecting to the cluster.")
	logsCpCmd.Flags().BoolVar(&flagHistoric, "historic", false, "Uses the cloud to fetch historical logs.")
	logsCpCmd.Flags().StringVar(&flagHistoricStartTimestamp, "historic_start_timestamp", "", "Start timestamp in RFC3339 format for fetching historical logs. eg. 2024-08-20T12:00:00Z")
	logsCpCmd.Flags().StringVar(&flagHistoricEndTimestamp, "historic_end_timestamp", "", "End timestamp in RFC3339 format for fetching historical logs. eg. 2024-08-20T12:00:00Z")
	logsCpCmd.MarkFlagRequired("context")
}
