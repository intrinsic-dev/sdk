// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package solutionutil provides helper functions for resolving clusters from solution names
package solutionutil

import (
	"context"
	"errors"
	"fmt"

	"google.golang.org/grpc"
	clusterdiscoverygrpcpb "intrinsic/frontend/cloud/api/clusterdiscovery_grpc_go_proto"
	"intrinsic/tools/inctl/cmd/solution/solution"
)

// GetClusterNameFromSolution returns the cluster in which a solution currently runs.
func GetClusterNameFromSolution(ctx context.Context, conn *grpc.ClientConn, solutionName string) (string, error) {
	solution, err := solution.GetSolution(ctx, conn, solutionName)
	if err != nil {
		return "", fmt.Errorf("failed to get solution: %w", err)
	}
	if solution.GetState() == clusterdiscoverygrpcpb.SolutionState_SOLUTION_STATE_NOT_RUNNING {
		return "", fmt.Errorf("solution is not running")
	}
	if solution.GetClusterName() == "" {
		return "", fmt.Errorf("unknown error: solution is running but cluster is empty")
	}
	return solution.GetClusterName(), nil
}

// GetClusterNameFromSolutionOrDefault checks if solutionName is set and resolves it to cluster
// return default otherwise.
func GetClusterNameFromSolutionOrDefault(ctx context.Context, conn *grpc.ClientConn, solutionName string, defaultCluster string) (string, error) {
	if solutionName != "" {
		cluster, err := GetClusterNameFromSolution(ctx, conn, solutionName)
		if err != nil {
			return "", fmt.Errorf("could not resolve context from solution '%s'"+
				"(please check if the solution is currently running): %w", solutionName, err)
		}
		return cluster, nil
	}
	if defaultCluster == "" {
		return "", errors.New("solution name and default cluster are empty - set exactly one of them")
	}

	return defaultCluster, nil
}
