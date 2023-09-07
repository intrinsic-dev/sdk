// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package resolvercache caches descriptors to parse textprotos.
package resolvercache

import (
	"context"
	"fmt"

	dpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"google.golang.org/protobuf/reflect/protoregistry"
	"intrinsic/util/proto/registryutil"
)

// Resolver fulfills prototext's Resolver interface to Marshal and Unmarshal
// textprotos.
type Resolver interface {
	protoregistry.ExtensionTypeResolver
	protoregistry.MessageTypeResolver
}

// FetchFn is the base callback type used by the resolver.  It must return the
// resolver responsible for a particular id.
type FetchFn func(ctx context.Context, id string) (Resolver, error)

// ResolverCache handles fetching and caching of descriptors based on an id.
// An id must be a string, but there are no requirements on the structure.  The
// user must ensure that the FetchFn used to get a resolver for a particular id
// is the one expected by the user when calling Get with the same id.  A string
// was chosen as the interface type here for simplicity, but could
// theoretically be relaxed to simply be comparable.
type ResolverCache struct {
	fetch FetchFn
	data  map[string]Resolver
}

// NewResolverCache creates a new cache given the function to fetch types.
func NewResolverCache(fetch FetchFn) *ResolverCache {
	return &ResolverCache{
		fetch: fetch,
		data:  make(map[string]Resolver),
	}
}

// FetchForFileDescriptorSet is a helper to create a FetchFn from one that
// retrieves file descriptor sets instead.  This will handle the errors
// associated with parsing the set and creating a usable registry.
func FetchForFileDescriptorSet(fetch func(context.Context, string) (*dpb.FileDescriptorSet, error)) FetchFn {
	return func(ctx context.Context, id string) (Resolver, error) {
		set, err := fetch(ctx, id)
		if err != nil {
			return nil, fmt.Errorf("unable to get file descriptor set for %q: %w", id, err)
		}
		types, err := registryutil.NewTypesFromFileDescriptorSet(set)
		if err != nil {
			return nil, fmt.Errorf("unable to build resolver from file descriptor set for %q: %v", id, err)
		}
		return types, nil
	}
}

// Get returns a resolver for the given id, using the cache if possible.
func (rc *ResolverCache) Get(ctx context.Context, id string) (Resolver, error) {
	types, ok := rc.data[id]
	if ok {
		return types, nil
	}
	return rc.Force(ctx, id)
}

// Force returns a resolver for the given id.  It always updates the cache, and
// thus can be used if there is reason to suspect the cache for this id is
// invalid.
func (rc *ResolverCache) Force(ctx context.Context, id string) (Resolver, error) {
	types, err := rc.fetch(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("unable to get resolver for %q: %w", id, err)
	}
	rc.data[id] = types
	return types, nil
}
