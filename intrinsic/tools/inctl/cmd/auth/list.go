// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/printer"
	"intrinsic/tools/inctl/util/viperutil"
)

var listParams *viper.Viper

var listCmd = &cobra.Command{
	Use:     "list",
	Aliases: []string{"ls"},
	Short:   "Lists available credentials",
	Long:    "Lists available credentials present for current user",
	Args:    cobra.NoArgs,
	RunE:    listCredentialsE,
}

func listCredentialsE(cmd *cobra.Command, _ []string) error {
	out, ok := printer.AsPrinter(cmd.OutOrStdout(), printer.TextOutputFormat)
	if !ok {
		return fmt.Errorf("invalid output configuration")
	}

	configurations, err := authStore.ListConfigurations()
	if err != nil {
		return fmt.Errorf("cannot list configurations: %w", err)
	}

	projectName := listParams.GetString(orgutil.KeyProject)

	result := &ConfigListView{Configurations: make(map[string][]string, len(configurations))}
	for _, config := range configurations {
		if projectName != "" && !strings.HasPrefix(config, projectName) {
			continue
		}
		tokens, err := authStore.GetConfiguration(config)
		if err != nil {
			// we are going to fail early if we encounter issue
			// we could consider be more defensive
			return fmt.Errorf("cannot read %s: %w", config, err)
		}
		result.Configurations[config] = mapToKeysArray(tokens.Tokens)
	}

	out.Print(result)
	return nil
}

func init() {
	authCmd.AddCommand(listCmd)

	flags := listCmd.Flags()

	// local user may have multiple accounts for single project
	flags.StringP(orgutil.KeyProject, keyProjectShort, "", "Show credentials for project starting with this prefix")

	listParams = viperutil.BindToViper(flags, viperutil.BindToListEnv(orgutil.KeyProject))

}

type ConfigListView struct {
	Configurations map[string][]string `json:"configurations"`
}

// String is not a typical implementation of fmt.Stringer but implementation
// of view object designed for human output, which strongly deviates from
// usual fmt.Stringer implementation.
func (c *ConfigListView) String() string {
	result := new(strings.Builder)
	if len(c.Configurations) > 0 {
		_, _ = fmt.Fprintln(result, "Available authorizations:")
		for key, config := range c.Configurations {
			_, _ = fmt.Fprintf(result, "  - %s: %s\n", key, strings.Join(config, ", "))
		}
	} else {
		_, _ = fmt.Fprintln(result, "No authorizations found")
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
