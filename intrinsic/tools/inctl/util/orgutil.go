// Copyright 2023 Intrinsic Innovation LLC

// Package orgutil provides common utility to handle projects/organizations in inctl.
package orgutil

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	// KeyProject is used as central flag name for passing a project name to inctl.
	KeyProject = "project"
	// KeyOrganization is used as central flag name for passing an organization name to inctl.
	KeyOrganization = "org"
)

var (
	// Exposed for testing
	authStore = auth.NewStore()
	errNotXor = fmt.Errorf("exactly one of --%s or --%s must be set", KeyProject, KeyOrganization)
)

// ErrOrgNotFound indicates that the lookup for a given credential
// name failed.
type ErrOrgNotFound struct {
	Err     error // the underlying error
	OrgName string
}

func (e *ErrOrgNotFound) Error() string {
	return fmt.Sprintf("credentials not found: %v", e.Err)
}

func (e *ErrOrgNotFound) Unwrap() error { return e.Err }

// PreRunOrganization provides the organization/project flag handling as PersistentPreRunE of a cobra command.
// This is done automatically with the wrap function.
func PreRunOrganization(cmd *cobra.Command, vipr *viper.Viper) error {
	projectFlag := cmd.PersistentFlags().Lookup(KeyProject)
	orgFlag := cmd.PersistentFlags().Lookup(KeyOrganization)

	org := vipr.GetString(KeyOrganization)
	project := vipr.GetString(KeyProject)

	if (project == "" && org == "") || (project != "" && org != "") {
		return errNotXor
	}

	// User used the organization flow.
	// The above also guarantees that org is set
	if project == "" {
		info, err := authStore.ReadOrgInfo(org)
		if err != nil {
			return &ErrOrgNotFound{Err: err, OrgName: org}
		}

		projectFlag.Value.Set(info.Project)
		vipr.Set(KeyProject, info.Project)
	}

	// Cleanup the org parameter, it could be org@project.
	// The full name is only required to lookup the correct project. So we can clean it up here
	if org != "" {
		cleanOrg := strings.Split(org, "@")[0]

		orgFlag.Value.Set(cleanOrg)
		vipr.Set(KeyOrganization, cleanOrg)
	}

	return nil
}

// WrapCmd injects KeyProject and KeyOrganization as PersistentFlags into the command and sets up shared handling for them.
func WrapCmd(cmd *cobra.Command, vipr *viper.Viper) *cobra.Command {
	cmd.PersistentFlags().StringP(KeyProject, "p", "",
		`The Google Cloud Project (GCP) project to use. You can set the environment variable
		INTRINSIC_PROJECT=project_name to set a default project name.`)
	cmd.PersistentFlags().StringP(KeyOrganization, "", "",
		`The Intrinsic organization to use. You can set the environment variable
		INTRINSIC_ORGANIZATION=organization to set a default organization.`)

	oldPreRunE := cmd.PersistentPreRunE
	cmd.PersistentPreRunE = func(c *cobra.Command, args []string) error {
		if err := PreRunOrganization(cmd, vipr); err != nil {
			return err
		}

		if oldPreRunE != nil {
			return oldPreRunE(c, args)
		}
		return nil
	}

	viperutil.BindFlags(vipr, cmd.PersistentFlags(), viperutil.BindToListEnv(KeyProject, KeyOrganization))

	return cmd
}
