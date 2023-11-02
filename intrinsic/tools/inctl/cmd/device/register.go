// Copyright 2023 Intrinsic Innovation LLC

package device

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"

	"github.com/spf13/cobra"
	"intrinsic/frontend/cloud/devicemanager/shared"
	"intrinsic/tools/inctl/cmd/device/projectclient"
	"intrinsic/tools/inctl/util/orgutil"
)

const (
	// https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-label-names
	hostnameRegexString = `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?`
)

var (
	deviceRole    = ""
	deviceRegion  = ""
	privateDevice = false
	replaceDevice = false
)

func validHostname(hostname string) (int, bool) {
	match := regexp.MustCompile(hostnameRegexString).FindStringIndex(hostname)
	if len(match) < 2 {
		return 0, false
	}

	// This should be guaranteed by ^, but better save than sorry
	if match[0] != 0 {
		return -1, false
	}

	// Make sure we matched the entire string
	if match[1] != len(hostname) {
		return match[1] + 1, false
	}

	return 0, true
}

func makeNameError(hostname string, index int) string {
	if len(hostname) == 0 {
		return "hostname cannot be empty"
	}

	if len(hostname) > 64 {
		return "hostname cannot exceed 64 characters"
	}

	if strings.HasSuffix(hostname, "-") {
		return "hostname cannot end with a dash"
	}

	if regexp.MustCompile("[A-Z]").MatchString(hostname) {
		return "hostname cannot contain upper case letters"
	}

	if index < 1 {
		index = 1
	}
	offender := hostname[index-1]
	return fmt.Sprintf("Cannot use %q in hostname", offender)
}

var registerCmd = &cobra.Command{
	Use:   "register",
	Short: "Tool to register hardware in setup flow",
	RunE: func(cmd *cobra.Command, args []string) error {
		projectName := viperLocal.GetString(orgutil.KeyProject)
		orgName := viperLocal.GetString(orgutil.KeyOrganization)
		hostname := viperLocal.GetString(keyHostname)
		if hostname == "" {
			hostname = deviceID
		}
		if deviceRole != "control-plane" && clusterName == "" {
			fmt.Printf("--cluster_name needs to be provided for role %q\n", deviceRole)
			return fmt.Errorf("invalid arguments")
		}

		if offender, ok := validHostname(hostname); !ok {
			fmt.Printf("%q is not a valid as hostname. Provide a valid hostname.\nSee https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-label-names for more information.\n", hostname)
			return fmt.Errorf(makeNameError(hostname, offender))
		}

		client, err := projectclient.Client(projectName, orgName)
		if err != nil {
			return fmt.Errorf("get client for project: %w", err)
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
			Region:   deviceRegion,
			Replace:  replaceDevice,
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
			fmt.Printf("Sent configuration to server. The device will reboot and apply the configuration within a minute.\n")
			return nil
		case http.StatusConflict:
			return fmt.Errorf("cluster %q already exists. Cannot create it again. Please use a unique value for --hostname", hostname)
		case http.StatusPreconditionFailed:
			return fmt.Errorf("cluster %q does not exist. please make sure that --cluster_name matches the --hostname from a previously registered cluster.\nIf you want to create a new cluster, do not use --device_role", clusterName)
		case http.StatusNotFound:
			return fmt.Errorf("device %q does not exist. please make sure you have the exact id from the device you are trying to register", deviceID)
		case http.StatusForbidden:
			if orgName == "" {
				orgName = fmt.Sprintf("defaultorg@%s", projectName)
			}
			return fmt.Errorf("you do not have the necessary permissions to add a cluster on organization %q.\nOpen a support request to get the 'clusterProvisioner' role", orgName)
		default:
			io.Copy(os.Stderr, resp.Body)

			return fmt.Errorf("request failed. http code: %v", resp.StatusCode)
		}
	}}

func init() {
	deviceCmd.AddCommand(registerCmd)

	registerCmd.Flags().StringVarP(&deviceRole, "device_role", "", "control-plane", "The role the device has in the cluster. Either 'control-plane' or 'worker'")
	registerCmd.Flags().BoolVarP(&privateDevice, "private", "", false, "If set to 'true', the device will not be visible to other organization members")
	registerCmd.Flags().StringVarP(&deviceRegion, "region", "", "unspecified", "This can be used for inventory tracking")
	registerCmd.Flags().BoolVarP(&replaceDevice, "replace", "", false, "If set to 'true', an existing cluster with the same name will be replaced.\nThis is equivalent to calling 'inctl cluster delete' first")
}
