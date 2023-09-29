// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package device

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/spf13/cobra"
	"intrinsic/frontend/cloud/devicemanager/shared/shared"
	"intrinsic/tools/inctl/auth/auth"
	"intrinsic/tools/inctl/cmd/device/projectclient"
)

var (
	deviceRole    = ""
	privateDevice = false
)

var registerCmd = &cobra.Command{
	Use:   "register",
	Short: "Tool to register hardware in setup flow",
	RunE: func(cmd *cobra.Command, args []string) error {
		projectName := viperLocal.GetString(keyProject)
		orgName := viperLocal.GetString(keyOrganization)
		hostname := viperLocal.GetString(keyHostname)
		if hostname == "" {
			hostname = deviceID
		}
		if deviceRole != "control-plane" && clusterName == "" {
			fmt.Printf("--cluster_name needs to be provided for role %q\n", deviceRole)
			return fmt.Errorf("invalid arguments")
		}

		client, err := projectclient.Client(projectName, orgName)
		if err != nil {
			return fmt.Errorf("get client for project: %w", err)
		}
		if projectName == "" {
			info, err := auth.NewStore().ReadOrgInfo(orgName)
			if err != nil {
				return fmt.Errorf("get org info: %w", err)
			}
			projectName = info.Project
		}

		// This map represents a json mapping of the config struct which lives in GoB:
		// https://source.corp.google.com/h/intrinsic/xfa-tools/+/main:internal/config/config.go
		config := map[string]any{
			"hostname": hostname,
			"cloudConnection": map[string]any{
				"project": projectName,
				"token":   "not-a-valid-token",
				"name":    hostname,
			},
			"cluster": map[string]any{
				"role": deviceRole,
				// Only relevant for worker, but this doesn't hurt the control-plane nodes.
				"controlPlaneURI": fmt.Sprintf("%s:6443", clusterName),
				"token":           shared.TokenPlaceholder,
			},
			"version": "v1alphav1",
		}
		// For now, assume that control planes have a GPU...
		if deviceRole == "control-plane" {
			config["gpuConfig"] = map[string]any{
				"enabled":  true,
				"replicas": 8,
			}
		}
		marshalled, err := json.Marshal(config)
		if err != nil {
			return fmt.Errorf("failed to marshal config: %w", err)
		}
		data := shared.ConfigureData{
			Hostname: hostname,
			Config:   marshalled,
			Role:     deviceRole,
			Cluster:  clusterName,
			Private:  privateDevice,
		}
		if testID := os.Getenv("INCTL_CREATED_BY_TEST"); testID != "" {
			// This is an automated test.
			data.CreatedByTest = testID
		}
		body, err := json.Marshal(data)
		if err != nil {
			return fmt.Errorf("failed to marshal config: %w", err)
		}

		resp, err := client.PostDevice(cmd.Context(), clusterName, deviceID, "configure", bytes.NewBuffer(body))
		if err != nil {
			return err
		}
		defer resp.Body.Close()

		switch resp.StatusCode {
		case http.StatusOK:
			// copybara_strip:begin
			if deviceRole == "control-plane" {
				fmt.Printf("Use these commands to add the cluster to your kubeconfig and connect via k9s:\n")
				fmt.Printf(`	kubectl config set-cluster "%s" --server="https://www.endpoints.%s.cloud.goog/apis/core.kubernetes-relay/client/%s"`+"\n",
					hostname, projectName, hostname)
				fmt.Printf(`	kubectl config set-context "%s" --cluster "%s" --namespace "default" --user "gke_%s_us-central1-a_cloud-robotics"`+"\n",
					hostname, hostname, projectName)
			}
			// copybara_strip:end
			return nil
		case http.StatusConflict:
			return fmt.Errorf("cluster %q already exists. Cannot create it again. Please use a unique value for --hostname", hostname)
		case http.StatusPreconditionFailed:
			return fmt.Errorf("cluster %q does not exist. please make sure that --cluster_name matches the --hostname from a previously registered cluster.\nIf you want to create a new cluster, do not use --device_role", clusterName)
		case http.StatusNotFound:
			return fmt.Errorf("device %q does not exist. please make sure you have the exact id from the device you are trying to register", deviceID)
		default:
			io.Copy(os.Stderr, resp.Body)

			return fmt.Errorf("request failed. http code: %v", resp.StatusCode)
		}
	}}

func init() {
	deviceCmd.AddCommand(registerCmd)

	registerCmd.Flags().StringVarP(&deviceRole, "device_role", "", "control-plane", "The role the device has in the cluster. Either 'control-plane' or 'worker'")
	registerCmd.Flags().BoolVarP(&privateDevice, "private", "", false, "If set to 'true', the device will not be visible to other organization members")
}
