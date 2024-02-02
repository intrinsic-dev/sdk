// Copyright 2023 Intrinsic Innovation LLC

package cluster

import (
	"bytes"
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
	"intrinsic/frontend/cloud/updatemanager/messages"
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
func (c *Client) Req(ctx context.Context, method, subpath string, body io.Reader) (*http.Request, error) {
	url := c.url
	url.Path = filepath.Join(url.Path, subpath)
	req, err := http.NewRequestWithContext(ctx, method, url.String(), body)
	if err != nil {
		return nil, fmt.Errorf("create %q request for %s: %w", method, url.String(), err)
	}
	return req, nil
}

// runReq runs a |method| request with path and returns the response/error
func (c *Client) runReq(ctx context.Context, method, subpath string, body io.Reader) ([]byte, error) {
	req, err := c.Req(ctx, method, subpath, body)
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

// Status queries the update status of a cluster
func (c *Client) Status(ctx context.Context) (*info.Info, error) {
	b, err := c.runReq(ctx, http.MethodGet, "/state", nil)
	if err != nil {
		return nil, fmt.Errorf("runReq(/state): %w", err)
	}
	ui := &info.Info{}
	if err := json.Unmarshal(b, ui); err != nil {
		return nil, fmt.Errorf("unmarshal json response for status: %w", err)
	}
	return ui, nil
}

// SetMode runs a request to set the update mode
func (c *Client) SetMode(ctx context.Context, mode string) error {
	bs := &messages.ModeRequest{
		Mode: mode,
	}
	body, err := json.Marshal(bs)
	if err != nil {
		return fmt.Errorf("marshal mode request: %w", err)
	}
	if _, err := c.runReq(ctx, http.MethodPost, "/setmode", bytes.NewReader(body)); err != nil {
		return fmt.Errorf("setmode request: %w", err)
	}
	return nil
}

// GetMode runs a request to read the update mode
func (c *Client) GetMode(ctx context.Context) (string, error) {
	ui, err := c.Status(ctx)
	if err != nil {
		return "", fmt.Errorf("cluster status: %w", err)
	}
	return ui.Mode, nil
}

// ClusterProjectTarget queries the update target for a cluster in a project
func (c *Client) ClusterProjectTarget(ctx context.Context) (*messages.ClusterProjectTargetResponse, error) {
	b, err := c.runReq(ctx, http.MethodGet, "/projecttarget", nil)
	if err != nil {
		return nil, fmt.Errorf("runReq(/state): %w", err)
	}
	r := &messages.ClusterProjectTargetResponse{}
	if err := json.Unmarshal(b, r); err != nil {
		return nil, fmt.Errorf("unmarshal json response for status: %w", err)
	}
	return r, nil
}

// Run runs an update if one is pending
func (c *Client) Run(ctx context.Context) ([]byte, error) {
	return c.runReq(ctx, http.MethodPost, "/run", nil)
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

const modeCmdDesc = `
Read/Write the current update mechanism mode

There are 3 modes on the system
- 'off': no updates can run
- 'on': updates run on demand, when triggered by the user
- 'automatic': updates run as soon as they are available
`

var modeCmd = &cobra.Command{
	Use:   "mode",
	Short: "Read/Write the current update mechanism mode",
	Long:  modeCmdDesc,
	// at most one arg, the mode
	Args: cobra.MaximumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := cmd.Context()
		projectName := ClusterCmdViper.GetString(orgutil.KeyProject)
		c, err := forCluster(projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client: %w", err)
		}
		switch len(args) {
		case 0:
			mode, err := c.GetMode(ctx)
			if err != nil {
				return fmt.Errorf("get cluster upgrade mode: %w", err)
			}
			fmt.Printf("update mechanism mode: %s\n", mode)
			return nil
		case 1:
			if err := c.SetMode(ctx, args[0]); err != nil {
				return fmt.Errorf("set cluster upgrade mode: %w", err)
			}
			return nil
		default:
			return fmt.Errorf("invalid number of arguments. At most 1: %d", len(args))
		}
	},
}

const showTargetCmdDesc = `
Show the upgrade target version.

This command indicates for this cluster, what version it should be running to be considered up to
date for its environment.
Please use
- 'cluster upgrade' to inspect whether it is at the target and
- 'cluster upgrade run' to execute a pending update if there is one.
`

// showTargetCmd is the command to execute an update if available
var showTargetCmd = &cobra.Command{
	Use: "show-target",

	Short: "Show the upgrade target version.",
	Long:  showTargetCmdDesc,
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := cmd.Context()

		projectName := ClusterCmdViper.GetString(orgutil.KeyProject)
		c, err := forCluster(projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client: %w", err)
		}
		r, err := c.ClusterProjectTarget(ctx)
		if err != nil {
			return fmt.Errorf("cluster status: %w", err)
		}
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
		fmt.Fprintf(w, "flowstate\tos\n")
		fmt.Fprintf(w, "%s\t%s\n", r.Base, r.OS)
		w.Flush()
		return nil
	},
}

const runCmdDesc = `
Run an upgrade of the specified cluster, if new software is available.

This command will execute right away. Please make sure the cluster is safe
and ready to upgrade. It might reboot in the process.
`

// runCmd is the command to execute an update if available
var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Run an upgrade if available.",
	Long:  runCmdDesc,
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := cmd.Context()

		projectName := ClusterCmdViper.GetString(orgutil.KeyProject)
		c, err := forCluster(projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client: %w", err)
		}
		_, err = c.Run(ctx)
		if err != nil {
			return fmt.Errorf("cluster upgrade run: %w", err)
		}
		fmt.Printf("update for cluster %q in %q kicked off successfully.\n", clusterName, projectName)
		fmt.Printf("monitor running `inctl cluster upgrade --project %s --cluster %s\n`", projectName, clusterName)
		return nil
	},
}

// clusterUpgradeCmd is the base command to query the upgrade state
var clusterUpgradeCmd = &cobra.Command{
	Use:   "upgrade",
	Short: "Upgrade",
	Long:  "Upgrade Intrinsic software on target cluster.",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		ctx := cmd.Context()

		projectName := ClusterCmdViper.GetString(orgutil.KeyProject)
		c, err := forCluster(projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client: %w", err)
		}
		ui, err := c.Status(ctx)
		if err != nil {
			return fmt.Errorf("cluster status: %w", err)
		}
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
		fmt.Fprintf(w, "project\tcluster\tmode\tstate\tflowstate\tos\n")
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\n", projectName, clusterName, ui.Mode, ui.State, ui.CurrentBase, ui.CurrentOS)
		w.Flush()
		return nil
	},
}

func init() {
	ClusterCmd.AddCommand(clusterUpgradeCmd)
	clusterUpgradeCmd.PersistentFlags().StringVar(&clusterName, "cluster", "", "Name of cluster to upgrade.")
	clusterUpgradeCmd.MarkPersistentFlagRequired("cluster")
	clusterUpgradeCmd.AddCommand(runCmd)
	clusterUpgradeCmd.AddCommand(modeCmd)
	clusterUpgradeCmd.AddCommand(showTargetCmd)
}
