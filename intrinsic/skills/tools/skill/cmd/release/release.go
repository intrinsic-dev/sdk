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
	"github.com/spf13/viper"
	"google.golang.org/grpc"
	tagpb "intrinsic/assets/proto/tag_go_proto"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd/cmd"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/imagetransfer"
	"intrinsic/skills/tools/skill/cmd/registry"
)

var (
	flagAuthPassword   string
	flagAuthUser       string
	flagCatalogAddress string
	flagRegistry       string
	flagType           string

	flagDocString    string
	flagReleaseNotes string
	flagVendor       string
	flagVersion      string
	flagDefault      bool
	flagDryRun       bool
)

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
		return fmt.Errorf("could not release the skill: %v", err)
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
	if len(flagAuthUser) != 0 && len(flagAuthPassword) != 0 {
		return remote.WithAuth(authn.FromConfig(authn.AuthConfig{
			Username: flagAuthUser,
			Password: flagAuthPassword,
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
			Vendor:       flagVendor,
			Version:      flagVersion,
			ReleaseNotes: flagReleaseNotes,
			DocString:    flagDocString,
		}

		skillID := ""

		var transferer imagetransfer.Transferer
		if flagDryRun {
			transferer = imagetransfer.Readonly(remoteOpt())
		} else {
			transferer = imagetransfer.RemoteTransferer(remoteOpt())
		}
		imgpb, installerParams, err := registry.PushSkill(target, registry.PushOptions{
			AuthUser:   flagAuthUser,
			AuthPwd:    flagAuthPassword,
			Registry:   flagRegistry,
			Type:       flagType,
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

		if flagDefault {
			d := tagpb.Tag_TAG_DEFAULT
			req.Tag = &d
		}

		project := viper.GetString(skillCmd.KeyProject)

		if flagDryRun {
			log.Printf("Skipping release of skill %q to the skill catalog %q (dry-run)", skillID, project)
			return nil
		}
		// Release the skill to the skill catalog

		var catalogAddress string
		if flagCatalogAddress != "" {
			catalogAddress = flagCatalogAddress
		} else {
			catalogAddress = fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", project)
		}

		return release(cmd.Context(), req, skillID, catalogAddress, project)
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(releaseCmd)

	f := releaseCmd.PersistentFlags()
	f.StringVar(&flagAuthUser, "auth_user", "", "(optional) The username used to access the private skill registry.")
	f.StringVar(&flagAuthPassword, "auth_password", "", "(optional) The password used to authenticate private skill registry access.")
	f.StringVar(&flagRegistry, "registry", "", "The container registry. This option is ignored when --type=image.")
	f.StringVar(&flagType, "type", "", `(required) The target's type {"build","archive","image"`+
		`}:
  "build" expects a build target that creates a skill image.
  "archive" expects a file path pointing to an already-built image.
  "image" expects a container image name.`+
		"",
	)

	f.StringVar(&flagDocString, "doc_string", "", "Skill documentation.")
	f.StringVar(&flagReleaseNotes, "release_notes", "", "Release notes.")
	f.StringVar(&flagVendor, "vendor", "", "(required) Skill vendor.")
	f.StringVar(&flagVersion, "version", "", "(required) Version for this skill release in sem-ver format.")
	f.BoolVar(&flagDefault, "default", false, "Whether this version of the skill should be tagged as default.")
	f.BoolVar(&flagDryRun, "dry_run", false, "Dry-run the release by performing validation, but not calling the catalog.")

	releaseCmd.MarkPersistentFlagRequired("type")
	releaseCmd.MarkPersistentFlagRequired("vendor")
	releaseCmd.MarkPersistentFlagRequired("version")
	releaseCmd.MarkFlagsRequiredTogether("auth_user", "auth_password")

	if viper.GetString(skillCmd.KeyProject) == "" {
		releaseCmd.MarkPersistentFlagRequired(skillCmd.KeyProject)
	}
}
