// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package device groups the commands for managing on-prem devices via inctl.
package device

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	keyProject      = "project"
	keyOrganization = "org"
	keyHostname     = "hostname"

	keyClusterName = "cluster_name"
)

var (
	deviceID    = ""
	clusterName = ""
)

var viperLocal *viper.Viper

var deviceCmd = &cobra.Command{
	Use:   "device",
	Short: "Manages user authorization",
	Long:  "Manages user authorization for accessing solutions in the project.",
	// Catching common typos and potential alternatives
	SuggestFor: []string{"devcie", "dve", "deviec"},

	PersistentPreRunE: func(_ *cobra.Command, _ []string) error {
		if viperLocal.GetString(keyProject) == "" && viperLocal.GetString(keyOrganization) == "" {
			return fmt.Errorf("at least one of --%s or --%s needs to be set", keyProject, keyOrganization)
		}

		return nil
	},
}

func init() {
	root.RootCmd.AddCommand(deviceCmd)

	deviceCmd.PersistentFlags().StringVarP(&deviceID, "device_id", "", "", "The device ID of the device to claim")
	deviceCmd.MarkPersistentFlagRequired("device_id")

	deviceCmd.PersistentFlags().StringP(keyProject, "p", "",
		`The Google Cloud Project (GCP) project to use. You can set the environment variable
		INTRINSIC_PROJECT=project_name to set a default project name.`)
	deviceCmd.PersistentFlags().StringP(keyOrganization, "", "",
		`The Intrinsic organization. You can set the environment variable
		INTRINSIC_ORGANIZATION=organization to set a default organization.`)
	deviceCmd.PersistentFlags().StringVarP(&clusterName, keyClusterName, "", "",
		`The cluster to join. Required for workers, ignored on control-plane.
		You can set the environment variable INTRINSIC_CLUSTER_NAME=cluster_name to set a default cluster_name.`)
	deviceCmd.PersistentFlags().StringP(keyHostname, "", "",
		`The hostname for the device. If it's a control plane this will be the cluster name.`)

	viperLocal = viperutil.BindToViper(deviceCmd.PersistentFlags(), viperutil.BindToListEnv(keyProject, keyClusterName, keyOrganization))
}
