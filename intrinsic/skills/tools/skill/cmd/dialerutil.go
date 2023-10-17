// Copyright 2023 Intrinsic Innovation LLC

// Package dialerutil has helpers for specifying grpc dialer information for the installer service.
package dialerutil

import (
	"context"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"errors"
	"fmt"
	"math"
	"strings"

	oauth2 "golang.org/x/oauth2/google"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/credentials/oauth"
	"google.golang.org/grpc/metadata"
	"intrinsic/tools/inctl/auth"
)

const (
	maxMsgSize = math.MaxInt64
)

// BasicAuth provides the data for perRPC authentication with the relay for the installer.
//
// Implements the `credentials.PerRPCCredentials` interface.
type BasicAuth struct {
	username string
	password string
}

// GetRequestMetadata returns the map {"authorization": "Basic <base64 encoded username:password>"}
func (b BasicAuth) GetRequestMetadata(ctx context.Context, in ...string) (map[string]string, error) {
	auth := b.username + ":" + InputHash(b.password)
	enc := base64.StdEncoding.EncodeToString([]byte(auth))
	return map[string]string{
		"authorization": "Basic " + enc,
	}, nil
}

// RequireTransportSecurity always returns true.
func (b BasicAuth) RequireTransportSecurity() bool {
	return true
}

// InputHash obfuscates input to match auth requirements.
//
// Hashing is done automatically when DialInfoParams are used. This is exported
// for callers who cannot use DialInfoParams such as command in `logs.go`
func InputHash(input string) string {
	return fmt.Sprintf("%x", sha256.Sum256([]byte(input)))
}

// DialInfoParams specifies the options for configuring the connection to a cloud/on-prem cluster.
type DialInfoParams struct {
	Address   string // The address of a cloud/on-prem cluster
	Cluster   string // The name of the server to install to
	CredName  string // The name of the credentials to load from auth.Store
	CredAlias string // Optional alias for key to load
	CredOrg   string // Optional the org-id header to set
	CredToken string // Optional the credential value itself. This bypasses the store
}

// insecure returns an insecure dial option when the user has physical access to
// the server, otherwise it returns nil.
func insecureOpts(address string) *[]grpc.DialOption {
	for _, prefix := range []string{"dns:///www.endpoints", "dns:///portal.intrinsic.ai", "dns:///portal-qa.intrinsic.ai"} {
		if strings.HasPrefix(address, prefix) {
			return nil
		}
	}

	return &[]grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
}

// DialInfoCtx returns the metadata for dialing a gRPC connection to a cloud/on-prem cluster.
//
// Function uses provided ctx to manage lifecycle of connection created. Ctx may be
// modified on return, caller is encouraged to switch to returned context if appropriate.
//
// DialInfoParams.Cluster optionally has to be set to the name of the target cluster if
// DialInfoParams.Address is the address of a cloud cluster and the connection will be used to send
// a request to an on-prem service via the relay running in the cloud cluster.
//
// Returns insecure connection data if the address is a local network address (such as
// `localhost:17080`), otherwise retrieves cert from system cert pool, and sets up the metadata for
// a TLS cert with per-RPC basic auth credentials.
// Deprecated: please use DialConnectionCtx
func DialInfoCtx(ctx context.Context, params DialInfoParams) (context.Context, *[]grpc.DialOption, error) {
	ctx, opts, _, err := dialInfoCtxInt(ctx, params)
	return ctx, opts, err
}

// dialInfoCtxInt is DialInfoCtx but allows to default the ServerAddr.
// This is used by DialConnectionCtx and unifies the www.endpoints... handling
func dialInfoCtxInt(ctx context.Context, params DialInfoParams) (context.Context, *[]grpc.DialOption, string, error) {
	if params.Address == "" {
		if params.CredName == "" {
			return ctx, nil, "", fmt.Errorf("not enough information to build target address. Provide --org or --project")
		}

		params.Address = fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", params.CredName)
	}

	// policy for retrying failed gRPC requests as documented here:
	// https://pkg.go.dev/google.golang.org/grpc/examples/features/retry
	// Note that the Ingress will return UNIMPLEMENTED if the server it wants to forward to
	// is unavailable, so we also check for UNIMPLEMENTED.
	var retryPolicy = `{
		"methodConfig": [{
				"waitForReady": true,

				"retryPolicy": {
						"MaxAttempts": 4,
						"InitialBackoff": ".5s",
						"MaxBackoff": ".5s",
						"BackoffMultiplier": 1.5,
						"RetryableStatusCodes": [ "UNAVAILABLE", "RESOURCE_EXHAUSTED", "UNIMPLEMENTED"]
				}
		}]
}`

	baseOpts := []grpc.DialOption{
		grpc.WithDefaultServiceConfig(retryPolicy),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(maxMsgSize),
			grpc.MaxCallSendMsgSize(maxMsgSize),
		),
	}

	if params.CredOrg != "" {
		ctx = metadata.AppendToOutgoingContext(ctx, auth.OrgIDHeader, strings.Split(params.CredOrg, "@")[0])
	}

	if opts := insecureOpts(params.Address); opts != nil {
		finalOpts := append(baseOpts, *opts...)
		return ctx, &finalOpts, params.Address, nil
	}
	pool, err := x509.SystemCertPool()
	if err != nil {
		return nil, nil, "", fmt.Errorf("failed to retrieve system cert pool: %w", err)
	}

	if params.Cluster != "" {
		ctx = metadata.AppendToOutgoingContext(ctx, "x-server-name", params.Cluster)
	}

	rpcCredentials, err := createCredentials(params)
	if err != nil {
		return nil, nil, "", fmt.Errorf("cannot retrieve connection credentials: %w", err)
	}

	finalOpts := append(baseOpts,
		grpc.WithPerRPCCredentials(rpcCredentials),
		grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(pool, "")),
	)

	return ctx, &finalOpts, params.Address, nil
}

func isLocal(address string) bool {
	for _, localAddress := range []string{"127.0.0.1", "local", "xfa.lan"} {
		if strings.Contains(address, localAddress) {
			return true
		}
	}
	return false
}

// ErrCredentialsRequired indicates that the credential name is not set in the
// DialInfoParams for a non-local call.
var ErrCredentialsRequired = errors.New("credential name required")

// ErrCredentialsNotFound indicates that the lookup for a given credential
// name failed.
type ErrCredentialsNotFound struct {
	Err            error // the underlying error
	CredentialName string
}

func (e *ErrCredentialsNotFound) Error() string {
	return fmt.Sprintf("credentials not found: %v", e.Err)
}

func (e *ErrCredentialsNotFound) Unwrap() error { return e.Err }

func createCredentials(params DialInfoParams) (credentials.PerRPCCredentials, error) {
	if params.CredToken != "" {
		return &auth.ProjectToken{APIKey: params.CredToken}, nil
	}

	if params.CredName != "" {
		configuration, err := auth.NewStore().GetConfiguration(params.CredName)
		if err != nil {
			return nil, &ErrCredentialsNotFound{Err: err, CredentialName: params.CredName}
		}

		if params.CredAlias == "" {
			return configuration.GetDefaultCredentials()
		}
		return configuration.GetCredentials(params.CredAlias)
	}

	if isLocal(params.Address) {
		// local calls do not require any authentication
		return nil, nil
	}
	// credential name is required for non-local calls to resolve
	// the corresponding API key.
	return nil, ErrCredentialsRequired
}

// DialConnectionCtx creates and returns a gRPC connection that is created based on the DialInfoParams.
// DialConnectionCtx will fill the ServerAddr or Credname if necessary.
// The CredName is filled from the organization information. It's equal to the project's name.
// The ServerAddr is defaulted to the endpoints url for compute projects.
func DialConnectionCtx(ctx context.Context, params DialInfoParams) (context.Context, *grpc.ClientConn, error) {

	ctx, dialerOpts, addr, err := dialInfoCtxInt(ctx, params)
	if err != nil {
		return nil, nil, fmt.Errorf("dial info: %w", err)
	}

	conn, err := grpc.DialContext(ctx, addr, *dialerOpts...)
	if err != nil {
		return nil, nil, fmt.Errorf("dialing context: %w", err)
	}

	return ctx, conn, nil
}

// DialInfoOauth2 returns the metadata for dialing a gRPC connection to the cloud cluster.
//
// Returns insecure connection data if the address is a local network address (such as
// `localhost:17080`), otherwise retrieves cert from system cert pool, and sets up the metadata for
// a TLS cert with per-RPC oauth2 credentials.
//
// Deprecated: Use DialInfoOauth2Ctx
func DialInfoOauth2(address string) (context.Context, *[]grpc.DialOption, error) {
	return DialInfoOauth2Ctx(context.Background(), address)
}

// DialInfoOauth2Ctx returns the metadata for dialing a gRPC connection to the cloud cluster.
//
// Returns insecure connection data if the address is a local network address (such as
// `localhost:17080`), otherwise retrieves cert from system cert pool, and sets up the metadata for
// a TLS cert with per-RPC oauth2 credentials.
func DialInfoOauth2Ctx(ctx context.Context, address string) (context.Context, *[]grpc.DialOption, error) {

	baseOpts := []grpc.DialOption{
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(maxMsgSize),
			grpc.MaxCallSendMsgSize(maxMsgSize),
		),
	}

	if opts := insecureOpts(address); opts != nil {
		finalOpts := append(baseOpts, *opts...)
		return ctx, &finalOpts, nil
	}
	pool, err := x509.SystemCertPool()
	if err != nil {
		return nil, nil, fmt.Errorf("failed to retrieve system cert pool: %w", err)
	}

	ts, err := oauth2.DefaultTokenSource(ctx)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to retrieve oauth2 token: %w", err)
	}
	creds := oauth.TokenSource{TokenSource: ts}

	finalOpts := append(baseOpts,
		grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(pool, "")),
		grpc.WithPerRPCCredentials(creds),
	)

	return ctx, &finalOpts, nil
}
