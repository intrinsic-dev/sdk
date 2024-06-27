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

	"intrinsic/frontend/cloud/devicemanager/info"
	"intrinsic/frontend/cloud/devicemanager/messages"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/util/orgutil"
)

var (
	clusterName  string
	rollbackFlag bool
)

// client helps run auth'ed requests for a specific cluster
type client struct {
	client      *http.Client
	tokenSource *auth.ProjectToken
	cluster     string
	project     string
	org         string
}

// do wraps http.Client.Do with Auth
func (c *client) do(req *http.Request) (*http.Response, error) {
	req, err := c.tokenSource.HTTPAuthorization(req)
	if err != nil {
		return nil, fmt.Errorf("auth token for %q %s: %w", req.Method, req.URL.String(), err)
	}
	return c.client.Do(req)
}

// runReq runs a |method| request with url and returns the response/error
func (c *client) runReq(ctx context.Context, method string, url url.URL, body io.Reader) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, method, url.String(), body)
	if err != nil {
		return nil, fmt.Errorf("create %q request for %s: %w", method, url.String(), err)
	}
	resp, err := c.do(req)
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
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, rb)
	}
	return rb, nil
}

// status queries the update status of a cluster
func (c *client) status(ctx context.Context) (*info.Info, error) {
	v := url.Values{}
	v.Set("cluster", c.cluster)
	u := newClusterUpdateURL(c.project, "/state", v)
	b, err := c.runReq(ctx, http.MethodGet, u, nil)
	if err != nil {
		return nil, err
	}
	ui := &info.Info{}
	if err := json.Unmarshal(b, ui); err != nil {
		return nil, fmt.Errorf("unmarshal json response for status: %w", err)
	}
	return ui, nil
}

// setMode runs a request to set the update mode
func (c *client) setMode(ctx context.Context, mode string) error {
	bs := &messages.ModeRequest{
		Mode: mode,
	}
	body, err := json.Marshal(bs)
	if err != nil {
		return fmt.Errorf("marshal mode request: %w", err)
	}
	v := url.Values{}
	v.Set("cluster", c.cluster)
	u := newClusterUpdateURL(c.project, "/setmode", v)
	_, err = c.runReq(ctx, http.MethodPost, u, bytes.NewReader(body))
	return err
}

// getMode runs a request to read the update mode
func (c *client) getMode(ctx context.Context) (string, error) {
	ui, err := c.status(ctx)
	if err != nil {
		return "", fmt.Errorf("cluster status: %w", err)
	}
	return ui.Mode, nil
}

// clusterProjectTarget queries the update target for a cluster in a project
func (c *client) clusterProjectTarget(ctx context.Context) (*messages.ClusterProjectTargetResponse, error) {
	v := url.Values{}
	v.Set("cluster", c.cluster)
	u := newClusterUpdateURL(c.project, "/projecttarget", v)
	b, err := c.runReq(ctx, http.MethodGet, u, nil)
	if err != nil {
		return nil, err
	}
	r := &messages.ClusterProjectTargetResponse{}
	if err := json.Unmarshal(b, r); err != nil {
		return nil, fmt.Errorf("unmarshal json response for status: %w", err)
	}
	return r, nil
}

// run runs an update if one is pending
func (c *client) run(ctx context.Context, rollback bool) error {
	v := url.Values{}
	v.Set("cluster", c.cluster)
	if rollback {
		v.Set("rollback", "y")
	}
	u := newClusterUpdateURL(c.project, "/run", v)
	_, err := c.runReq(ctx, http.MethodPost, u, nil)
	return err
}

func newTokenSource(project string) (*auth.ProjectToken, error) {
	configuration, err := auth.NewStore().GetConfiguration(project)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, &dialerutil.ErrCredentialsNotFound{
				CredentialName: project,
				Err:            err,
			}
		}
		return nil, fmt.Errorf("get configuration for project %q: %w", project, err)
	}
	token, err := configuration.GetDefaultCredentials()
	if err != nil {
		return nil, fmt.Errorf("get default credentials for project %q: %w", project, err)
	}
	return token, nil
}

func newClusterUpdateURL(project string, subPath string, values url.Values) url.URL {
	return url.URL{
		Scheme:   "https",
		Host:     fmt.Sprintf("www.endpoints.%s.cloud.goog", project),
		Path:     filepath.Join("/api/clusterupdate/", subPath),
		RawQuery: values.Encode(),
	}
}

func newClient(org, project, cluster string) (client, error) {
	ts, err := newTokenSource(project)
	if err != nil {
		return client{}, err
	}
	return client{
		client:      http.DefaultClient,
		tokenSource: ts,
		cluster:     cluster,
		project:     project,
		org:         org,
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
		orgName := ClusterCmdViper.GetString(orgutil.KeyOrganization)
		c, err := newClient(orgName, projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client: %w", err)
		}
		switch len(args) {
		case 0:
			mode, err := c.getMode(ctx)
			if err != nil {
				return fmt.Errorf("get cluster upgrade mode:\n%w", err)
			}
			fmt.Printf("update mechanism mode: %s\n", mode)
			return nil
		case 1:
			if err := c.setMode(ctx, args[0]); err != nil {
				return fmt.Errorf("set cluster upgrade mode:\n%w", err)
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
		orgName := ClusterCmdViper.GetString(orgutil.KeyOrganization)
		c, err := newClient(orgName, projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client:\n%w", err)
		}
		r, err := c.clusterProjectTarget(ctx)
		if err != nil {
			return fmt.Errorf("cluster status:\n%w", err)
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
		orgName := ClusterCmdViper.GetString(orgutil.KeyOrganization)
		qOrgName := orgutil.QualifiedOrg(projectName, orgName)
		c, err := newClient(orgName, projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client:\n%w", err)
		}
		err = c.run(ctx, rollbackFlag)
		if err != nil {
			return fmt.Errorf("cluster upgrade run:\n%w", err)
		}

		fmt.Printf("update for cluster %q in %q kicked off successfully.\n", clusterName, qOrgName)
		fmt.Printf("monitor running `inctl cluster upgrade --org %s --cluster %s\n`", qOrgName, clusterName)
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
		orgName := ClusterCmdViper.GetString(orgutil.KeyOrganization)
		c, err := newClient(orgName, projectName, clusterName)
		if err != nil {
			return fmt.Errorf("cluster upgrade client:\n%w", err)
		}
		ui, err := c.status(ctx)
		if err != nil {
			return fmt.Errorf("cluster status:\n%w", err)
		}
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
		rollback := ui.RollbackOS != "" && ui.RollbackBase != ""
		fmt.Fprintf(w, "project\tcluster\tmode\tstate\trollback available\tflowstate\tos\n")
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%v\t%s\t%s\n", projectName, clusterName, ui.Mode, ui.State, rollback, ui.CurrentBase, ui.CurrentOS)
		w.Flush()
		return nil
	},
}

func init() {
	ClusterCmd.AddCommand(clusterUpgradeCmd)
	clusterUpgradeCmd.PersistentFlags().StringVar(&clusterName, "cluster", "", "Name of cluster to upgrade.")
	clusterUpgradeCmd.MarkPersistentFlagRequired("cluster")
	clusterUpgradeCmd.AddCommand(runCmd)
	runCmd.PersistentFlags().BoolVar(&rollbackFlag, "rollback", false, "Whether to trigger a rollback update instead")
	clusterUpgradeCmd.AddCommand(modeCmd)
	clusterUpgradeCmd.AddCommand(showTargetCmd)
}
