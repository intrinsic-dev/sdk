// Copyright 2023 Intrinsic Innovation LLC

package client

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"math/rand"

	log "github.com/golang/glog"
	crv1 "github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/partial"
	crtypes "github.com/google/go-containerregistry/pkg/v1/types"
	"go.uber.org/atomic"
	artifactgrpcpb "intrinsic/storage/artifacts/proto/artifact_go_grpc_proto"
	artifactpb "intrinsic/storage/artifacts/proto/artifact_go_grpc_proto"
)

const (
	chunkIDMaxIncrement int64 = 100
	size4MB             int   = 4 * 1024 * 1024
)

func newTask(ctx context.Context, client artifactgrpcpb.ArtifactServiceApiClient, maxUpdateSize int32, item namedObject, getItemReader itemReader) (_ *uploaderTask, err error) {
	task := &uploaderTask{
		updateSize:   maxUpdateSize,
		monitor:      getProgressMonitor(ctx),
		client:       client,
		terminalChan: make(chan error),
	}

	// in case caller didn't set any content size, we will force 4MB
	if task.updateSize <= 0 {
		task.updateSize = int32(size4MB)
	}

	task.descriptor, err = partial.Descriptor(item)
	if err != nil {
		return nil, err
	}

	task.reader, err = getItemReader()
	if err != nil {
		return nil, err
	}

	task.name, err = item.Name()
	if err != nil {
		return nil, err
	}
	return task, nil

}

type uploaderTask struct {
	reader       io.ReadCloser
	client       artifactgrpcpb.ArtifactServiceApiClient
	descriptor   *crv1.Descriptor
	monitor      ProgressMonitor
	updateSize   int32
	name         string
	terminalChan chan error
}

func runWithContext(ctx context.Context, task *uploaderTask) func() error {
	return func() error {
		return task.runWithCtx(ctx)
	}
}

func (t *uploaderTask) run() error {
	return t.runWithCtx(context.Background())
}

func (t *uploaderTask) runWithCtx(ctx context.Context) error {
	log.Infof("starting upload: %s", t.getShortName())
	t.updateMonitor(ProgressUpdate{
		Status:  StatusUndetermined,
		Current: 0,
		Total:   t.descriptor.Size,
		Message: "waiting for upload",
	})

	stream, err := t.client.WriteContentStream(ctx)
	if err != nil {
		return fmt.Errorf("cannot contact upstream: %s", err)
	}
	defer func() {
		log.Infof("closing client connection: %s", t.getShortName())
		stream.CloseSend()
	}() // in any case we are done here.

	go t.goProcessInbound(ctx, stream)

	contentBuffer := make([]byte, t.updateSize)
	idTracker := atomic.NewInt64(0)
	firstChunk := true

	var totalSize int64 = 0
	var ctxErr error = nil
	for ctxErr = ctx.Err(); ctxErr == nil; ctxErr = ctx.Err() {
		log.Infof("%s: sending chunk %5d: (%d/%d) in %d increment", t.getShortName(), idTracker.Load(), totalSize, t.descriptor.Size, t.updateSize)
		action := artifactpb.UpdateAction_UPDATE_ACTION_UPDATE
		length, err := t.reader.Read(contentBuffer)
		if err != nil {
			if err != io.EOF {
				t.abortRun(firstChunk, idTracker, stream)
				return fmt.Errorf("failed to read from source: %w", err)
			}
			action = artifactpb.UpdateAction_UPDATE_ACTION_COMMIT
		}

		// let's make defensive copy of slice to ensure we do not run into issues
		// if Message is delayed "on wire".
		dataSlice := make([]byte, length)
		copy(dataSlice, contentBuffer[:length])

		updateRequest := &artifactpb.UpdateRequest{
			Ref:       t.name,
			MediaType: string(t.descriptor.MediaType),
			Action:    action,
			// randomizing sequence, no need for cryptographically safe random
			ChunkId: idTracker.Add(rand.Int63n(chunkIDMaxIncrement)),
			Length:  int32(length),
			Data:    dataSlice,
		}
		log.Infof("chunk id: %d", updateRequest.ChunkId)

		if firstChunk {
			digest := t.descriptor.Digest.String()
			updateRequest.ExpectedDigest = &digest
			updateRequest.Content = t.getArtifactDescriptor()
			firstChunk = false
		}

		err = stream.Send(updateRequest)
		if err != nil {
			return fmt.Errorf("send failed: %s", err)
		}

		totalSize += int64(length)
		if action == artifactpb.UpdateAction_UPDATE_ACTION_COMMIT {
			break
		}
	}

	if ctxErr != nil {
		// we terminated loop with context. This means we may not have finished
		// full update. If we already did commit, we will get and error on abort
		// but if we didn't finish, we will put Abort on wire to make sure we
		// abort requests in flight
		t.abortRun(firstChunk, idTracker, stream)
		return fmt.Errorf("premature termination: %w", ctxErr)
	}

	return <-t.terminalChan
}

func (t *uploaderTask) abortRun(firstChunk bool, idTracker *atomic.Int64, stream artifactgrpcpb.ArtifactServiceApi_WriteContentStreamClient) {
	if !firstChunk {
		// we already sent some data to server, let's abort write
		abortRequest := &artifactpb.UpdateRequest{
			Ref:     t.name,
			Action:  artifactpb.UpdateAction_UPDATE_ACTION_ABORT,
			ChunkId: idTracker.Add(chunkIDMaxIncrement),
		}
		if errSend := stream.Send(abortRequest); errSend != nil {
			log.Errorf("failed to send Abort to server: %s", errSend)
		}
	}
}

func (t *uploaderTask) getShortName() string {
	return t.name // for now
}

func (t *uploaderTask) getArtifactDescriptor() *artifactpb.ArtifactDescriptor {
	digest := t.descriptor.Digest.String()
	return &artifactpb.ArtifactDescriptor{
		MediaType:   string(t.descriptor.MediaType),
		Digest:      &digest,
		Size:        &t.descriptor.Size,
		Annotations: t.descriptor.Annotations,
	}
}

func (t *uploaderTask) goProcessInbound(ctx context.Context, stream artifactgrpcpb.ArtifactServiceApi_WriteContentStreamClient) {
	defer close(t.terminalChan)
	for ctx.Err() == nil {
		msg, err := stream.Recv()
		log.Infof("err: %v, msg %v", err, msg)
		if err != nil {
			if err != io.EOF {
				t.updateMonitor(ProgressUpdate{
					Status: StatusFailure,
					Err:    err,
				})
				t.terminalChan <- err
			} else {
				t.terminalChan <- nil
			}
			return
		}
		switch *msg.Action {
		case artifactpb.UpdateAction_UPDATE_ACTION_COMMIT:
			t.updateMonitor(ProgressUpdate{
				Status:  StatusSuccess,
				Current: *msg.Total,
				Total:   *msg.Total,
				Message: fmt.Sprintf("[%5d]: done", msg.ChunkId),
			})
			t.terminalChan <- nil
			return
		case artifactpb.UpdateAction_UPDATE_ACTION_ABORT:
			t.updateMonitor(ProgressUpdate{
				Status:  StatusFailure,
				Current: *msg.Total,
				Total:   t.descriptor.Size,
				Message: fmt.Sprintf("[%5d]: aborted", msg.ChunkId),
			})
			t.terminalChan <- nil
			return
		case artifactpb.UpdateAction_UPDATE_ACTION_UPDATE:
			t.updateMonitor(ProgressUpdate{
				Status:  StatusContinue,
				Current: *msg.Total,
				Total:   t.descriptor.Size,
				Message: fmt.Sprintf("[%5d]: uploading", msg.ChunkId),
			})
		default:
			continue
		}
	}
	t.terminalChan <- ctx.Err()
}

func (t *uploaderTask) updateMonitor(update ProgressUpdate) {
	if t.monitor != nil {
		t.monitor.UpdateProgress(t.getShortName(), update)
	}
}

type itemReader func() (io.ReadCloser, error)

func bytesReader(extract func() ([]byte, error)) itemReader {
	return func() (io.ReadCloser, error) {
		content, err := extract()
		if err != nil {
			return nil, err
		}
		return io.NopCloser(bytes.NewReader(content)), nil
	}
}

func asDigestNamed(desc partial.Describable) namedObject {
	return asNamedObject(func() (string, error) {
		digest, err := desc.Digest()
		if err != nil {
			return "", err
		}
		return digest.String(), nil
	}, desc)
}

func asSimplyNamed(name string, desc partial.Describable) namedObject {
	return asNamedObject(func() (string, error) {
		return name, nil
	}, desc)
}

func asNamedObject(name func() (string, error), desc partial.Describable) namedObject {
	return &describableObject{
		describable: desc,
		nameFx:      name,
	}
}

type namedObject interface {
	partial.Describable
	Name() (string, error)
}

type describableObject struct {
	describable partial.Describable
	nameFx      func() (string, error)
}

func (d *describableObject) Digest() (crv1.Hash, error) {
	return d.describable.Digest()
}

func (d *describableObject) MediaType() (crtypes.MediaType, error) {
	return d.describable.MediaType()
}

func (d *describableObject) Size() (int64, error) {
	return d.describable.Size()
}

func (d *describableObject) Name() (string, error) {
	return d.nameFx()
}

type descWrap struct {
	value crv1.Descriptor
}

func (c descWrap) Digest() (crv1.Hash, error) {
	return c.value.Digest, nil
}

func (c descWrap) MediaType() (crtypes.MediaType, error) {
	return c.value.MediaType, nil
}

func (c descWrap) Size() (int64, error) {
	return c.value.Size, nil
}
