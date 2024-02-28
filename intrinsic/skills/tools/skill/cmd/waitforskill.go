// Copyright 2023 Intrinsic Innovation LLC

// Package waitforskill provides helpers to wait for skills to be available.
package waitforskill

import (
	"context"
	"fmt"
	"time"

	srgrpcpb "intrinsic/skills/proto/skill_registry_go_grpc_proto"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Params holds parameters for waitForSkill.
type Params struct {
	// gRPC connection to the skill registry. This will not be used if `Client` is provided and may be
	// omitted in that case.
	Connection *grpc.ClientConn
	// gRPC client for the skill registry. The `Connection` will be ignored (and can be omitted) when
	// this is provided.
	Client srgrpcpb.SkillRegistryClient
	// The ID of the skill to wait for.
	SkillID string
	// If non-empty, then wait for this specific version of the skill.
	SkillIDVersion string
	// How long WaitForSkill should wait.
	WaitDuration time.Duration
}

// WaitForSkill polls the skill registry until matching skill is found.
func WaitForSkill(ctx context.Context, params *Params) error {

	var client srgrpcpb.SkillRegistryClient
	if params.Client != nil {
		client = params.Client
	} else {
		client = srgrpcpb.NewSkillRegistryClient(params.Connection)
	}
	start := time.Now()
	for {
		res, err := client.GetSkill(ctx, &srgrpcpb.GetSkillRequest{
			Id: params.SkillID,
		})
		if err == nil {
			if params.SkillIDVersion == "" || res.GetSkill().GetIdVersion() == params.SkillIDVersion {
				break
			}
			// If we reach this point, it means that another version of the skill is (still) running.
		} else {
			grpcStatus, ok := status.FromError(err)

			if !ok {
				return fmt.Errorf("querying skill registry failed: %w", err)
			}

			// Catch certain error codes and either retry or return an error message with a helpful hint.
			switch grpcStatus.Code() {
			case codes.Unimplemented:
				// Ingress will return Unimplemented if no skill registry is running as part of a solution.
				return fmt.Errorf(
					"querying skill registry failed (is a solution running in the target cluster?): %w", err)
			case codes.NotFound:
				// Wait and retry because skill is not registered yet.
			case codes.Unavailable:
				// Wait and retry, likely due to one of:
				// - Connection error: The skill registry is not reachable, possibly a transient error (e.g.
				//   because of rate-limiting in the Ingress).
				// - Server error: E.g., the skill is already registered but not available yet because the
				//   skill's container is currently starting.
			default:
				return fmt.Errorf("wait failed with grpc error: %w", err)
			}
		}
		timeSince := time.Since(start)
		if timeSince > params.WaitDuration {
			return fmt.Errorf(
				"timed out after %q. Skill may not be running, see skill logs for details.\n"+
					"Last known error: %w", timeSince, err)
		}
		time.Sleep(1 * time.Second)
	}
	return nil
}
