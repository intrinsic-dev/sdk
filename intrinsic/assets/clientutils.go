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
	authProjectKey = "x-intrinsic-auth-project"
	authProxyKey   = "auth-proxy"
	maxMsgSize     = math.MaxInt64
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

// DialCatalogOptions specifies the options DialCatalog.
type DialCatalogOptions struct {
	Address         string
	Organization    string
	Project         string
	UseFirebaseAuth bool
	UserReader      *bufio.Reader // Required if UseFirebaseAuth is true.
	UserWriter      io.Writer     // Required if UseFirebaseAuth is true.
}

// DialSkillCatalogFromInctl creates a connection to a skill catalog service from an inctl command.
func DialSkillCatalogFromInctl(cmd *cobra.Command, flags *cmdutils.CmdFlags) (*grpc.ClientConn, error) {
	return DialSkillCatalog(
		cmd.Context(), DialCatalogOptions{
			Address:         "",
			Organization:    flags.GetFlagOrganization(),
			Project:         flags.GetFlagProject(),
			UseFirebaseAuth: false,
			UserReader:      bufio.NewReader(cmd.InOrStdin()),
			UserWriter:      cmd.OutOrStdout(),
		},
	)
}

// DialSkillCatalog creates a connection to a skill catalog service.
func DialSkillCatalog(ctx context.Context, opts DialCatalogOptions) (*grpc.ClientConn, error) {
	options := BaseDialOptions

	address, err := resolveSkillCatalogAddress(opts.Address, opts.Project)
	if err != nil {
		return nil, fmt.Errorf("cannot resolve address: %w", err)
	}

	// Determine credentials to include in requests.
	if opts.UseFirebaseAuth {
		return nil, fmt.Errorf("firebase auth unimplemented")
	} else if IsLocalAddress(opts.Address) {
		options = append(options, grpc.WithTransportCredentials(insecure.NewCredentials()))
	} else {
		rpcCreds, err := GetAPIKeyPerRPCCredentials(opts.Project, opts.Organization)
		if err != nil {
			return nil, fmt.Errorf("cannot get api key per rpc credentials: %w", err)
		}
		tcOption, err := GetTransportCredentialsDialOption()
		if err != nil {
			return nil, fmt.Errorf("cannot get transport credentials: %w", err)
		}
		options = append(options, grpc.WithPerRPCCredentials(rpcCreds), tcOption)
	}

	conn, err := grpc.DialContext(ctx, address, options...)
	if err != nil {
		return nil, fmt.Errorf("dialing context: %w", err)
	}

	return conn, nil
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

func resolveSkillCatalogAddress(address string, project string) (string, error) {
	// Check for user-provided address.
	if address != "" {
		return address, nil
	}

	// Derive address from project.
	if project == "" {
		return "", fmt.Errorf("project is required if no address is specified")
	}
	return fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", project), nil
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

// GetAPIKeyPerRPCCredentials returns api-key PerRPCCredentials.
func GetAPIKeyPerRPCCredentials(project string, organization string) (credentials.PerRPCCredentials, error) {
	configuration, err := auth.NewStore().GetConfiguration(project)
	if err != nil {
		return nil, err
	}

	creds, err := configuration.GetDefaultCredentials()
	if err != nil {
		return nil, err
	}

	if organization != "" {
		return &CustomOrganizationCredentials{
			c:            creds,
			organization: organization,
		}, nil
	}

	return creds, nil
}
