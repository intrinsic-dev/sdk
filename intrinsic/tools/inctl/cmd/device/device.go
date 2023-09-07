// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package device groups the commands for managing on-prem devices via inctl.
package device

import (
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	keyProject  = "project"
	keyHostname = "hostname"

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
}

func init() {
	root.RootCmd.AddCommand(deviceCmd)

	deviceCmd.PersistentFlags().StringVarP(&deviceID, "device_id", "", "", "The device ID of the device to claim")
	deviceCmd.MarkPersistentFlagRequired("device_id")

	deviceCmd.PersistentFlags().StringP(keyProject, "p", "",
		`The Google Cloud Project (GCP) project to use. You can set the environment variable
		INTRINSIC_PROJECT=project_name to set a default project name.`)
	deviceCmd.PersistentFlags().StringVarP(&clusterName, keyClusterName, "", "",
		`The cluster to join. Required for workers, ignored on control-plane.
		You can set the environment variable INTRINSIC_CLUSTER_NAME=cluster_name to set a default cluster_name.`)
	deviceCmd.PersistentFlags().StringP(keyHostname, "", "",
		`The hostname for the device. If it's a control plane this will be the cluster name.`)

	viperLocal = viperutil.BindToViper(deviceCmd.PersistentFlags(), viperutil.BindToListEnv(keyProject, keyClusterName))
	if viperLocal.GetString(keyProject) == "" {
		deviceCmd.MarkPersistentFlagRequired(keyProject)
	}
}
