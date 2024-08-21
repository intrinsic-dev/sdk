// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"net/url"
	"os"
	"os/exec"
	"slices"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"golang.org/x/exp/maps"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	accdiscoverv1grpcpb "intrinsic/kubernetes/accounts/service/api/discoveryv1api_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	keyNoBrowser = "no_browser"

	orgTokenURLFmt     = "https://%s/o/%s/generate-keys"
	projectTokenURLFmt = "https://%s/project/%s/generate-keys"
	// We are going to use system defaults to ensure we open web-url correctly.
	// For dev container running via VS Code the sensible-browser redirects
	// call into code client from server to ensure URL is opened in valid
	// client browser.
	sensibleBrowser = "/usr/bin/sensible-browser"
)

// Exposed for testing
var (
	queryProjects   = queryProjectsForAPIKey
	flowstateDomain = map[string]string{
		orgutil.ProdEnvironment:    "flowstate.intrinsic.ai",
		orgutil.StagingEnvironment: "flowstate-qa.intrinsic.ai",
		orgutil.DevEnvironment:     "flowstate-dev.intrinsic.ai",
	}
)

var loginParams *viper.Viper

var loginCmd = &cobra.Command{
	Use:   "login",
	Short: "Logs in user into Flowstate",
	Long:  "Logs in user into Flowstate to allow interactions with solutions.",
	Args:  cobra.NoArgs,
	RunE:  loginCmdE,

	PersistentPreRunE: func(_ *cobra.Command, _ []string) error {
		if loginParams.GetString(orgutil.KeyProject) == "" && loginParams.GetString(orgutil.KeyOrganization) == "" {
			return fmt.Errorf("at least one of --project or --org needs to be set")
		}
		if err := orgutil.ValidateEnvironment(loginParams); err != nil {
			return err
		}

		return nil
	},
}

func readAPIKeyFromPipe(reader *bufio.Reader) (string, error) {
	fi, _ := os.Stdin.Stat()
	// Check if input comes from pipe. Taken from
	// https://www.socketloop.com/tutorials/golang-check-if-os-stdin-input-data-is-piped-or-from-terminal
	if (fi.Mode() & os.ModeCharDevice) == 0 {
		bytes, _, err := reader.ReadLine()
		if err != nil {
			return "", err
		}

		return strings.TrimSpace(string(bytes)), nil
	}
	return "", nil
}

var portalToAccounts = map[string]string{
	"portal.intrinsic.ai":        "accounts.intrinsic.ai",
	"portal-qa.intrinsic.ai":     "accounts-qa.intrinsic.ai",
	"portal-dev.intrinsic.ai":    "accounts-dev.intrinsic.ai",
	"flowstate.intrinsic.ai":     "accounts.intrinsic.ai",
	"flowstate-qa.intrinsic.ai":  "accounts-qa.intrinsic.ai",
	"flowstate-dev.intrinsic.ai": "accounts-dev.intrinsic.ai",
}

func queryForAPIKey(ctx context.Context, writer io.Writer, in *bufio.Reader, organization, project string) (string, error) {
	portal := flowstateDomain[loginParams.GetString(orgutil.KeyEnvironment)]
	if portal == "" {
		return "", fmt.Errorf("unknown environment %q", loginParams.GetString(orgutil.KeyEnvironment))
	}
	authorizationURL := fmt.Sprintf(projectTokenURLFmt, portal, project)
	if organization != "" {
		authorizationURL = fmt.Sprintf(orgTokenURLFmt, portal, url.PathEscape(organization))
	}
	fmt.Fprintf(writer, "Open URL in your browser to obtain authorization token: %s\n", authorizationURL)

	ignoreBrowser := loginParams.GetBool(keyNoBrowser)
	if !ignoreBrowser {
		_, _ = fmt.Fprintln(writer, "Attempting to open URL in your browser...")
		browser := exec.CommandContext(ctx, sensibleBrowser, authorizationURL)
		browser.Stdout = io.Discard
		browser.Stderr = io.Discard
		if err := browser.Start(); err != nil {
			fmt.Fprintf(writer, "Failed to open URL in your browser, please run command again with '--%s'.\n", keyNoBrowser)
			return "", fmt.Errorf("rerun with '--%s', got error %w", keyNoBrowser, err)
		}
	}
	fmt.Fprintf(writer, "\nPaste access token from website: ")

	apiKey, err := in.ReadString('\n')
	if err != nil {
		return "", fmt.Errorf("cannot read from input device: %w", err)
	}
	return strings.TrimSpace(apiKey), nil
}

// queryProjectsForAPIKey discovers the projects the given API key has access to.
// If optionalOrg is set, it will be used as a filter to only return projects the given organization
// is part of.
func queryProjectsForAPIKey(ctx context.Context, apiKey string, optionalOrg string) ([]string, error) {
	portal := flowstateDomain[loginParams.GetString(orgutil.KeyEnvironment)]
	if portal == "" {
		return nil, fmt.Errorf("unknown environment %q", loginParams.GetString(orgutil.KeyEnvironment))
	}
	address := fmt.Sprintf("dns:///%s:443", portalToAccounts[portal])
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		Address:   address,
		CredToken: apiKey,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to dial: %w", err)
	}
	defer conn.Close()

	client := accdiscoverv1grpcpb.NewAccountsDiscoveryServiceClient(conn)
	resp, err := client.ListOrganizations(ctx, &emptypb.Empty{})
	if err != nil {
		fmt.Println("Could not find the project for this token. Please restart the login process and make sure to provide the exact key shown by the portal.")
		return nil, fmt.Errorf("failed to list organizations: %w", err)
	}
	// multiple organizations are fine, but they must be all on the same project
	orgs := resp.GetOrganizations()
	projects := map[string]struct{}{}
	for _, org := range orgs {
		// filter by org if specified
		if optionalOrg != "" && optionalOrg != org.GetName() {
			continue
		}
		projects[org.GetProject()] = struct{}{}
	}
	return maps.Keys(projects), nil
}

func loginCmdE(cmd *cobra.Command, _ []string) (err error) {
	writer := cmd.OutOrStdout()
	projectName := loginParams.GetString(orgutil.KeyProject)
	orgName := loginParams.GetString(orgutil.KeyOrganization)
	in := bufio.NewReader(cmd.InOrStdin())
	// In the future multiple aliases should be supported for one project.
	alias := auth.AliasDefaultToken
	isBatch := loginParams.GetBool(keyBatch)

	apiKey, err := readAPIKeyFromPipe(in)
	if err != nil {
		return err
	}

	if projectName == "" {
		parts := strings.Split(orgName, "@")
		if len(parts) == 2 {
			projectName = parts[1]
		}
	}

	if apiKey != "" && isBatch {
		_, err = authStore.WriteConfiguration(&auth.ProjectConfiguration{
			Name:   projectName,
			Tokens: map[string]*auth.ProjectToken{alias: &auth.ProjectToken{APIKey: apiKey}},
		})
		return err
	}

	if apiKey == "" {
		apiKey, err = queryForAPIKey(cmd.Context(), writer, in, orgName, projectName)
		if err != nil {
			return err
		}
	}

	// If we are passed an org, we don't know the project yet
	if projectName == "" {
		// orgName is always pure here (without @) because projectName is set above if org includes "@".
		projects, err := queryProjects(cmd.Context(), apiKey, orgName)
		if err != nil {
			return fmt.Errorf("query project: %w", err)
		}
		if len(projects) == 0 {
			return fmt.Errorf("no project found for API key")
		}
		if len(projects) > 1 {
			slices.Sort(projects)
			return fmt.Errorf("multiple projects found for API key (and org %q): %+v", orgName, projects)
		}
		// exactly one found
		projectName = projects[0]
	}
	if orgName != "" {
		if err := authStore.WriteOrgInfo(&auth.OrgInfo{Organization: orgName, Project: projectName}); err != nil {
			return fmt.Errorf("store org info: %w", err)
		}
	}

	var config *auth.ProjectConfiguration
	if authStore.HasConfiguration(projectName) {
		if config, err = authStore.GetConfiguration(projectName); err != nil {
			return fmt.Errorf("cannot load '%s' configuration: %w", projectName, err)
		}
	} else {
		config = auth.NewConfiguration(projectName)
	}

	config, err = config.SetCredentials(alias, apiKey)
	if err != nil {
		return fmt.Errorf("aborting, invalid credentials: %w", err)
	}

	_, err = authStore.WriteConfiguration(config)

	return err
}

func init() {
	authCmd.AddCommand(loginCmd)

	flags := loginCmd.Flags()
	// we will use viper to fetch data, we do not need local variables
	flags.StringP(orgutil.KeyProject, keyProjectShort, "", "Name of the Google cloud project to authorize for")
	flags.StringP(orgutil.KeyOrganization, "", "", "Name of the Intrinsic organization to authorize for")
	flags.Bool(keyNoBrowser, false, "Disables attempt to open login URL in browser automatically")
	flags.Bool(keyBatch, false, "Suppresses command prompts and assume Yes or default as an answer. Use with shell scripts.")
	flags.StringP(orgutil.KeyEnvironment, "", orgutil.ProdEnvironment, fmt.Sprintf("Auth environment to use. This should be one of %q, %q or %q. %q is used by default. See http://go/intrinsic-users#environments for the compatible environment corresponding to a cloud project.", orgutil.ProdEnvironment, orgutil.StagingEnvironment, orgutil.DevEnvironment, orgutil.ProdEnvironment))
	flags.MarkHidden(orgutil.KeyEnvironment)
	flags.MarkHidden(orgutil.KeyProject)

	loginParams = viperutil.BindToViper(flags, viperutil.BindToListEnv(orgutil.KeyProject, orgutil.KeyOrganization, orgutil.KeyEnvironment))
}
