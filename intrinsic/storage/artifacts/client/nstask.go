// Copyright 2023 Intrinsic Innovation LLC

package client

import (
	"context"
	"fmt"
	"io"

	log "github.com/golang/glog"
	"go.uber.org/atomic"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	artifactpb "intrinsic/storage/artifacts/proto/artifact_go_grpc_proto"
)

type nonStreamingTask struct {
	taskData
}

func newNonStreamingTask(base taskData) (uploadTask, error) {
	return &nonStreamingTask{taskData: base}, nil
}

func (t *nonStreamingTask) runWithCtx(ctx context.Context) error {
	log.InfoContextf(ctx, "[%s] starting upload", asShortName(t.name))
	updateMonitor(t.monitor, asShortName(t.name), ProgressUpdate{
		Status:  StatusUndetermined,
		Current: 0,
		Total:   t.descriptor.Size,
		Message: "waiting for upload",
	})

	contentBuffer := make([]byte, 100) // initial exploratory chunk, see b/327799134
	idTracker := atomic.NewInt64(0)
	firstChunk := true
	var totalSize int64 = 0
	var ctxErr error = nil
	for ctxErr = ctx.Err(); ctxErr == nil; ctxErr = ctx.Err() {
		action := artifactpb.UpdateAction_UPDATE_ACTION_UPDATE
		length, err := t.reader.Read(contentBuffer)
		if err != nil {
			if err != io.EOF {
				abortRun(t.name, firstChunk, idTracker, t.sender(ctx))
				return fmt.Errorf("failed to read from source: %w", err)
			}
			action = artifactpb.UpdateAction_UPDATE_ACTION_COMMIT
		}

		updateRequest := &artifactpb.UpdateRequest{
			Ref:       t.name,
			MediaType: string(t.descriptor.MediaType),
			Action:    action,
			// randomizing sequence, no need for cryptographically safe random
			ChunkId: idTracker.Add(nextChunkID()),
			Length:  int32(length),
			Data:    make([]byte, length),
		}
		if length > 0 {
			// let's make defensive copy of slice to ensure we do not run into issues
			// if Message is delayed "on wire".
			copy(updateRequest.Data, contentBuffer[:length])
		}
		totalSize += int64(length)

		log.InfoContextf(ctx, "[%s]: sending chunk %5d (%s): (%d/%d) in %d increment", asShortName(t.name), idTracker.Load(), action, totalSize, t.descriptor.Size, t.updateSize)

		if firstChunk {
			digest := t.descriptor.Digest.String()
			updateRequest.ExpectedDigest = &digest
			updateRequest.Content = asArtifactDescriptor(t.descriptor)
			// reset contentBuffer to full size after first chunk
			contentBuffer = make([]byte, t.updateSize)
		}

		response, err := t.client.WriteContent(ctx, updateRequest)
		if err != nil {
			if firstChunk {
				// on first chunk we need to check if resource we are writing already
				// exists. see b/327799134
				if errStatus, ok := status.FromError(err); ok {
					if errStatus.Code() == codes.AlreadyExists {
						// this item already exists. This could be for various reasons,
						// but we consider this success.
						updateMonitor(t.monitor, asShortName(t.name), ProgressUpdate{
							Status:  StatusSuccess,
							Current: t.descriptor.Size,
							Total:   t.descriptor.Size,
							Message: "already exists",
						})
						log.InfoContextf(ctx, "[%s] already exists", asShortName(t.name))
						return nil // our work is done.
					}
				}
			}
			return fmt.Errorf("[%s] write failed: %w", asShortName(t.name), err)
		}
		firstChunk = false
		doUpdateMonitor(t.monitor, response, t.descriptor)

		updateAction := valueOrDefault(response.Action, action)
		if updateAction == artifactpb.UpdateAction_UPDATE_ACTION_COMMIT ||
			updateAction == artifactpb.UpdateAction_UPDATE_ACTION_ABORT {
			// this is the only valid non-error exit condition, any other path
			// needs to return with error.
			return nil
		}
	}

	return fmt.Errorf("[%s]: premature end: %w", asShortName(t.name), ctxErr)
}

func (t *nonStreamingTask) sender(ctx context.Context) func(request *artifactpb.UpdateRequest) error {
	return func(request *artifactpb.UpdateRequest) error {
		_, err := t.client.WriteContent(ctx, request)
		return err
	}
}
