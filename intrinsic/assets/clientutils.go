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

// DialCatalogOptions specifies the options for DialSkillCatalog and DialCatalog.
type DialCatalogOptions struct {
	Address      string
	APIKey       string
	Organization string
	Project      string
	UserReader   *bufio.Reader // Required if UseFirebaseAuth is true.
	UserWriter   io.Writer     // Required if UseFirebaseAuth is true.
}

// DialCatalogFromInctl creates a connection to an asset catalog service from an inctl command.
func DialCatalogFromInctl(cmd *cobra.Command, flags *cmdutils.CmdFlags) (*grpc.ClientConn, error) {

	return DialCatalog(
		cmd.Context(), DialCatalogOptions{
			Address:      "",
			APIKey:       "",
			Organization: "",
			Project:      ResolveProject(cmd.Context(), flags),
			UserReader:   bufio.NewReader(cmd.InOrStdin()),
			UserWriter:   cmd.OutOrStdout(),
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
		rpcCreds, err := getAPIKeyPerRPCCredentials(opts.APIKey, opts.Project, opts.Organization)
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

// DialSkillCatalogFromInctl creates a connection to a skill catalog service from an inctl command.
func DialSkillCatalogFromInctl(cmd *cobra.Command, flags *cmdutils.CmdFlags) (*grpc.ClientConn, error) {

	return DialSkillCatalog(
		cmd.Context(), DialCatalogOptions{
			Address:      "",
			APIKey:       "",
			Organization: flags.GetFlagOrganization(),
			Project:      flags.GetFlagProject(),
			UserReader:   bufio.NewReader(cmd.InOrStdin()),
			UserWriter:   cmd.OutOrStdout(),
		},
	)
}

// DialSkillCatalog creates a connection to a skill catalog service.
func DialSkillCatalog(ctx context.Context, opts DialCatalogOptions) (*grpc.ClientConn, error) {
	// Get the catalog address.
	address, err := resolveSkillCatalogAddress(ctx, opts)
	if err != nil {
		return nil, errors.Wrap(err, "cannot resolve address")
	}

	options := BaseDialOptions

	// Determine credentials to include in requests.
	if IsLocalAddress(opts.Address) { // Use insecure creds.
		options = append(options, grpc.WithTransportCredentials(insecure.NewCredentials()))
	} else { // Use api-key creds.
		rpcCreds, err := getAPIKeyPerRPCCredentials(opts.APIKey, opts.Project, opts.Organization)
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

// GetSkillCatalogProject returns the SkillCatalog project that the specified project uses.
func GetSkillCatalogProject(project string) (string, error) {
	address, err := getCustomSkillCatalogAddressForProject(project)
	if err != nil {
		return "", err
	}

	// No custom address, so the project is running its own catalog.
	if address == "" {
		return project, nil
	}

	// Try to derive the project from an endpoint-style catalog address.
	submatches := catalogEndpointAddressRegex.FindStringSubmatch(address)
	if submatches != nil {
		return submatches[2], nil
	}

	// Try to derive the project from an asset-style catalog address.
	submatches = catalogAssetAddressRegex.FindStringSubmatch(address)
	if submatches != nil {
		addressSuffix := submatches[2]
		projectSuffix := "prod"
		if len(addressSuffix) > 0 {
			projectSuffix = addressSuffix
		}
		return fmt.Sprintf("intrinsic-assets-%s", projectSuffix), nil
	}

	return "", fmt.Errorf("cannot infer project from address: %s", address)
}

// ResolveProject returns the project to use for communicating with a catalog.
func ResolveProject(ctx context.Context, flags *cmdutils.CmdFlags) string {
	project := "intrinsic-assets-prod"

	return project
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

func resolveSkillCatalogAddress(ctx context.Context, opts DialCatalogOptions) (string, error) {
	// Check for user-provided address.
	if opts.Address != "" {
		return opts.Address, nil
	}

	// Derive the address from the project.
	if opts.Project == "" {
		return "", fmt.Errorf("project is empty")
	}
	address, err := getSkillCatalogAddressForProject(ctx, opts)
	if err != nil {
		return "", err
	}

	addDNS := true
	if addDNS && !strings.HasPrefix(address, "dns:///") {
		address = fmt.Sprintf("dns:///%s", address)
	}

	return address, nil
}

func defaultGetSkillCatalogAddressForProject(ctx context.Context, opts DialCatalogOptions) (string, error) {
	// Check for a custom address for this project.
	if address, err := getCustomSkillCatalogAddressForProject(opts.Project); err != nil {
		return "", err
	} else if address != "" {
		return address, nil
	}

	// Otherwise derive address from project.
	address := fmt.Sprintf("www.endpoints.%s.cloud.goog:443", opts.Project)

	return address, nil
}

func defaultGetCatalogAddressForProject(ctx context.Context, opts DialCatalogOptions) (string, error) {
	// Check for a custom address for this project.
	if address, err := getCustomCatalogAddressForProject(opts.Project); err != nil {
		return "", err
	} else if address != "" {
		return address, nil
	}

	// Otherwise use address of global catalog
	address := fmt.Sprintf("assets.intrinsic.ai:443")

	return address, nil
}

func defaultGetCustomCatalogAddressForProject(project string) (string, error) {
	address := ""

	return address, nil
}

func defaultGetCustomSkillCatalogAddressForProject(project string) (string, error) {
	address := ""

	return address, nil
}

// CustomOrganizationCredentials adds a custom organization to credentials provided by a base
// PerRPCCredentials.
type CustomOrganizationCredentials struct {
	c            credentials.PerRPCCredentials
	organization string
}

// GetRequestMetadata returns a map of request metadata.
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

// Overridable for testing.
var (
	getCatalogAddressForProject            = defaultGetCatalogAddressForProject
	getCustomCatalogAddressForProject      = defaultGetCustomCatalogAddressForProject
	getSkillCatalogAddressForProject       = defaultGetSkillCatalogAddressForProject
	getCustomSkillCatalogAddressForProject = defaultGetCustomSkillCatalogAddressForProject
)
