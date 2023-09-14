// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package release defines the skill release command which releases a skill to the catalog.
package release

import (
	"context"
	"fmt"
	"log"
	"strings"

	"github.com/google/go-containerregistry/pkg/authn"
	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	tagpb "intrinsic/assets/proto/tag_go_proto"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/imagetransfer"
	"intrinsic/skills/tools/skill/cmd/registry"
)

const (
	keyDocString                      = "doc_string"
	keyAllowSkillToSkillCommunication = "allow_skill_to_skill_communication"
)

var cmdFlags = cmdutil.NewCmdFlags()

// release puts the skill into the skill catalog. This version is the default
// version used by the command-line tool. It always releases the skill to the
// production 'live' environment.
//
// If the skill is already present in the catalog, this function will
// pass-through an AlreadyExists error from the skill catalog.
func release(ctx context.Context, req *skillcatalogpb.CreateSkillReleaseRequest, skillID string, address string, project string) error {
	log.Printf("Releasing skill %q to the skill catalog %q", skillID, address)

	ctx, dialerOpts, err := dialerutil.DialInfoCtx(ctx, dialerutil.DialInfoParams{
		Address:  address,
		CredName: project,
	})
	if err != nil {
		return fmt.Errorf("could not create connection options for the skill catalog service: %v", err)
	}

	conn, err := grpc.DialContext(ctx, address, *dialerOpts...)
	if err != nil {
		return fmt.Errorf("failed to create client connection: %v", err)
	}
	defer conn.Close()

	client := skillcataloggrpcpb.NewSkillCatalogClient(conn)
	_, err = client.CreateSkill(ctx, req)
	if err != nil {
		return fmt.Errorf("could not release the skill :%w", err)
	}
	log.Printf("Finished releasing the skill")
	return nil
}

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
		target := args[0]

		req := &skillcatalogpb.CreateSkillReleaseRequest{
			Vendor:       cmdFlags.GetFlagVendor(),
			Version:      cmdFlags.GetFlagVersion(),
			ReleaseNotes: cmdFlags.GetFlagReleaseNotes(),
			DocString:    cmdFlags.GetString(keyDocString),
		}

		dryRun := cmdFlags.GetFlagDryRun()

		skillID := ""

		targetType := cmdFlags.GetFlagReleaseType()
		registryAddr := cmdFlags.GetFlagRegistry()

		var transferer imagetransfer.Transferer
		if dryRun {
			transferer = imagetransfer.Readonly(remoteOpt())
		} else {
			transferer = imagetransfer.RemoteTransferer(remoteOpt())
		}
		authUser, authPwd := cmdFlags.GetFlagsRegistryAuthUserPassword()
		imgpb, installerParams, err := registry.PushSkill(target, registry.PushOptions{
			AuthUser:   authUser,
			AuthPwd:    authPwd,
			Registry:   registryAddr,
			Type:       targetType,
			Transferer: transferer,
		})
		if err != nil {
			return fmt.Errorf("could not push target %q to the container registry: %v", target, err)
		}
		skillID = installerParams.SkillID
		req.DeploymentType = &skillcatalogpb.CreateSkillReleaseRequest_Image{Image: imgpb}

		splitID := strings.Split(skillID, ".")
		packageName := ""
		if len(splitID) > 1 {
			packageName = strings.Join(splitID[:len(splitID)-1], ".")
		}
		skillName := splitID[len(splitID)-1]

		req.Name = skillName
		req.PackageName = packageName

		if cmdFlags.GetFlagDefault() {
			d := tagpb.Tag_TAG_DEFAULT
			req.Tag = &d
		}

		project := cmdFlags.GetFlagProject()

		if dryRun {
			log.Printf("Skipping release of skill %q to the skill catalog %q (dry-run)", skillID, project)
			return nil
		}
		// Release the skill to the skill catalog

		catalogAddress := fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", project)

		return release(cmd.Context(), req, skillID, catalogAddress, project)
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(releaseCmd)
	cmdFlags.SetCommand(releaseCmd)

	cmdFlags.AddFlagDefault()
	cmdFlags.AddFlagDryRun()
	cmdFlags.AddFlagProject()
	cmdFlags.AddFlagRegistry()
	cmdFlags.AddFlagsRegistryAuthUserPassword()
	cmdFlags.AddFlagReleaseNotes()
	cmdFlags.AddFlagReleaseType()
	cmdFlags.AddFlagVendor()
	cmdFlags.AddFlagVersion()

	cmdFlags.OptionalString(keyDocString, "", "Skill documentation.")
}
