// Copyright 2023 Intrinsic Innovation LLC

// Package device groups the commands for managing on-prem devices via inctl.
package device

import (
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	keyHostname = "hostname"

	keyClusterName = "cluster_name"
)

var (
	deviceID    = ""
	clusterName = ""
	viperLocal  = viper.New()
)

var deviceCmd = orgutil.WrapCmd(
	&cobra.Command{
		Use:   "device",
		Short: "Manage device specific settings and registration.",
		Long:  "This subcommand provides utilities that interact with singular devices.\nThese are generally part of a cluster, or not yet registered to any user.",
		// Catching common typos and potential alternatives
		SuggestFor: []string{"devcie", "dve", "deviec"},
	}, viperLocal)

func init() {
	root.RootCmd.AddCommand(deviceCmd)

	deviceCmd.PersistentFlags().StringVarP(&deviceID, "device_id", "", "", "The device ID of the device to claim")
	deviceCmd.MarkPersistentFlagRequired("device_id")

	deviceCmd.PersistentFlags().StringVarP(&clusterName, keyClusterName, "", "",
		`The cluster to join. Required for workers, ignored on control-plane.
		You can set the environment variable INTRINSIC_CLUSTER_NAME=cluster_name to set a default cluster_name.`)
	deviceCmd.PersistentFlags().StringP(keyHostname, "", "",
		`The hostname for the device. If it's a control plane this will be the cluster name.`)

	viperutil.BindFlags(viperLocal, deviceCmd.PersistentFlags(), viperutil.BindToListEnv(keyClusterName))
}
