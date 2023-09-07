// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package auth

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/auth/auth"
	"intrinsic/tools/inctl/util/viperutil"
)

const (
	keyNoBrowser = "no_browser"

	projectTokenURLFmt = "https://portal.intrinsic.ai/proxy/projects/%s/generate-keys"
	// We are going to use system defaults to ensure we open web-url correctly.
	// For dev container running via VS Code the sensible-browser redirects
	// call into code client from server to ensure URL is opened in valid
	// client browser.
	sensibleBrowser = "/usr/bin/sensible-browser"
)

var loginParams *viper.Viper

var loginCmd = &cobra.Command{
	Use:   "login",
	Short: "Logs in user into project",
	Long:  "Logs in user into project to allow interactions with solutions.",
	Args:  cobra.NoArgs,
	RunE:  loginCmdE,
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

func loginCmdE(cmd *cobra.Command, _ []string) (err error) {
	writer := cmd.OutOrStdout()
	projectName := loginParams.GetString(keyProject)
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
		authorizationURL := fmt.Sprintf(projectTokenURLFmt, projectName)
		fmt.Fprintf(writer, "Open URL in your browser to obtain authorization token: %s\n", authorizationURL)

		ignoreBrowser := loginParams.GetBool(keyNoBrowser)
		if !ignoreBrowser {
			_, _ = fmt.Fprintln(writer, "Attempting to open URL in your browser...")
			browser := exec.CommandContext(cmd.Context(), sensibleBrowser, authorizationURL)
			browser.Stdout = io.Discard
			browser.Stderr = io.Discard
			if err = browser.Start(); err != nil {
				fmt.Fprintf(writer, "Failed to open URL in your browser, please run command again with '--%s'.\n", keyNoBrowser)
				return fmt.Errorf("rerun with '--%s', got error %w", keyNoBrowser, err)
			}
		}
		fmt.Fprintf(writer, "\nPaste access token from website: ")

		apiKey, err = in.ReadString('\n')
		if err != nil {
			return fmt.Errorf("cannot read from input device: %w", err)
		}
		apiKey = strings.TrimSpace(apiKey) // normalizing the input
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
	flags.StringP(keyProject, keyProjectShort, "", "Name of the Google cloud project to authorize for")
	flags.Bool(keyNoBrowser, false, "Disables attempt to open login URL in browser automatically")
	flags.Bool(keyBatch, false, "Suppresses command prompts and assume Yes or default as an answer. Use with shell scripts.")

	loginParams = viperutil.BindToViper(flags, viperutil.BindToListEnv(keyProject))

	// This is to workaround Cobra not cooperating with Viper.
	if !loginParams.IsSet(keyProject) {
		_ = loginCmd.MarkFlagRequired(keyProject)
	}
}
