// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"fmt"

	"github.com/spf13/cobra"
	"intrinsic/tools/inctl/util/orgutil"
)

func init() {
	authCmd.AddCommand(printCmd)
	printCmd.Flags().StringP(orgutil.KeyProject, keyProjectShort, "", "Name of the Google cloud project to authorize for")
	printCmd.MarkFlagRequired(orgutil.KeyProject)
}

var printCmd = &cobra.Command{
	Use:   "print-api-key",
	Short: "Prints the API key for a project.",
	Long:  "Prints the API key for a project.",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, args []string) error {
		project, err := cmd.Flags().GetString(orgutil.KeyProject)
		if err != nil {
			return err
		}
		store, err := authStore.GetConfiguration(project)
		if err != nil {
			return fmt.Errorf("failed to get configuration for project %q: %v", project, err)
		}
		key, err := store.GetCredentials("default")
		if err != nil {
			return fmt.Errorf("failed to get default API key for project %q: %v", project, err)
		}
		fmt.Print(key.APIKey)
		return nil
	},
}
