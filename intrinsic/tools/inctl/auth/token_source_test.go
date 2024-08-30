// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/pborman/uuid"
	"intrinsic/kubernetes/acl/testing/jwttesting"
)

type TestAPIKeyTokenProvider struct {
	// Tokens contains a map of API keys to tokens.
	Tokens map[string]string
	// Number of times GetIDToken was called.
	RequestCount int
}

func (f *TestAPIKeyTokenProvider) Token(ctx context.Context, apiKey string) (string, error) {
	f.RequestCount++
	if token, ok := f.Tokens[apiKey]; ok {
		return token, nil
	}
	return "", fmt.Errorf("no token for API key %q", apiKey)
}

func TestGetRequestMetadata(t *testing.T) {
	ctx := context.Background()
	apiKey := uuid.New()
	token := jwttesting.MintToken(t, jwttesting.WithEmail("user@example.com"))
	tp := &TestAPIKeyTokenProvider{
		Tokens: map[string]string{
			apiKey: token,
		},
	}
	ts := NewAPIKeyTokenSource(apiKey, tp)

	got, err := ts.GetRequestMetadata(ctx)
	if err != nil {
		t.Fatalf("GetRequestMetadata(ctx) returned an unexpected error: %v", err)
	}

	want := map[string]string{
		"cookie": fmt.Sprintf("auth-proxy=%s", token),
	}
	if diff := cmp.Diff(want, got); diff != "" {
		t.Errorf("GetRequestMetadata(ctx) returned an unexpected diff (-want +got): %v", diff)
	}
}

func TestGetRequestMetadataMissingToken(t *testing.T) {
	ctx := context.Background()
	tp := &TestAPIKeyTokenProvider{}
	ts := NewAPIKeyTokenSource(uuid.New(), tp)

	if got, err := ts.GetRequestMetadata(ctx); err == nil { // if NO error
		t.Fatalf("GetRequestMetadata(ctx) = %v, want error", got)
	}
}

func TestGetRequestMetadataTokenCache(t *testing.T) {
	type req struct {
		offsetFromNow     time.Duration
		wantReqCountAfter int
	}

	tests := []struct {
		name              string
		tokenExpiresAfter time.Duration
		tsOpts            []APIKeyTokenSourceOption
		reqs              []*req
	}{
		{
			name:              "default min token lifetime",
			tokenExpiresAfter: 10 * time.Minute,
			reqs: []*req{
				{
					offsetFromNow:     0,
					wantReqCountAfter: 1,
				},
				{
					offsetFromNow:     5 * time.Minute,
					wantReqCountAfter: 1,
				},
				{
					// Offset into the min token lifetime window by one second.
					offsetFromNow:     10*time.Minute - defaultMinTokenLifetime + 1*time.Second,
					wantReqCountAfter: 2,
				},
			},
		},
		{
			name:              "custom min token lifetime",
			tokenExpiresAfter: 10 * time.Minute,
			tsOpts:            []APIKeyTokenSourceOption{WithMinTokenLifetime(5 * time.Minute)},
			reqs: []*req{
				{
					offsetFromNow:     0,
					wantReqCountAfter: 1,
				},
				{
					offsetFromNow:     3 * time.Minute,
					wantReqCountAfter: 1,
				},
				{
					// Offset into the min token lifetime window by one second.
					offsetFromNow:     10*time.Minute - 5*time.Minute + 1*time.Second,
					wantReqCountAfter: 2,
				},
			},
		},
		{
			name:              "no min token lifetime",
			tokenExpiresAfter: 10 * time.Minute,
			tsOpts:            []APIKeyTokenSourceOption{WithMinTokenLifetime(0)},
			reqs: []*req{
				{
					offsetFromNow:     0,
					wantReqCountAfter: 1,
				},
				{
					// The token is still valid (but will be invalid 1s after).
					offsetFromNow:     10*time.Minute - 1*time.Second,
					wantReqCountAfter: 1,
				},
				{
					offsetFromNow:     10 * time.Minute,
					wantReqCountAfter: 2,
				},
			},
		},
		{
			name:              "min token lifetime larger than token expiry",
			tokenExpiresAfter: 10 * time.Minute,
			tsOpts:            []APIKeyTokenSourceOption{WithMinTokenLifetime(15 * time.Minute)},
			reqs: []*req{
				{
					offsetFromNow:     0,
					wantReqCountAfter: 1,
				},
				{
					offsetFromNow:     0,
					wantReqCountAfter: 2,
				},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			ctx := context.Background()
			apiKey := uuid.New()
			now := time.Now()
			token := jwttesting.MintToken(t, jwttesting.WithExpiresAt(now.Add(tc.tokenExpiresAfter)))
			tp := &TestAPIKeyTokenProvider{
				Tokens: map[string]string{
					apiKey: token,
				},
			}
			ts := NewAPIKeyTokenSource(apiKey, tp, tc.tsOpts...)

			for _, req := range tc.reqs {
				timeNow = func() time.Time {
					return now.Add(req.offsetFromNow)
				}
				t.Cleanup(func() { timeNow = time.Now })

				ts.GetRequestMetadata(ctx)

				if tp.RequestCount != req.wantReqCountAfter {
					t.Errorf("GetRequestMetadata(ctx) called GetIDToken %d times, want %d", tp.RequestCount, req.wantReqCountAfter)
				}
			}
		})
	}
}

func TestRequireTransportSecurity(t *testing.T) {
	tests := []struct {
		name string
		opts []APIKeyTokenSourceOption
		want bool
	}{
		{
			name: "defaults to transport security required",
			opts: []APIKeyTokenSourceOption{},
			want: true,
		},
		{
			name: "can disable transport security",
			opts: []APIKeyTokenSourceOption{WithAllowInsecure()},
			want: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			ts := NewAPIKeyTokenSource(uuid.New(), nil, tc.opts...)

			if got := ts.RequireTransportSecurity(); got != tc.want {
				t.Errorf("RequireTransportSecurity() = %v, want %v", got, tc.want)
			}
		})
	}
}
