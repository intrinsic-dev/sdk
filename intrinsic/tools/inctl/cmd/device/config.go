// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package device

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"intrinsic/frontend/cloud/devicemanager/shared/shared"
	"intrinsic/tools/inctl/cmd/device/projectclient"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

func prettyPrintStatusInterfaces(interfaces map[string]shared.StatusInterface) string {
	ret := ""
	for name, iface := range interfaces {
		ret = ret + fmt.Sprintf("\t%s: %v\n", name, iface.IPAddress)
	}

	return ret
}

var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Tool to interact with device config",
}

type networkConfigInfo struct {
	Current map[string]shared.StatusInterface `json:"current"`
	Config  string                            `json:"config"`
}

func (info *networkConfigInfo) String() string {
	return "Current state:\n" + prettyPrintStatusInterfaces(info.Current) + "Current config: " + info.Config
}

var configGetCmd = &cobra.Command{
	Use:   "get",
	Short: "Retrieve current configuration",
	RunE: func(cmd *cobra.Command, args []string) error {
		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}

		projectName := viperLocal.GetString(keyProject)

		client, err := projectclient.Client(projectName)
		if err != nil {
			return fmt.Errorf("get project client: %w", err)
		}

		var status shared.Status
		if err := client.GetJSON(cmd.Context(), clusterName, deviceID, "relay/v1alpha1/status", &status); err != nil {
			if errors.Is(err, projectclient.ErrNotFound) {
				fmt.Fprintf(os.Stderr, "Cluster does not exist. Either it does not exist, or you don't have access to it.\n")
				return err
			}

			return fmt.Errorf("get status: %w", err)
		}
		prettyPrintStatusInterfaces(status.Network)

		res, err := client.GetDevice(cmd.Context(), clusterName, deviceID, "relay/v1alpha1/config/network")
		if err != nil {
			return fmt.Errorf("get config: %w", err)
		}
		defer res.Body.Close()

		if res.StatusCode != http.StatusOK {
			io.Copy(os.Stderr, res.Body)
			return fmt.Errorf("http code %v", res.StatusCode)
		}
		body, err := io.ReadAll(res.Body)
		if err != nil {
			return fmt.Errorf("read config: %w", err)
		}
		prtr.Print(&networkConfigInfo{Current: status.Network, Config: string(body)})

		if res.StatusCode != 200 {
			return fmt.Errorf("request failed")
		}

		return nil
	},
}

var configSetCmd = &cobra.Command{
	Use:   "set",
	Short: "Set the network config",
	Args:  cobra.MatchAll(cobra.ExactArgs(1), cobra.OnlyValidArgs),
	ValidArgsFunction: func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
		var comps []string
		if len(args) == 0 {
			comps = cobra.AppendActiveHelp(comps, "You must provide a valid network configuration in json format.")
		}

		return comps, cobra.ShellCompDirectiveNoFileComp
	},

	RunE: func(cmd *cobra.Command, args []string) error {
		projectName := viperLocal.GetString(keyProject)

		client, err := projectclient.Client(projectName)
		if err != nil {
			return fmt.Errorf("get project client: %w", err)
		}

		resp, err := client.PostDevice(cmd.Context(), clusterName, deviceID, "relay/v1alpha1/config/network", strings.NewReader(args[0]))
		if err != nil {
			if errors.Is(err, projectclient.ErrNotFound) {
				fmt.Fprintf(os.Stderr, "Cluster does not exist. Either it does not exist, or you don't have access to it.\n")
				return err
			}

			return fmt.Errorf("post config: %w", err)
		}
		defer resp.Body.Close()

		fmt.Printf("Got http code: %v\n", resp.StatusCode)
		io.Copy(os.Stderr, resp.Body)

		if resp.StatusCode != 200 {
			return fmt.Errorf("request failed")
		}

		return nil
	}}

func init() {
	deviceCmd.AddCommand(configCmd)
	configCmd.AddCommand(configGetCmd)
	configCmd.AddCommand(configSetCmd)
}
