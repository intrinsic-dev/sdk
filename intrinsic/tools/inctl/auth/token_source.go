// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"google.golang.org/grpc/credentials"
	"intrinsic/kubernetes/acl/jwt"
)

const defaultMinTokenLifetime = time.Minute

var _ credentials.PerRPCCredentials = &APIKeyTokenSource{}

// timeNow can be overridden in tests.
var timeNow = time.Now

type tokenCache struct {
	t      string
	expiry time.Time
}

// APIKeyTokenProvider provides a token for an API key.
type APIKeyTokenProvider interface {
	Token(ctx context.Context, apiKey string) (string, error)
}

// APIKeyTokenSource provides a JWT token retrieved using an API key. Can be
// used as [credentials.PerRPCCredentials] with gRPC clients.
type APIKeyTokenSource struct {
	tp               APIKeyTokenProvider
	apiKey           string
	allowInsecure    bool
	minTokenLifetime time.Duration

	mu sync.Mutex
	c  *tokenCache
}

// APIKeyTokenSourceOption configures an [APIKeyTokenSource].
type APIKeyTokenSourceOption = func(s *APIKeyTokenSource)

// WithAllowInsecure enables the token source to add credentials on insecure
// connections. This can be necessary to pass credentials over local connections
// that use insecure transport security.
func WithAllowInsecure() APIKeyTokenSourceOption {
	return func(s *APIKeyTokenSource) {
		s.allowInsecure = true
	}
}

// WithMinTokenLifetime specifies the minimum amount of time that a token must
// still be valid at the time of the request. Defaults to 1 minute. The token
// source will retrieve a new token if the expiry is too close. Specifying a
// duration larger than the initial lifetime of the token means that it will be
// refreshed on every request.
func WithMinTokenLifetime(d time.Duration) APIKeyTokenSourceOption {
	return func(s *APIKeyTokenSource) {
		s.minTokenLifetime = d
	}
}

// NewAPIKeyTokenSource creates and configures an [APIKeyTokenSource].
func NewAPIKeyTokenSource(apiKey string, tp APIKeyTokenProvider, opts ...APIKeyTokenSourceOption) *APIKeyTokenSource {
	s := &APIKeyTokenSource{
		tp:               tp,
		apiKey:           apiKey,
		minTokenLifetime: defaultMinTokenLifetime,
	}
	for _, opt := range opts {
		opt(s)
	}
	return s
}

// GetRequestMetadata returns request metadata that authenticates the request
// using a JWT retrieved using the API key.
func (s *APIKeyTokenSource) GetRequestMetadata(ctx context.Context, _ ...string) (map[string]string, error) {
	t, err := s.token(ctx)
	if err != nil {
		return nil, fmt.Errorf("could not get account token: %v", err)
	}
	authCookie := &http.Cookie{Name: "auth-proxy", Value: t}
	return map[string]string{"cookie": authCookie.String()}, nil
}

// RequireTransportSecurity returns the configured level of transport security.
// A token source requires transport security unless it was explicitly
// configured using [WithAllowInsecure].
func (s *APIKeyTokenSource) RequireTransportSecurity() bool {
	return !s.allowInsecure
}

func (s *APIKeyTokenSource) token(ctx context.Context) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.c == nil || s.c.expiry.Add(-s.minTokenLifetime).Before(timeNow()) {
		t, err := s.tp.Token(ctx, s.apiKey)
		if err != nil {
			return "", fmt.Errorf("could not get account token: %v", err)
		}
		d, err := jwt.UnmarshalUnsafe(t)
		if err != nil {
			return "", fmt.Errorf("could not unmarshal account token: %v", err)
		}
		s.c = &tokenCache{
			t:      t,
			expiry: time.Unix(d.ExpiresAt, 0),
		}
	}
	return s.c.t, nil
}
