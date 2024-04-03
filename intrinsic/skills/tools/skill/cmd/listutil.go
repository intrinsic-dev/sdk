// Copyright 2023 Intrinsic Innovation LLC

// Package listutil contains utils for commands that list released skills.
package listutil

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"
	"strings"

	"intrinsic/assets/idutils"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	spb "intrinsic/skills/proto/skills_go_proto"
)

// SkillDescription has custom proto->json conversion to handle fields like the update timestamp.
type SkillDescription struct {
	Name         string `json:"name,omitempty"`
	Vendor       string `json:"vendor,omitempty"`
	PackageName  string `json:"packageName,omitempty"`
	Version      string `json:"version,omitempty"`
	UpdateTime   string `json:"updateTime,omitempty"`
	ID           string `json:"id,omitempty"`
	IDVersion    string `json:"idVersion,omitempty"`
	ReleaseNotes string `json:"releaseNotes,omitempty"`
	Description  string `json:"description,omitempty"`
}

// SkillDescriptions wraps the required data for the output of skill list commands.
type SkillDescriptions struct {
	Skills []SkillDescription `json:"skills"`
}

// SkillDescriptionsFromCatalogSkills creates a SkillDescriptions instance from catalog.Skill protos
func SkillDescriptionsFromCatalogSkills(skills []*skillcatalogpb.Skill) (*SkillDescriptions, error) {
	out := SkillDescriptions{Skills: make([]SkillDescription, len(skills))}

	for i, skill := range skills {
		metadata := skill.GetMetadata()
		idVersion, err := idutils.IDVersionFromProto(metadata.GetIdVersion())
		if err != nil {
			return nil, err
		}
		ivp, err := idutils.NewIDVersionParts(idVersion)
		if err != nil {
			return nil, err
		}

		out.Skills[i] = SkillDescription{
			Name:         ivp.Name(),
			Vendor:       metadata.GetVendor().GetDisplayName(),
			PackageName:  ivp.Package(),
			Version:      ivp.Version(),
			UpdateTime:   metadata.GetUpdateTime().AsTime().String(),
			ID:           ivp.ID(),
			IDVersion:    idVersion,
			ReleaseNotes: metadata.GetReleaseNotes(),
			Description:  metadata.GetDocumentation().GetDescription(),
		}
	}

	return &out, nil
}

// SkillDescriptionsFromSkills creates a SkillDescriptions instance from Skill protos
func SkillDescriptionsFromSkills(skills []*spb.Skill) *SkillDescriptions {
	out := SkillDescriptions{Skills: make([]SkillDescription, len(skills))}

	for i, skill := range skills {
		out.Skills[i] = SkillDescription{
			Name:        skill.GetSkillName(),
			PackageName: skill.GetPackageName(),
			ID:          skill.GetId(),
			IDVersion:   skill.GetIdVersion(),
			Description: skill.GetDescription(),
		}
	}

	return &out
}

// MarshalJSON converts a SkillDescription to a byte slice.
func (sd SkillDescriptions) MarshalJSON() ([]byte, error) {
	return json.Marshal(struct {
		Skills []SkillDescription `json:"skills"`
	}{Skills: sd.Skills})
}

// String converts a SkillDescription to a string
func (sd SkillDescriptions) String() string {
	lines := []string{}
	for _, skill := range sd.Skills {
		lines = append(lines, fmt.Sprintf("%s", skill.IDVersion))
	}
	sort.Strings(lines)
	return strings.Join(lines, "\n")
}

type clientWrapper struct {
	client skillcataloggrpcpb.SkillCatalogClient
}

type skillLister interface {
	listSkills(ctx context.Context, req *skillcatalogpb.ListSkillsRequest) (*skillcatalogpb.ListSkillsResponse, error)
}

func (c clientWrapper) listSkills(ctx context.Context, req *skillcatalogpb.ListSkillsRequest) (*skillcatalogpb.ListSkillsResponse, error) {
	return c.client.ListSkills(ctx, req)
}

func listSkillsPaginated(ctx context.Context, lister skillLister, req *skillcatalogpb.ListSkillsRequest) ([]*skillcatalogpb.Skill, error) {
	nextPageToken := req.GetPageToken()
	skills := []*skillcatalogpb.Skill{}
	for {
		resp, err := lister.listSkills(ctx, &skillcatalogpb.ListSkillsRequest{
			View:         req.GetView(),
			PageToken:    nextPageToken,
			PageSize:     req.GetPageSize(),
			StrictFilter: req.GetStrictFilter()})
		if err != nil {
			return nil, fmt.Errorf("could not list skills: %w", err)
		}
		skills = append(skills, resp.GetSkills()...)
		nextPageToken = resp.GetNextPageToken()
		if nextPageToken == "" {
			break
		}
	}
	return skills, nil
}

// ListWithCatalogClient lists all skills by pagination
func ListWithCatalogClient(ctx context.Context, client skillcataloggrpcpb.SkillCatalogClient, req *skillcatalogpb.ListSkillsRequest) ([]*skillcatalogpb.Skill, error) {
	clientWrapper := clientWrapper{client}
	return listSkillsPaginated(ctx, clientWrapper, req)
}
