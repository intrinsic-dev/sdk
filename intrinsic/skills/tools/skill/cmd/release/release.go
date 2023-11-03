// Copyright 2023 Intrinsic Innovation LLC

// Package release defines the skill release command which releases a skill to the catalog.
package release

import (
	"fmt"

	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"

	"github.com/google/go-containerregistry/pkg/authn"
	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/spf13/cobra"
)

const (
	keyDocString                      = "doc_string"
	keyAllowSkillToSkillCommunication = "allow_skill_to_skill_communication"
)

var cmdFlags = cmdutil.NewCmdFlags()

var (
	buildCommand    = "bazel"
	buildConfigArgs = []string{
		"-c", "opt",
	}
)

func remoteOpt() remote.Option {
	authUser, authPwd := cmdFlags.GetFlagsRegistryAuthUserPassword()
	if len(authUser) != 0 && len(authPwd) != 0 {
		return remote.WithAuth(authn.FromConfig(authn.AuthConfig{
			Username: authUser,
			Password: authPwd,
		}))
	}
	return remote.WithAuthFromKeychain(google.Keychain)
}

var releaseCmd = &cobra.Command{
	Use:   "release target",
	Short: "Release a skill",
	Example: `Build a skill, upload it to a container registry, and release to the skill catalog
$ inctl skill release --type=build //abc:skill.tar --registry=gcr.io/my-registry --vendor=abc --version="0.0.0" --default

Upload skill image to a container registry, and release to the skill catalog
$ inctl skill release --type=archive abc/skill.tar --registry=gcr.io/my-registry --vendor=abc --version="0.0.0" --default

Release a skill using an image that has already been pushed to the container registry
$ inctl skill release --type=image gcr.io/my-workcell/abc@sha256:20ab4f --vendor=abc --version="0.0.0" --default` +
		"",
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		return fmt.Errorf("unimplemented")
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(releaseCmd)
	cmdFlags.SetCommand(releaseCmd)

	cmdFlags.AddFlagDefault()
	cmdFlags.AddFlagDryRun()
	cmdFlags.AddFlagsProjectOrg()
	cmdFlags.AddFlagRegistry()
	cmdFlags.AddFlagsRegistryAuthUserPassword()
	cmdFlags.AddFlagReleaseNotes()
	cmdFlags.AddFlagReleaseType()
	cmdFlags.AddFlagVendor()
	cmdFlags.AddFlagVersion()
	cmdFlags.AddFlagManifestFile()
	cmdFlags.AddFlagManifestTarget()

	cmdFlags.OptionalString(keyDocString, "", "Skill documentation.")
}
