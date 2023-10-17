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
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	projectdiscoverygrpcpb "intrinsic/frontend/cloud/api/projectdiscovery_grpc_go_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	keyNoBrowser = "no_browser"

	orgTokenURLFmt     = "https://%s/o/%s/generate-keys"
	projectTokenURLFmt = "https://%s/proxy/projects/%s/generate-keys"
	// We are going to use system defaults to ensure we open web-url correctly.
	// For dev container running via VS Code the sensible-browser redirects
	// call into code client from server to ensure URL is opened in valid
	// client browser.
	sensibleBrowser = "/usr/bin/sensible-browser"
)

// Exposed for testing
var (
	queryProject = queryProjectForAPIKey
)

var loginParams *viper.Viper

var loginCmd = &cobra.Command{
	Use:   "login",
	Short: "Logs in user into project",
	Long:  "Logs in user into project to allow interactions with solutions.",
	Args:  cobra.NoArgs,
	RunE:  loginCmdE,

	PersistentPreRunE: func(_ *cobra.Command, _ []string) error {
		if loginParams.GetString(orgutil.KeyProject) == "" && loginParams.GetString(orgutil.KeyOrganization) == "" {
			return fmt.Errorf("at least one of --project or --org needs to be set")
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

func queryForAPIKey(ctx context.Context, writer io.Writer, in *bufio.Reader, organization, project string) (string, error) {
	portal := loginParams.GetString(keyPortal)
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

func queryProjectForAPIKey(ctx context.Context, apiKey string) (string, error) {
	portal := loginParams.GetString(keyPortal)
	address := fmt.Sprintf("dns:///%s:443", portal)
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		Address:   address,
		CredToken: apiKey,
	})
	if err != nil {
		return "", fmt.Errorf("failed to dial: %w", err)
	}
	defer conn.Close()

	client := projectdiscoverygrpcpb.NewProjectDiscoveryServiceClient(conn)
	resp, err := client.GetProject(ctx, &emptypb.Empty{})
	if err != nil {
		if code, ok := status.FromError(err); ok && code.Code() == codes.NotFound {
			fmt.Printf("Could not find the project for this token. Please restart the login process and make sure to provide the exact key shown by the portal.\n")
			return "", fmt.Errorf("validate token")
		}
		return "", fmt.Errorf("request to list clusters failed: %w", err)
	}

	return resp.GetProject(), nil
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
		projectName, err = queryProject(cmd.Context(), apiKey)
		if err != nil {
			return err
		}
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

	if config.HasCredentials(alias) {
		fmt.Fprintf(writer, "Key for project %s already exists. Do you want to override it? [y/N]: ", projectName)
		response, err := in.ReadString('\n')
		if err != nil {
			return fmt.Errorf("cannot read from input device: %w", err)
		}
		response = strings.TrimSpace(response)
		if len(response) <= 0 || strings.ToLower(response[0:1]) != "y" {
			return fmt.Errorf("aborting per user request")
		}
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
	flags.StringP(keyPortal, "", "portal.intrinsic.ai", "Hostname of the intrinsic portal to authenticate with.")
	flags.MarkHidden(keyPortal)

	loginParams = viperutil.BindToViper(flags, viperutil.BindToListEnv(orgutil.KeyProject, orgutil.KeyOrganization))
}
