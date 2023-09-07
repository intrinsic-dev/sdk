// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package list defines the skill list command which lists skills in a registry.
package list

import (
	"context"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	skillregistrygrpcpb "intrinsic/skills/proto/skill_registry_go_grpc_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd/cmd"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/listutil"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

const (
	keyAddress = "address"
	keyCluster = "cluster"
	keyFilter  = "filter"

	sideloadedFilter = "sideloaded"
	releasedFilter   = "released"
)

var (
	filterOptions = []string{sideloadedFilter, releasedFilter}

	flagAddress  string
	flagCluster  string
	flagSolution string
	flagFilter   string
)

type listSkillsParams struct {
	cluster     string
	filter      string
	printer     printer.Printer
	projectName string
	serverAddr  string
}

func listSkills(ctx context.Context, params *listSkillsParams) error {
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		Address:  params.serverAddr,
		Cluster:  params.cluster,
		CredName: params.projectName,
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
$	inctl skill list --project my-project --solution my-solution-id

Set the cluster on which the solution is running
$	inctl skill list --project my-project --cluster my-cluster
`,
	Args: cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		projectName := viper.GetString(skillCmd.KeyProject)
		serverAddr := "dns:///www.endpoints." + projectName + ".cloud.goog:443"

		if flagCluster == "" && flagSolution == "" {
			return fmt.Errorf("One of `--%s` or `--%s` needs to be set", keyCluster, skillCmd.KeySolution)
		}

		cluster := flagCluster

		if flagSolution != "" {
			ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
				Address:  serverAddr,
				CredName: projectName,
			})
			if err != nil {
				return fmt.Errorf("could not create connection: %v", err)
			}
			defer conn.Close()

			cluster, err = solutionutil.GetClusterNameFromSolution(
				ctx,
				conn,
				flagSolution,
			)
			if err != nil {
				return fmt.Errorf("could not resolve solution to cluster: %s", err)
			}
		}
		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}

		err = listSkills(cmd.Context(), &listSkillsParams{
			cluster:     cluster,
			filter:      flagFilter,
			printer:     prtr,
			projectName: projectName,
			serverAddr:  serverAddr,
		})
		if err != nil {
			return err
		}

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listCmd)

	if viper.GetString(skillCmd.KeyProject) == "" {
		listCmd.MarkPersistentFlagRequired(skillCmd.KeyProject)
	}
	listCmd.Flags().StringVar(&flagCluster, keyCluster, "", "Defines the cluster from which the skills"+
		" should be read.")
	listCmd.Flags().StringVar(&flagSolution, skillCmd.KeySolution, "", "The solution from which the "+
		"skills should be listed. Needs to run on a cluster.")
	listCmd.Flags().StringVar(&flagFilter, keyFilter, "", fmt.Sprintf("Filter skills by the way they "+
		"where loaded into the solution. One of %s", strings.Join(filterOptions, ", ")))

	// A solution will be resolved internally to the cluster it is running on.
	listCmd.MarkFlagsMutuallyExclusive(skillCmd.KeySolution, keyCluster)
}

// skills get a specific prefix when sideloaded via inctl.
// This method checks if the skill id version string contains this prefix.
func isSideloaded(skillIDversion string) bool {
	return strings.Contains(skillIDversion, skillCmd.SideloadedSkillPrefix)
}

func applyFilter(skills *listutil.SkillDescriptions, filter string) *listutil.SkillDescriptions {
	if filter == "" {
		return skills
	}

	filteredSkills := listutil.SkillDescriptions{Skills: []listutil.SkillDescription{}}
	for _, skill := range skills.Skills {
		if filter == sideloadedFilter && isSideloaded(skill.IDVersion) ||
			filter == releasedFilter && !isSideloaded(skill.IDVersion) {
			filteredSkills.Skills = append(filteredSkills.Skills, skill)
		}
	}
	return &filteredSkills
}
