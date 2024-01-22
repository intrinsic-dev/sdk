// Copyright 2023 Intrinsic Innovation LLC

// Package list defines the skill list command which lists skills in a registry.
package list

import (
	"context"
	"fmt"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	"intrinsic/assets/cmdutils"
	skillregistrygrpcpb "intrinsic/skills/proto/skill_registry_go_grpc_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/listutil"
	"intrinsic/skills/tools/skill/cmd/skillid"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

const (
	keyFilter = "filter"

	sideloadedFilter = "sideloaded"
	releasedFilter   = "released"
)

var (
	cmdFlags = cmdutils.NewCmdFlags()

	filterOptions = []string{sideloadedFilter, releasedFilter}
)

type listSkillsParams struct {
	cluster     string
	filter      string
	printer     printer.Printer
	projectName string
	orgName     string
	serverAddr  string
}

func listSkills(ctx context.Context, params *listSkillsParams) error {
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		Address:  params.serverAddr,
		Cluster:  params.cluster,
		CredName: params.projectName,
		CredOrg:  params.orgName,
	})
	if err != nil {
		return fmt.Errorf("failed to create client connection: %v", err)
	}
	defer conn.Close()

	client := skillregistrygrpcpb.NewSkillRegistryClient(conn)
	resp, err := client.GetSkills(ctx, &emptypb.Empty{})
	if err != nil {
		return fmt.Errorf("could not list skills: %w", err)
	}

	skills := listutil.SkillDescriptionsFromSkills(resp.GetSkills())
	filteredSkills := applyFilter(skills, params.filter)
	params.printer.Print(filteredSkills)

	return nil
}

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List skills that are loaded into a solution.",
	Example: `List skills of a running solution (solution id, not display name)
$ inctl skill list --project my-project --solution my-solution-id

	To find a running solution's id, run:
	$ inctl solution list --project my-project --filter "running_on_hw,running_in_sim" --output json

Set the cluster on which the solution is running
$ inctl skill list --project my-project --cluster my-cluster
`,
	Args: cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		project := cmdFlags.GetFlagProject()
		org := cmdFlags.GetFlagOrganization()
		cluster, solution, err := cmdFlags.GetFlagsListClusterSolution()
		if err != nil {
			return err
		}

		if solution != "" {
			ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
				CredName: project,
				CredOrg:  org,
			})
			if err != nil {
				return errors.Wrapf(err, "could not create connection")
			}
			defer conn.Close()

			cluster, err = solutionutil.GetClusterNameFromSolution(ctx, conn, solution)
			if err != nil {
				return errors.Wrapf(err, "could not resolve solution to cluster")
			}
		}
		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}

		err = listSkills(cmd.Context(), &listSkillsParams{
			cluster:     cluster,
			filter:      cmdFlags.GetString(keyFilter),
			printer:     prtr,
			projectName: project,
			orgName:     org,
		})
		if err != nil {
			return err
		}

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listCmd)
	cmdFlags.SetCommand(listCmd)

	cmdFlags.AddFlagsListClusterSolution("skill")
	cmdFlags.AddFlagsProjectOrg()

	cmdFlags.OptionalString(keyFilter, "", fmt.Sprintf("Filter skills by the way they where loaded into the solution. One of: %s.", strings.Join(filterOptions, ", ")))
}

func applyFilter(skills *listutil.SkillDescriptions, filter string) *listutil.SkillDescriptions {
	if filter == "" {
		return skills
	}

	filteredSkills := listutil.SkillDescriptions{Skills: []listutil.SkillDescription{}}
	for _, skill := range skills.Skills {
		if filter == sideloadedFilter && skillid.IsSideloaded(skill.IDVersion) ||
			filter == releasedFilter && !skillid.IsSideloaded(skill.IDVersion) {
			filteredSkills.Skills = append(filteredSkills.Skills, skill)
		}
	}
	return &filteredSkills
}
