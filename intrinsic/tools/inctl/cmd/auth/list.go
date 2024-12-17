// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/auth/auth"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/printer"
	"intrinsic/tools/inctl/util/viperutil"
)

var (
	listParams *viper.Viper
)

var listCmd = &cobra.Command{
	Use:     "list",
	Aliases: []string{"ls"},
	Short:   "Lists available credentials",
	Long:    "Lists available credentials present for current user",
	Args:    cobra.NoArgs,
	RunE:    listCredentialsE,
}

func configListing(store *auth.Store) (*configListView, error) {
	configurations, err := store.ListConfigurations()
	if err != nil {
		return nil, fmt.Errorf("cannot list configurations: %w", err)
	}

	orgs, err := store.ListOrgs()
	if err != nil {
		return nil, fmt.Errorf("list orgs: %w", err)
	}

	projectName := listParams.GetString(orgutil.KeyProject)

	result := &configListView{Configurations: make(map[string][]string, len(configurations)), Orgs: make([]auth.OrgInfo, 0, len(orgs))}
	for _, config := range configurations {
		if projectName != "" && !strings.HasPrefix(config, projectName) {
			continue
		}
		tokens, err := store.GetConfiguration(config)
		if err != nil {
			// we are going to fail early if we encounter issue
			// we could consider be more defensive
			return nil, fmt.Errorf("cannot read %s: %w", config, err)
		}
		result.Configurations[config] = mapToKeysArray(tokens.Tokens)
	}

	for _, org := range orgs {
		orgInfo, err := store.ReadOrgInfo(org)
		if err != nil {
			continue
		}

		result.Orgs = append(result.Orgs, orgInfo)
	}

	return result, nil
}

func runListCmd(prtr printer.Printer) error {
	result, err := configListing(authStore)
	if err != nil {
		return fmt.Errorf("get configs: %w", err)
	}

	prtr.Print(result)
	return nil
}

func listCredentialsE(cmd *cobra.Command, _ []string) error {
	out, ok := printer.AsPrinter(cmd.OutOrStdout(), printer.TextOutputFormat)
	if !ok {
		return fmt.Errorf("invalid output configuration")
	}

	return runListCmd(out)
}

type configListView struct {
	Configurations map[string][]string `json:"configurations"`
	Orgs           []auth.OrgInfo      `json:"orgs"`
}

// String is not a typical implementation of fmt.Stringer but implementation
// of view object designed for human output, which strongly deviates from
// usual fmt.Stringer implementation.
func (c *configListView) String() string {
	result := new(strings.Builder)

	if len(c.Orgs) > 0 {
		result.WriteString("The following organizations can be used:\n")
		for _, org := range c.Orgs {
			result.WriteString("  ")
			result.WriteString(org.Organization)
			result.WriteString("\n")
		}
	}

	if len(c.Configurations) > 0 {
		result.WriteString("The following projects can be used:\n")
		for project, configs := range c.Configurations {
			result.WriteString(fmt.Sprintf("  %s: %s\n", project, strings.Join(configs, ", ")))
		}
	}

	return result.String()
}

func mapToKeysArray[K comparable, V any](in map[K]V) []K {
	result := make([]K, 0, len(in))
	for key := range in {
		result = append(result, key)
	}
	return result
}

func init() {
	authCmd.AddCommand(listCmd)

	flags := listCmd.Flags()

	// local user may have multiple accounts for single project
	flags.StringP(orgutil.KeyProject, keyProjectShort, "", "Show credentials for project starting with this prefix")

	listParams = viperutil.BindToViper(flags, viperutil.BindToListEnv(orgutil.KeyProject))
}
