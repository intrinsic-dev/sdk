// Copyright 2023 Intrinsic Innovation LLC

// Package dialerutil has helpers for specifying grpc dialer information for the installer service.
package dialerutil

import (
	"bufio"
	"context"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"math"
	"strings"

	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	assetsauth "intrinsic/assets/auth"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
	"intrinsic/tools/inctl/auth"
)

const (
	maxMsgSize = math.MaxInt64
	// policy for retrying failed gRPC requests as documented here:
	// https://pkg.go.dev/google.golang.org/grpc/examples/features/retry
	// Note that the Ingress will return UNIMPLEMENTED if the server it wants to forward to
	// is unavailable, so we also check for UNIMPLEMENTED.
	retryPolicy = `{
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
)

var (
	baseDialOptions = []grpc.DialOption{
		grpc.WithDefaultServiceConfig(retryPolicy),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(maxMsgSize),
			grpc.MaxCallSendMsgSize(maxMsgSize),
		),
	}
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

// DialCatalogContextOptions specifies the options DialCatalogContext.
type DialCatalogContextOptions struct {
	Address         string
	Organization    string
	Project         string
	UseFirebaseAuth bool
	UserReader      *bufio.Reader // Required if UseFirebaseAuth is true.
	UserWriter      io.Writer     // Required if UseFirebaseAuth is true.
}

// DialCatalogContextFromInctl creates a connection to a catalog service from an inctl command.
func DialCatalogContextFromInctl(cmd *cobra.Command, flags *cmdutil.CmdFlags) (*grpc.ClientConn, error) {
	return DialCatalogContext(
		cmd.Context(), DialCatalogContextOptions{
			Address:         "",
			Organization:    flags.GetFlagOrganization(),
			Project:         flags.GetFlagProject(),
			UseFirebaseAuth: false,
			UserReader:      bufio.NewReader(cmd.InOrStdin()),
			UserWriter:      cmd.OutOrStdout(),
		},
	)
}

// DialCatalogContext creates a connection to a catalog service.
func DialCatalogContext(ctx context.Context, opts DialCatalogContextOptions) (*grpc.ClientConn, error) {
	options := baseDialOptions

	// Determine credentials to include in requests.
	if opts.UseFirebaseAuth {
		return nil, fmt.Errorf("firebase auth unimplemented")
	} else if isLocal(opts.Address) {
		options = append(options, grpc.WithTransportCredentials(insecure.NewCredentials()))
	} else {
		rpcCreds, err := assetsauth.GetAPIKeyPerRPCCredentials(opts.Project, opts.Organization)
		if err != nil {
			return nil, fmt.Errorf("cannot get api key per rpc credentials: %w", err)
		}
		tcOption, err := getTransportCredentialsDialOption()
		if err != nil {
			return nil, fmt.Errorf("cannot get transport credentials: %w", err)
		}
		options = append(options, grpc.WithPerRPCCredentials(rpcCreds), tcOption)
	}

	address, err := resolveAddress(opts.Address, opts.Project)
	if err != nil {
		return nil, fmt.Errorf("cannot resolve address: %w", err)
	}

	conn, err := grpc.DialContext(ctx, address, options...)
	if err != nil {
		return nil, fmt.Errorf("dialing context: %w", err)
	}

	return conn, nil
}

// DialConnectionCtx creates and returns a gRPC connection that is created based on the DialInfoParams.
// DialConnectionCtx will fill the ServerAddr or Credname if necessary.
// The CredName is filled from the organization information. It's equal to the project's name.
// The ServerAddr is defaulted to the endpoints url for compute projects.
func DialConnectionCtx(ctx context.Context, params DialInfoParams) (context.Context, *grpc.ClientConn, error) {

	ctx, dialerOpts, addr, err := dialInfoCtx(ctx, params)
	if err != nil {
		return nil, nil, fmt.Errorf("dial info: %w", err)
	}

	conn, err := grpc.DialContext(ctx, addr, *dialerOpts...)
	if err != nil {
		return nil, nil, fmt.Errorf("dialing context: %w", err)
	}

	return ctx, conn, nil
}

// dialInfoCtx returns the metadata for dialing a gRPC connection to a cloud/on-prem cluster.
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
func dialInfoCtx(ctx context.Context, params DialInfoParams) (context.Context, *[]grpc.DialOption, string, error) {
	address, err := resolveAddress(params.Address, params.CredName)
	if err != nil {
		return ctx, nil, "", err
	}
	params.Address = address

	if params.CredOrg != "" {
		ctx = metadata.AppendToOutgoingContext(ctx, auth.OrgIDHeader, strings.Split(params.CredOrg, "@")[0])
	}

	if opts := insecureOpts(params.Address); opts != nil {
		finalOpts := append(baseDialOptions, *opts...)
		return ctx, &finalOpts, params.Address, nil
	}

	if params.Cluster != "" {
		ctx = metadata.AppendToOutgoingContext(ctx, "x-server-name", params.Cluster)
	}

	rpcCredentials, err := createCredentials(params)
	if err != nil {
		return nil, nil, "", fmt.Errorf("cannot retrieve connection credentials: %w", err)
	}
	tcOption, err := getTransportCredentialsDialOption()
	if err != nil {
		return nil, nil, "", fmt.Errorf("cannot retrieve transport credentials: %w", err)
	}

	finalOpts := append(baseDialOptions,
		grpc.WithPerRPCCredentials(rpcCredentials),
		tcOption,
	)

	return ctx, &finalOpts, params.Address, nil
}

func getTransportCredentialsDialOption() (grpc.DialOption, error) {
	pool, err := x509.SystemCertPool()
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve system cert pool: %w", err)
	}

	return grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(pool, "")), nil
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

func isLocal(address string) bool {
	for _, localAddress := range []string{"127.0.0.1", "local", "xfa.lan"} {
		if strings.Contains(address, localAddress) {
			return true
		}
	}
	return false
}

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

func resolveAddress(address string, project string) (string, error) {
	if address != "" {
		return address, nil
	}

	if project == "" {
		return "", fmt.Errorf("project is required if no address is specified")
	}

	return fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", project), nil
}
