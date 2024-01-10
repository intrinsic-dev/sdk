// Copyright 2023 Intrinsic Innovation LLC

package cluster

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
	"text/tabwriter"

	"github.com/spf13/cobra"

	"intrinsic/frontend/cloud/updatemanager/info"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/util/orgutil"
)

var (
	clusterName string
)

// Client helps run auth'ed requests for a specific cluster
type Client struct {
	client      *http.Client
	url         url.URL
	tokenSource *auth.ProjectToken
	cluster     string
}

// Do wraps http.Client.Do with Auth
func (c *Client) Do(req *http.Request) (*http.Response, error) {
	req, err := c.tokenSource.HTTPAuthorization(req)
	if err != nil {
		return nil, fmt.Errorf("auth token for %q %s: %w", req.Method, req.URL.String(), err)
	}
	return c.client.Do(req)
}

// Req returns an http request for subpath
//
// Note: empty subpath just queries the root path
func (c *Client) Req(ctx context.Context, method, subpath string) (*http.Request, error) {
	url := c.url
	url.Path = filepath.Join(url.Path, subpath)
	req, err := http.NewRequestWithContext(ctx, method, url.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("create %q request for %s: %w", method, url.String(), err)
	}
	return req, nil
}

// Status queries the update status of a cluster
func (c *Client) Status(ctx context.Context) ([]byte, error) {
	req, err := c.Req(ctx, http.MethodGet, "/state")
	if err != nil {
		return nil, err
	}
	resp, err := c.Do(req)
	if err != nil {
		return nil, fmt.Errorf("%q request for %s: %w", req.Method, req.URL.String(), err)
	}
	// read body first as error response might also be in the body
	rb, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("response %q request for %s: %w", req.Method, req.URL.String(), err)
	}
	switch resp.StatusCode {
	case http.StatusOK:
	default:
		return nil, fmt.Errorf("HTTP %d %q request for %s: %s", resp.StatusCode, req.Method, req.URL.String(), rb)
	}
	return rb, nil
}

func forCluster(project, cluster string) (Client, error) {
	configuration, err := auth.NewStore().GetConfiguration(project)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return Client{}, &dialerutil.ErrCredentialsNotFound{
				CredentialName: project,
				Err:            err,
			}
		}
		return Client{}, fmt.Errorf("get configuration for project %q: %w", project, err)
	}

	token, err := configuration.GetDefaultCredentials()
	if err != nil {
		return Client{}, fmt.Errorf("get default credentials for project %q: %w", project, err)
	}

	// cluster is a query parameter for clusterupdate
	v := url.Values{}
	v.Set("cluster", cluster)

	return Client{
		client: http.DefaultClient,
		url: url.URL{
			Scheme:   "https",
			Host:     fmt.Sprintf("www.endpoints.%s.cloud.goog", project),
			Path:     "/api/clusterupdate/",
			RawQuery: v.Encode(),
		},
		tokenSource: token,
	}, nil
}

var clusterUpgradeCmd = &cobra.Command{
	Use:   "upgrade",
	Short: "Upgrade",
	Long:  "Upgrade Intrinsic software on target cluster.",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		ctx := context.Background()

		projectName := ClusterCmdViper.GetString(orgutil.KeyProject)
		c, err := forCluster(projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client: %v", err)
		}
		o, err := c.Status(ctx)
		if err != nil {
			return fmt.Errorf("cluster status: %v", err)
		}
		ui := info.Info{}
		if err := json.Unmarshal(o, &ui); err != nil {
			return fmt.Errorf("unmarshal json response for status: %v", err)
		}
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
		fmt.Fprintf(w, "project\tcluster\tstate\tflowstate\tos\tflowstate.next\tos.next\n")
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", projectName, clusterName, ui.State, "", ui.CurrentOS, "", ui.TargetOS)
		w.Flush()
		return nil
	},
}

func init() {
	ClusterCmd.AddCommand(clusterUpgradeCmd)
	clusterUpgradeCmd.PersistentFlags().StringVar(&clusterName, "cluster", "", "Name of cluster to update.")
	clusterUpgradeCmd.MarkPersistentFlagRequired("cluster")
}
