// Copyright 2023 Intrinsic Innovation LLC

// Package projectclient provides a http client wrapper that authenticates requests via apikeys.
package projectclient

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"

	clustermanagergrpcpb "intrinsic/frontend/cloud/api/clustermanager_api_go_grpc_proto"

	"google.golang.org/grpc"
	"intrinsic/frontend/cloud/devicemanager/shared"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/auth"
)

var (
	// These will be returned on corresponding http error codes, since they are errors that are
	// expected and can be printed with better UX than just the number.
	ErrNotFound     = fmt.Errorf("Not found")
	ErrBadGateway   = fmt.Errorf("Bad Gateway")
	ErrUnauthorized = fmt.Errorf("Unauthorized")
)

// AuthedClient injects an api key for the project into every request.
type AuthedClient struct {
	client       *http.Client
	baseURL      url.URL
	tokenSource  *auth.ProjectToken
	projectName  string
	organization string
	grpcConn     *grpc.ClientConn
	grpcClient   clustermanagergrpcpb.ClustersServiceClient
}

// Do is the primary function of the http client interface.
func (c *AuthedClient) Do(req *http.Request) (*http.Response, error) {
	req, err := c.tokenSource.HTTPAuthorization(req)
	if c.organization != "" {
		req.AddCookie(&http.Cookie{Name: auth.OrgIDHeader, Value: c.organization})
	}

	if err != nil {
		return nil, err
	}

	return c.client.Do(req)
}

// Client returns a http.Client compatible that injects auth for the project into every request.
func Client(ctx context.Context, projectName string, orgName string, clusterName string) (context.Context, AuthedClient, error) {
	configuration, err := auth.NewStore().GetConfiguration(projectName)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, AuthedClient{}, &dialerutil.ErrCredentialsNotFound{
				CredentialName: projectName,
				Err:            err,
			}
		}
		return nil, AuthedClient{}, fmt.Errorf("get configuration: %w", err)
	}

	token, err := configuration.GetDefaultCredentials()
	if err != nil {
		return nil, AuthedClient{}, fmt.Errorf("get default credential: %w", err)
	}

	params := dialerutil.DialInfoParams{
		Cluster:  clusterName,
		CredName: projectName,
		CredOrg:  orgName,
	}
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, params)
	if err != nil {
		return nil, AuthedClient{}, fmt.Errorf("create grpc client: %w", err)
	}

	return ctx, AuthedClient{
		client: http.DefaultClient,
		baseURL: url.URL{
			Scheme: "https",
			Host:   fmt.Sprintf("www.endpoints.%s.cloud.goog", projectName),
			Path:   "/api/devices/",
		},
		tokenSource:  token,
		projectName:  projectName,
		organization: orgName,
		grpcConn:     conn,
		grpcClient:   clustermanagergrpcpb.NewClustersServiceClient(conn),
	}, nil
}

// Close closes the grpc connection if it exists.
func (c *AuthedClient) Close() error {
	if c.grpcConn != nil {
		return c.grpcConn.Close()
	}
	return nil
}

func (c *AuthedClient) GetStatusNetwork(ctx context.Context, clusterName, deviceID string) (map[string]shared.StatusInterface, error) {
	req := &clustermanagergrpcpb.GetStatusRequest{
		Project:   c.projectName,
		Org:       c.organization,
		ClusterId: clusterName,
		DeviceId:  deviceID,
	}
	resp, err := c.grpcClient.GetStatus(ctx, req)
	if err != nil {
		return nil, err
	}
	statusNetwork := map[string]shared.StatusInterface{}
	for in, ifa := range resp.GetInterfaces() {
		statusNetwork[in] = shared.StatusInterface{
			IPAddress: ifa.GetAddresses(),
		}
	}
	return statusNetwork, nil
}

func translateNetworkConfig(n *clustermanagergrpcpb.IntOSNetworkConfig) map[string]shared.Interface {
	configMap := map[string]shared.Interface{}
	for name, inf := range n.GetInterfaces() {
		ns := inf.GetNameservers()
		configMap[name] = shared.Interface{
			DHCP4:    inf.GetDhcp4(),
			Gateway4: inf.GetGateway4(),
			DHCP6:    &inf.Dhcp6,
			Gateway6: inf.GetGateway6(),
			MTU:      int64(inf.GetMtu()),
			Nameservers: shared.Nameservers{
				Search:    ns.GetSearch(),
				Addresses: ns.GetAddresses(),
			},
			Addresses: inf.GetAddresses(),
			Realtime:  inf.GetRealtime(),
			EtherType: int64(inf.GetEtherType()),
		}
	}
	return configMap
}

func (c *AuthedClient) GetNetworkConfig(ctx context.Context, clusterName, deviceID string) (map[string]shared.Interface, error) {
	req := &clustermanagergrpcpb.GetNetworkConfigRequest{
		Project: c.projectName,
		Org:     c.organization,
		Cluster: clusterName,
		Device:  deviceID,
	}
	resp, err := c.grpcClient.GetNetworkConfig(ctx, req)
	if err != nil {
		return nil, err
	}
	return translateNetworkConfig(resp), nil
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

// GetJSON acts similar to [GetDevice] but also does [json.Decode] and enforces [http.StatusOK].
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
		if resp.StatusCode == http.StatusBadGateway {
			return ErrBadGateway
		}
		if resp.StatusCode == http.StatusUnauthorized {
			return ErrUnauthorized
		}

		return fmt.Errorf("get status code: %v", resp.StatusCode)
	}

	return json.NewDecoder(resp.Body).Decode(value)
}
