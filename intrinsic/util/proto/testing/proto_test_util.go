// Copyright 2023 Intrinsic Innovation LLC

// Package prototestutil contains helpers for handling protos in tests.
package prototestutil

import (
	"testing"

	"google.golang.org/protobuf/proto"
	anypb "google.golang.org/protobuf/types/known/anypb"
)

// MustWrapInAny is a test helper that wraps a proto message in an Any proto.
func MustWrapInAny(t *testing.T, m proto.Message) *anypb.Any {
	t.Helper()
	p, err := anypb.New(m)
	if err != nil {
		t.Fatalf("Unable to wrap proto message: %v ", err)
	}
	return p
}
