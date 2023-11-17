// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"context"
	"fmt"

	"github.com/spf13/cobra"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/util/printer"

	orgdiscoverygrpcpb "intrinsic/frontend/cloud/api/orgdiscovery_grpc_go_proto"
)

const updateCommandDesc = ""

var updateCmd = &cobra.Command{
	Use:   "update",
	Short: "Update available organizations and verify logins",
	Long:  updateCommandDesc,
	Args:  cobra.NoArgs,
	RunE:  updateCredentials,
}

func queryOrgs(ctx context.Context, project string) ([]auth.OrgInfo, error) {
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		CredName: project,
	})
	if err != nil {
		return []auth.OrgInfo{}, fmt.Errorf("failed to dial: %w", err)
	}
	defer conn.Close()

	client := orgdiscoverygrpcpb.NewOrganizationManagerServiceClient(conn)
	resp, err := client.ListOrganizations(ctx, &emptypb.Empty{})
	if err != nil {
		if code, ok := status.FromError(err); ok && code.Code() == codes.NotFound {
			fmt.Printf("Could not find the project for this token. Please restart the login process and make sure to provide the exact key shown by the portal.\n")
			return []auth.OrgInfo{}, fmt.Errorf("validate token")
		}
		return []auth.OrgInfo{}, fmt.Errorf("request to list orgs failed: %w", err)
	}

	ret := []auth.OrgInfo{}
	for _, org := range resp.GetOrganizations() {
		info := auth.OrgInfo{
			Project:      org.GetProject(),
			Organization: org.GetName(),
		}
		ret = append(ret, info)
	}

	return ret, nil
}

func updateCredentials(cmd *cobra.Command, args []string) error {
	store := auth.NewStore()
	projects, err := store.ListConfigurations()
	if err != nil {
		return fmt.Errorf("get projects: %w", err)
	}

	infos := map[string][]auth.OrgInfo{}

	for _, project := range projects {
		orgs, err := queryOrgs(cmd.Context(), project)
		if err != nil {
			fmt.Printf("Failed to update project %q: %v\n", project, err)
			continue
		}

		for _, org := range orgs {
			infos[org.Organization] = append(infos[org.Organization], org)
		}
	}

	for _, orgs := range infos {
		if len(orgs) > 1 {
			for _, org := range orgs {
				org.Organization = fmt.Sprintf("%s@%s", org.Organization, org.Project)
				store.WriteOrgInfo(&org)
			}
		} else {
			store.WriteOrgInfo(&orgs[0])
		}
	}

	prtr, ok := printer.AsPrinter(cmd.OutOrStdout(), printer.TextOutputFormat)
	if !ok {
		return fmt.Errorf("invalid output configuration")
	}
	return runListCmd(prtr)
}

func init() {
	authCmd.AddCommand(updateCmd)
}
