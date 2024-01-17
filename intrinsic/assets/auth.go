// Copyright 2023 Intrinsic Innovation LLC

// Package auth provides utils for supporting authentication of skill catalog requests.
package auth

import (
	"context"

	"google.golang.org/grpc/credentials"
	"intrinsic/tools/inctl/auth"
)

const (
	authProjectKey = "x-intrinsic-auth-project"
	authProxyKey   = "auth-proxy"
)

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
