// Copyright 2023 Intrinsic Innovation LLC

// Package orgutil provides common utility to handle projects/organizations in inctl.
package orgutil

import (
	"fmt"
	"os"
	"strings"

	"github.com/pkg/errors"
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
	// KeyEnvironment is used as central flag name for passing an environment name to inctl.
	//
	// The environment can be one of prod, staging or dev.
	KeyEnvironment = "env"
	// ProdEnvironment is the value for KeyEnvironment for the prod environment.
	ProdEnvironment = "prod"
	// StagingEnvironment is the value for KeyEnvironment for the staging environment.
	StagingEnvironment = "staging"
	// DevEnvironment is the value for KeyEnvironment for the dev environment.
	DevEnvironment = "dev"
)

var (
	// Exposed for testing
	authStore        = auth.NewStore()
	errNoOrg         = fmt.Errorf("expected --%s=<org>", KeyOrganization)
	errOrgAndProject = fmt.Errorf("do not set --%s, use --%s=<org> or <org@project> instead", KeyProject, KeyOrganization)

	noOrg = false
)

// ErrOrgNotFound indicates that the lookup for a given credential
// name failed.
type ErrOrgNotFound struct {
	err           error
	CandidateOrgs []string
	OrgName       string
}

func (e *ErrOrgNotFound) Error() string {
	return fmt.Sprintf("credentials not found: %q", e.OrgName)
}

func (e *ErrOrgNotFound) Unwrap() error {
	return e.err
}

func editDistance(left, right string) int {
	length := len([]rune(right))
	if length == 0 {
		return len([]rune(left))
	}

	dist1 := make([]int, length+1)
	dist2 := make([]int, length+1)

	// initialize dist1 (the previous row of distances)
	// this row is A[0][i]: edit distance from an empty left to right;
	// that distance is the number of characters to append to  left to make right.
	for i := 0; i < length+1; i++ {
		dist1[i] = i
		dist2[i] = 0
	}

	for i, vLeft := range []rune(left) {
		dist2[0] = i + 1

		for j, vRight := range []rune(right) {
			deletionCost := dist1[j+1] + 1
			insertionCost := dist2[j] + 1
			var substitutionCost int
			if vLeft == vRight {
				substitutionCost = dist1[j]
			} else {
				substitutionCost = dist1[j] + 1
			}

			// dist2[j + 1] = min(insertionCost, deletionCost, substitutionCost)
			if deletionCost <= insertionCost && deletionCost <= substitutionCost {
				dist2[j+1] = deletionCost
			} else if insertionCost <= deletionCost && insertionCost <= substitutionCost {
				dist2[j+1] = insertionCost
			} else {
				dist2[j+1] = substitutionCost
			}
		}

		copy(dist1, dist2)
	}

	return dist1[length]
}

func makeOrgNotFound(inner error, org string) error {
	candidates := []string{}
	orgs, err := auth.NewStore().ListOrgs()
	// We can only do this, if there's NO error!
	if err == nil {
		for _, candidate := range orgs {
			if editDistance(org, candidate) < 3 {
				candidates = append(candidates, candidate)
			}
		}
	}

	return &ErrOrgNotFound{err: inner, CandidateOrgs: candidates, OrgName: org}
}

// ValidateEnvironment validates the environment value in a cobra command.
func ValidateEnvironment(vipr *viper.Viper) error {
	env := vipr.GetString(KeyEnvironment)
	if env == "" {
		return fmt.Errorf("--%s needs to be set", KeyEnvironment)
	}
	switch env {
	case ProdEnvironment, StagingEnvironment, DevEnvironment:
		return nil
	default:
		return fmt.Errorf("invalid --%s value %q. It must be one of %s, %s or %s", KeyEnvironment, env, ProdEnvironment, StagingEnvironment, DevEnvironment)
	}
}

// PreRunOrganizationOptional provides the organization/project flag handling as PersistentPreRunE
// of a cobra command. This is done automatically with the WrapCmdOptional() function.
//
// However, it lets the user skip setting --org in case they prefer --context with a local context /
// alias.
func PreRunOrganizationOptional(cmd *cobra.Command, vipr *viper.Viper) error {
	projectFlag := cmd.PersistentFlags().Lookup(KeyProject)
	orgFlag := cmd.PersistentFlags().Lookup(KeyOrganization)

	org := vipr.GetString(KeyOrganization)
	project := vipr.GetString(KeyProject)

	if project != "" && org != "" {
		return errOrgAndProject
	}

	if org == "" {
		// When using --project, the org is unknown and no further logic is required.
		return nil
	}

	// Look up the project that contains this org.
	info, err := authStore.ReadOrgInfo(org)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return makeOrgNotFound(err, org)
		}

		return err
	}
	projectFlag.Value.Set(info.Project)
	vipr.Set(KeyProject, info.Project)

	// Cleanup the org parameter, it could be org@project.
	// The full name is only required to lookup the correct project. So we can clean it up here
	cleanOrg := strings.Split(org, "@")[0]

	orgFlag.Value.Set(cleanOrg)
	vipr.Set(KeyOrganization, cleanOrg)
	return nil
}

// PreRunOrganization checks organization/project flags as PersistentPreRunE of a cobra command.
// This is done automatically with the WrapCmd() function. PreRunOrganization() doesn't call
// PreRunOrganizationOptional() itself.
//
// It enforces that exactly one of --project or --org is set.
func PreRunOrganization(cmd *cobra.Command, vipr *viper.Viper) error {
	org := vipr.GetString(KeyOrganization)
	project := vipr.GetString(KeyProject)

	if project == "" && org == "" {
		return errNoOrg
	}
	if org == "" {
		noOrg = true
		fmt.Fprintf(os.Stderr, "\ninctl was called without an organization. This is deprecated and will soon be an error. Please use --org intrinsic@%v.\n", project)
	}

	return nil
}

// WrapCmdOptional injects KeyProject and KeyOrganization as PersistentFlags into the command and
// sets up shared handling for them.
//
// However, it lets the user skip setting --org in case they prefer --context with a local context /
// alias.
func WrapCmdOptional(cmd *cobra.Command, vipr *viper.Viper) *cobra.Command {
	cmd.PersistentFlags().StringP(KeyProject, "p", "",
		`The Google Cloud Project (GCP) project to use. You can set the environment variable
		INTRINSIC_PROJECT=project_name to set a default project name.`)
	cmd.PersistentFlags().StringP(KeyOrganization, "", "",
		`The Intrinsic organization to use. You can set the environment variable
		INTRINSIC_ORG=organization to set a default organization.`)

	oldPreRunE := cmd.PersistentPreRunE
	cmd.PersistentPreRunE = func(c *cobra.Command, args []string) error {
		// This is required to cooperate with cobrautil.
		// Cobrautil's way to force an error instead of 0 return code when there's no subcommand
		// causes cobra to run the PersistentPreRunE either way. So we need to short-circuit
		// the flag handling here.
		if !c.DisableFlagParsing {
			if err := PreRunOrganizationOptional(cmd, vipr); err != nil {
				return err
			}
		}

		if oldPreRunE != nil {
			return oldPreRunE(c, args)
		}
		return nil
	}

	viperutil.BindFlags(vipr, cmd.PersistentFlags(), viperutil.BindToListEnv(KeyOrganization))

	return cmd
}

// WrapCmd injects KeyProject and KeyOrganization as PersistentFlags into the command and sets up
// shared handling for them.
//
// It enforces that exactly one of --project or --org is set.
func WrapCmd(cmd *cobra.Command, vipr *viper.Viper) *cobra.Command {
	cmd = WrapCmdOptional(cmd, vipr)

	oldPreRunE := cmd.PersistentPreRunE
	cmd.PersistentPreRunE = func(c *cobra.Command, args []string) error {
		// This is required to cooperate with cobrautil.
		// Cobrautil's way to force an error instead of 0 return code when there's no subcommand
		// causes cobra to run the PersistentPreRunE either way. So we need to short-circuit
		// the flag handling here.
		if !c.DisableFlagParsing {
			if err := PreRunOrganization(cmd, vipr); err != nil {
				return err
			}
		}

		if oldPreRunE != nil {
			return oldPreRunE(c, args)
		}
		return nil
	}
	oldPostRunE := cmd.PersistentPostRunE
	cmd.PersistentPostRunE = func(c *cobra.Command, args []string) error {
		if noOrg {
			fmt.Fprintf(os.Stderr, "\ninctl was called without an organization. This is deprecated and will soon be an error. Please use --org.\n")
		}

		if oldPostRunE != nil {
			return oldPostRunE(c, args)
		}
		return nil
	}

	return cmd
}

// SharedOrg identifies if an org name is ambiguous, ie if it is unqualified and present in multiple
// projects.
func SharedOrg(orgName string) bool {
	return orgName == "intrinsic"
}

// QualifiedOrg returns a "unique" org name, adding an @project suffix for orgs that are present in
// multiple projects. This undoes the "cleaning" applied by PreRunOrganization when using WrapCmd().
func QualifiedOrg(projectName, orgName string) string {
	if orgName == "" {
		return fmt.Sprintf("intrinsic@%s", projectName)
	}
	if SharedOrg(orgName) {
		orgName = fmt.Sprintf("%s@%s", orgName, projectName)
	}
	return orgName
}
