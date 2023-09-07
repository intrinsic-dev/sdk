// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package version contains all commands related to versions
package version

import (
	"errors"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

const (
	// SDKVersionDefaultValue is a special value for flagSDKVersion below.
	SDKVersionDefaultValue = "unknown"
	// DevContainerVersionFilePath is the path to the dev container version file
	// which will only be present in the context of a dev container.
	devContainerVersionFilePath = "/etc/intrinsic/sdk.version"
)

var (
	// SDKVersion is the version of the used Intrinsic SDK
	// It can be changed by stamping at build time as follows:
	//
	//   Externally with Bazel (enabled by go_library.x_defs):
	//     bazel build/run
	//       --stamp
	//       --workspace_status_command="echo STABLE_SDK_VERSION intrinsic.platform.20221231.RC00"
	//       ...
	//   See https://github.com/bazelbuild/rules_go/blob/master/docs/go/core/defines_and_stamping.md#defines-and-stamping.
	SDKVersion string = SDKVersionDefaultValue
)

type versionInfo struct {
	InctlSDKVersion     string `json:"inctlVersion,omitempty"`
	DevContainerVersion string `json:"devContainerVersion,omitempty"`
}

// String prints the versionMessage in the case of --output=text.
func (msg *versionInfo) String() string {
	var result strings.Builder
	result.WriteString(fmt.Sprintf("Inctl version: %s", msg.InctlSDKVersion))

	if msg.DevContainerVersion != "" {
		result.WriteByte('\n')
		result.WriteString(fmt.Sprintf("Dev container version: %s", msg.DevContainerVersion))
	}

	return result.String()
}

type cmdParams struct {
	flagOutput                  string
	devContainerVersionFilePath string
}

// runVersionCmd implements the version command. It is the entry-point for
// unit tests and does not rely on any global state (e.g. global flag
// variables).
func runVersionCmd(params *cmdParams, stdout io.Writer) error {
	prtr, err := printer.NewPrinterWithWriter(params.flagOutput, stdout)
	if err != nil {
		return fmt.Errorf("creating printer: %w", err)
	}

	devContainerVersion := ""
	devContainerVersionBytes, err := os.ReadFile(params.devContainerVersionFilePath)
	if err == nil {
		devContainerVersion = string(devContainerVersionBytes)
	} else if !errors.Is(err, os.ErrNotExist) {
		// We recognized that the user is likely in a dev container (version file exists) but
		// cannot determine the version.
		devContainerVersion = "cannot determine"
	}

	prtr.Print(&versionInfo{
		InctlSDKVersion:     SDKVersion,
		DevContainerVersion: devContainerVersion,
	})

	return nil
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Displays Intrinsic SDK version",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		cmdParams := &cmdParams{
			flagOutput:                  root.FlagOutput,
			devContainerVersionFilePath: devContainerVersionFilePath,
		}
		return runVersionCmd(cmdParams, cmd.OutOrStdout())
	},
}

func init() {
	root.RootCmd.AddCommand(versionCmd)
}
