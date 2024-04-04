// Copyright 2023 Intrinsic Innovation LLC

// Package clientutils provides utils for supporting catalog clients and authentication.
package clientutils

import (
	"bufio"
	"context"
	"crypto/x509"
	"fmt"
	"io"
	"math"
	"regexp"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	"intrinsic/assets/cmdutils"
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
	// BaseDialOptions are the base dial options for catalog clients.
	BaseDialOptions = []grpc.DialOption{
		grpc.WithDefaultServiceConfig(retryPolicy),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(maxMsgSize),
			grpc.MaxCallSendMsgSize(maxMsgSize),
		),
	}

	catalogEndpointAddressRegex = regexp.MustCompile(`(^|/)www\.endpoints\.([^\.]+).cloud.goog`)
	catalogAssetAddressRegex    = regexp.MustCompile(`(^|/)assets[-]?([^\.]*)\.intrinsic\.ai`)
)

// DialCatalogOptions specifies the options for DialCatalog.
type DialCatalogOptions struct {
	Address    string
	APIKey     string
	Project    string
	UserReader *bufio.Reader // Required if UseFirebaseAuth is true.
	UserWriter io.Writer     // Required if UseFirebaseAuth is true.
}

// DialCatalogFromInctl creates a connection to an asset catalog service from an inctl command.
func DialCatalogFromInctl(cmd *cobra.Command, flags *cmdutils.CmdFlags) (*grpc.ClientConn, error) {

	return DialCatalog(
		cmd.Context(), DialCatalogOptions{
			Address:    "",
			APIKey:     "",
			Project:    ResolveProject(cmd.Context(), flags),
			UserReader: bufio.NewReader(cmd.InOrStdin()),
			UserWriter: cmd.OutOrStdout(),
		},
	)
}

// DialCatalog creates a connection to a asset catalog service.
func DialCatalog(ctx context.Context, opts DialCatalogOptions) (*grpc.ClientConn, error) {
	// Get the catalog address.
	address, err := resolveCatalogAddress(ctx, opts)
	if err != nil {
		return nil, errors.Wrap(err, "cannot resolve address")
	}

	options := BaseDialOptions
	if IsLocalAddress(opts.Address) { // Use insecure creds.
		options = append(options, grpc.WithTransportCredentials(insecure.NewCredentials()))
	} else { // Use api-key creds.
		rpcCreds, err := getAPIKeyPerRPCCredentials(opts.APIKey, opts.Project)
		if err != nil {
			return nil, errors.Wrap(err, "cannot get api-key credentials")
		}
		tcOption, err := GetTransportCredentialsDialOption()
		if err != nil {
			return nil, errors.Wrap(err, "cannot get transport credentials")
		}
		options = append(options, grpc.WithPerRPCCredentials(rpcCreds), tcOption)
	}

	return grpc.DialContext(ctx, address, options...)
}

// ResolveProject returns the project to use for communicating with a catalog.
func ResolveProject(ctx context.Context, flags *cmdutils.CmdFlags) string {
	project := "intrinsic-assets-prod"

	return project
}

// GetTransportCredentialsDialOption returns transport credentials from the system certificate pool.
func GetTransportCredentialsDialOption() (grpc.DialOption, error) {
	pool, err := x509.SystemCertPool()
	if err != nil {
		return nil, errors.Wrap(err, "failed to retrieve system cert pool")
	}

	return grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(pool, "")), nil
}

// IsLocalAddress returns true if the address is a local address.
func IsLocalAddress(address string) bool {
	for _, localAddress := range []string{"127.0.0.1", "local", "xfa.lan"} {
		if strings.Contains(address, localAddress) {
			return true
		}
	}
	return false
}

func resolveCatalogAddress(ctx context.Context, opts DialCatalogOptions) (string, error) {
	// Check for user-provided address.
	if opts.Address != "" {
		return opts.Address, nil
	}

	// Derive the address from the project.
	if opts.Project == "" {
		return "", fmt.Errorf("project is empty")
	}
	address, err := getCatalogAddressForProject(ctx, opts)
	if err != nil {
		return "", err
	}

	addDNS := true
	if addDNS && !strings.HasPrefix(address, "dns:///") {
		address = fmt.Sprintf("dns:///%s", address)
	}

	return address, nil
}

func defaultGetCatalogAddressForProject(ctx context.Context, opts DialCatalogOptions) (address string, err error) {
	if opts.Project != "intrinsic-assets-prod" {
		return "", fmt.Errorf("unsupported project %s", opts.Project)
	}
	address = fmt.Sprintf("assets.intrinsic.ai:443")

	return address, nil
}

var (
	getCatalogAddressForProject = defaultGetCatalogAddressForProject
)

// getAPIKeyPerRPCCredentials returns api-key PerRPCCredentials.
func getAPIKeyPerRPCCredentials(apiKey string, project string) (credentials.PerRPCCredentials, error) {
	var token *auth.ProjectToken

	if apiKey != "" {
		// User-provided api-key.
		token = &auth.ProjectToken{APIKey: apiKey}
	} else {
		// Load api-key from the auth store.
		configuration, err := auth.NewStore().GetConfiguration(project)
		if err != nil {
			return nil, err
		}

		token, err = configuration.GetDefaultCredentials()
		if err != nil {
			return nil, err
		}
	}

	return token, nil
}
