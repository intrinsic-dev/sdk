// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"fmt"
	"net/http"

	"github.com/spf13/cobra"

	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/util/orgutil"
)

var (
	flagFlowstateAddr string
)

func init() {
	authCmd.AddCommand(printAPIKeyCmd)
	printAPIKeyCmd.Flags().StringP(orgutil.KeyProject, keyProjectShort, "", "Name of the Google cloud project to authorize for")
	printAPIKeyCmd.MarkFlagRequired(orgutil.KeyProject)

	authCmd.AddCommand(printAccessTokenCmd)
	printAccessTokenCmd.Flags().StringP(orgutil.KeyProject, keyProjectShort, "", "Name of the Google cloud project to authorize for")
	printAccessTokenCmd.MarkFlagRequired(orgutil.KeyProject)
	printAccessTokenCmd.Flags().StringVar(&flagFlowstateAddr, "flowstate", "flowstate.intrinsic.ai", "Flowstate address.")
}

var printAPIKeyCmd = &cobra.Command{
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
		key, err := store.GetDefaultCredentials()
		if err != nil {
			return fmt.Errorf("failed to get default API key for project %q: %v", project, err)
		}
		fmt.Print(key.APIKey)
		return nil
	},
}

var makeHTTPClient = func() *http.Client { // for unit-tests
	return &http.Client{}
}

var printAccessTokenCmd = &cobra.Command{
	Use:   "print-access-token",
	Short: "Print an access token.",
	Long:  "Print an access token.",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := cmd.Context()
		project, err := cmd.Flags().GetString(orgutil.KeyProject)
		if err != nil {
			return fmt.Errorf("failed to get project: %v", err)
		}
		store, err := authStore.GetConfiguration(project)
		if err != nil {
			return fmt.Errorf("failed to get configuration for project %q: %v", project, err)
		}
		key, err := store.GetDefaultCredentials()
		if err != nil {
			return fmt.Errorf("failed to get default API key for project %q: %v", project, err)
		}
		resp, err := auth.GetIDToken(ctx, makeHTTPClient(), flagFlowstateAddr, &auth.GetIDTokenRequest{
			APIKey:   key.APIKey,
			DoFanOut: true,
		})
		if err != nil {
			return fmt.Errorf("failed to get ID token : %v", err)
		}
		cmd.Printf(resp.IDToken)
		return nil
	},
}
