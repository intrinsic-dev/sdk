// Copyright 2023 Intrinsic Innovation LLC

// Package release defines the command that releases skills to the catalog.
package release

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
)

const (
	keyDescription = "description"
)

var cmdFlags = cmdutil.NewCmdFlags()

var (
	buildCommand    = "bazel"
	buildConfigArgs = []string{
		"-c", "opt",
	}
)

var releaseExamples = strings.Join(
	[]string{
		`Build a skill then upload and release it to the skill catalog:
		  $ inctl skill release --type=build //abc:skill.tar ...`,
		`Upload and release a skill image to the skill catalog:
		  $ inctl skill release --type=archive /path/to/skill.tar ...`,
	},
	"\n\n",
)

var releaseCmd = &cobra.Command{
	Use:     "release target",
	Short:   "Release a skill",
	Example: releaseExamples,
	Args:    cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		return fmt.Errorf("unimplemented")
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(releaseCmd)
	cmdFlags.SetCommand(releaseCmd)

	cmdFlags.AddFlagDefault("skill")
	cmdFlags.AddFlagDryRun()
	cmdFlags.AddFlagManifestFile()
	cmdFlags.AddFlagManifestTarget()
	cmdFlags.AddFlagReleaseNotes("skill")
	cmdFlags.AddFlagSkillReleaseType()
	cmdFlags.AddFlagVendor("skill")
	cmdFlags.AddFlagVersion("skill")

	cmdFlags.OptionalString(keyDescription, "", "A description of the skill.")
}
