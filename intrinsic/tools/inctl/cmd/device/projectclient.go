// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package projectclient provides a http client wrapper that authenticates requests via apikeys.
package projectclient

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"path/filepath"
	"strings"

	"intrinsic/tools/inctl/auth/auth"
)

var (
	// ErrNotFound will be returned on 404, since it's an error that's expected
	// and can be printed with better UX than just the number.
	ErrNotFound = fmt.Errorf("Not found")
)

// AuthedClient injects an api key for the project into every request.
type AuthedClient struct {
	client       *http.Client
	baseURL      url.URL
	tokenSource  *auth.ProjectToken
	organization string
}

// Do is the primary function of the http client interface.
func (c *AuthedClient) Do(req *http.Request) (*http.Response, error) {
	req, err := c.tokenSource.HTTPAuthorization(req)
	if c.organization != "" {
		req.AddCookie(&http.Cookie{Name: "org-id", Value: c.organization})
	}

	if err != nil {
		return nil, err
	}

	return c.client.Do(req)
}

// Client returns a http.Client compatible that injects auth for the project into every request.
func Client(projectName string, orgName string) (AuthedClient, error) {
	if projectName == "" {
		info, err := auth.NewStore().ReadOrgInfo(orgName)
		if err != nil {
			return AuthedClient{}, fmt.Errorf("get org info: %w", err)
		}

		projectName = info.Project
		orgName = strings.Split(orgName, "@")[0]
	}

	configuration, err := auth.NewStore().GetConfiguration(projectName)
	if err != nil {
		return AuthedClient{}, fmt.Errorf("get credential store: %w", err)
	}

	token, err := configuration.GetDefaultCredentials()
	if err != nil {
		return AuthedClient{}, fmt.Errorf("get default credential: %w", err)
	}

	return AuthedClient{
		client: http.DefaultClient,
		baseURL: url.URL{
			Scheme: "https",
			Host:   fmt.Sprintf("www.endpoints.%s.cloud.goog", projectName),
			Path:   "/api/devices/",
		},
		tokenSource:  token,
		organization: orgName,
	}, nil
}

// PostDevice acts similar to [http.Post] but takes a context and injects base path of the device manager for the project.
func (c *AuthedClient) PostDevice(ctx context.Context, cluster, deviceID, subPath string, body io.Reader) (*http.Response, error) {
	reqURL := c.baseURL

	reqURL.Path = filepath.Join(reqURL.Path, subPath)
	reqURL.RawQuery = url.Values{"device-id": []string{deviceID}, "cluster": []string{cluster}}.Encode()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, reqURL.String(), body)
	if err != nil {
		return nil, err
	}

	return c.Do(req)
}

// GetDevice acts similar to [http.Get] but takes a context and injects base path of the device manager for the project.
func (c *AuthedClient) GetDevice(ctx context.Context, cluster, deviceID, subPath string) (*http.Response, error) {
	reqURL := c.baseURL

	reqURL.Path = filepath.Join(reqURL.Path, subPath)
	reqURL.RawQuery = url.Values{"device-id": []string{deviceID}, "cluster": []string{cluster}}.Encode()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, reqURL.String(), nil)
	if err != nil {
		return nil, err
	}

	return c.Do(req)
}

// GetDevice acts similar to [GetDevice] but also does [json.Decode] and enforces [http.StatusOK].
func (c *AuthedClient) GetJSON(ctx context.Context, cluster, deviceID, subPath string, value any) error {
	resp, err := c.GetDevice(ctx, cluster, deviceID, subPath)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		if resp.StatusCode == http.StatusNotFound {
			return ErrNotFound
		}

		return fmt.Errorf("get status code: %v", resp.StatusCode)
	}

	return json.NewDecoder(resp.Body).Decode(value)
}
