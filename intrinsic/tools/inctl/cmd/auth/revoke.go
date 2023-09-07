// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package auth

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"go.uber.org/multierr"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	keyRevokeAll = "all"
)

var revokeParams *viper.Viper

var revokeCmd = &cobra.Command{
	Use:     "revoke",
	Aliases: []string{"ls"},
	Short:   "Removes local credentials",
	Long:    "Remove selected local credentials. Credentials are currently not revoked on server.",
	Args:    cobra.NoArgs,
	RunE:    revokeCredentialsE,
}

func revokeCredentialsE(cmd *cobra.Command, _ []string) error {
	isRevokeAll := revokeParams.GetBool(keyRevokeAll)
	projectName := revokeParams.GetString(keyProject)
	if !isRevokeAll && projectName == "" {
		return fmt.Errorf("either --%s or --%s needs to be specified", keyProject, keyRevokeAll)
	}

	isBatch := revokeParams.GetBool(keyBatch)

	rw := newReadWriterForCmd(cmd)
	if projectName == "" && isRevokeAll {
		if !isBatch {
			resp, err := userPrompt(rw, "Are you sure you want to remove all projects?", 1, "yes", "NO")
			if err != nil {
				// this error means something terrible happened with terminal, aborting is really only option
				return fmt.Errorf("cannot continue: %w", err)
			}
			if resp != "yes" {
				return fmt.Errorf("aborted by user")
			}
		}
		return removeAllProjects()
	} else if authStore.HasConfiguration(projectName) {
		if !isBatch {
			prompt := fmt.Sprintf("Are you sure you want to revoke all credentials for '%s'", projectName)
			resp, err := userPrompt(rw, prompt, 1, "yes", "NO")
			if err != nil {
				return err
			} else if resp != "yes" {
				return fmt.Errorf("aborted by user")
			}
		}
		return authStore.RemoveConfiguration(projectName)
	} else {
		return fmt.Errorf("cannot find configuration for %s", projectName)
	}
}

func removeAllProjects() error {
	configurations, err := authStore.ListConfigurations()
	if err != nil {
		return err
	}
	for _, configuration := range configurations {
		err = multierr.Append(err, authStore.RemoveConfiguration(configuration))
	}
	return err
}

func init() {
	authCmd.AddCommand(revokeCmd)

	flags := revokeCmd.Flags()

	flags.StringP(keyProject, keyProjectShort, "", "Project to revoke credentials for")
	flags.Bool(keyRevokeAll, false, "Revokes all credentials for given project. If project is omitted, removes all known credentials")
	flags.Bool(keyBatch, false, "Suppresses command prompts and assume Yes or default as an answer. Use with shell scripts.")

	revokeParams = viperutil.BindToViper(flags, viperutil.BindToListEnv(keyProject))

}
