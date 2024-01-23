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
	"strings"

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
)

// DialCatalogOptions specifies the options for DialSkillCatalog.
type DialCatalogOptions struct {
	Address          string
	APIKey           string
	Organization     string
	Project          string
	UseFirebaseCreds bool
	UserReader       *bufio.Reader // Required if UseFirebaseAuth is true.
	UserWriter       io.Writer     // Required if UseFirebaseAuth is true.
}

// DialSkillCatalogFromInctl creates a connection to a skill catalog service from an inctl command.
func DialSkillCatalogFromInctl(cmd *cobra.Command, flags *cmdutils.CmdFlags) (*grpc.ClientConn, error) {

	return DialSkillCatalog(
		cmd.Context(), DialCatalogOptions{
			Address:          "",
			APIKey:           "",
			Organization:     flags.GetFlagOrganization(),
			Project:          flags.GetFlagProject(),
			UseFirebaseCreds: false,
			UserReader:       bufio.NewReader(cmd.InOrStdin()),
			UserWriter:       cmd.OutOrStdout(),
		},
	)
}

// DialSkillCatalog creates a connection to a skill catalog service.
func DialSkillCatalog(ctx context.Context, opts DialCatalogOptions) (*grpc.ClientConn, error) {
	// Get the catalog address.
	addDNS := true
	address, err := resolveSkillCatalogAddress(opts.Address, opts.Project, addDNS)
	if err != nil {
		return nil, fmt.Errorf("cannot resolve address: %w", err)
	}

	options := BaseDialOptions

	// Determine credentials to include in requests.
	if opts.UseFirebaseCreds { // Use firebase creds.
		return nil, fmt.Errorf("firebase auth unimplemented")
	} else if IsLocalAddress(opts.Address) { // Use insecure creds.
		options = append(options, grpc.WithTransportCredentials(insecure.NewCredentials()))
	} else { // Use api-key creds.
		rpcCreds, err := getAPIKeyPerRPCCredentials(opts.APIKey, opts.Project, opts.Organization)
		if err != nil {
			return nil, fmt.Errorf("cannot get api-key credentials: %w", err)
		}
		tcOption, err := GetTransportCredentialsDialOption()
		if err != nil {
			return nil, fmt.Errorf("cannot get transport credentials: %w", err)
		}
		options = append(options, grpc.WithPerRPCCredentials(rpcCreds), tcOption)
	}

	return grpc.DialContext(ctx, address, options...)
}

// GetTransportCredentialsDialOption returns transport credentials from the system certificate pool.
func GetTransportCredentialsDialOption() (grpc.DialOption, error) {
	pool, err := x509.SystemCertPool()
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve system cert pool: %w", err)
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

func resolveSkillCatalogAddress(address string, project string, addDNS bool) (string, error) {
	// Check for user-provided address.
	if address != "" {
		return address, nil
	}

	// Derive address from project.
	if address == "" {
		if project == "" {
			return "", fmt.Errorf("project is required if no address is specified")
		}
		address = fmt.Sprintf("www.endpoints.%s.cloud.goog:443", project)
	}

	if addDNS && !strings.HasPrefix(address, "dns:///") {
		address = fmt.Sprintf("dns:///%s", address)
	}

	return address, nil
}

// CustomOrganizationCredentials adds a custom organization to credentials provided by a base
// PerRPCCredentials.
type CustomOrganizationCredentials struct {
	c            credentials.PerRPCCredentials
	organization string
}

func (c *CustomOrganizationCredentials) GetRequestMetadata(ctx context.Context, uri ...string) (map[string]string, error) {
	md, err := c.c.GetRequestMetadata(ctx, uri...)
	if err != nil {
		return nil, err
	}
	md[auth.OrgIDHeader] = c.organization

	return md, nil
}

// RequireTransportSecurity always returns true to protect credentials
func (c *CustomOrganizationCredentials) RequireTransportSecurity() bool {
	return true
}

// getAPIKeyPerRPCCredentials returns api-key PerRPCCredentials.
func getAPIKeyPerRPCCredentials(apiKey string, project string, organization string) (credentials.PerRPCCredentials, error) {
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

	if organization != "" {
		return &CustomOrganizationCredentials{
			c:            token,
			organization: organization,
		}, nil
	}

	return token, nil
}
