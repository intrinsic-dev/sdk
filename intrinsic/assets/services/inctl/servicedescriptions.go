// Copyright 2023 Intrinsic Innovation LLC

// Package servicedescriptions contains utils for commands that list released services.
package servicedescriptions

import (
	"fmt"
	"sort"
	"strings"

	acpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	"intrinsic/assets/idutils"
	atpb "intrinsic/assets/proto/asset_type_go_proto"
)

// Description has custom proto->json conversion to handle fields like the update timestamp.
type Description struct {
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

// Descriptions wraps the required data for the output of service list commands.
type Descriptions struct {
	Services []Description `json:"services"`
}

// FromCatalogServices creates a Descriptions instance from catalog.v1.Asset protos.
func FromCatalogServices(assets []*acpb.Asset) (*Descriptions, error) {
	out := Descriptions{Services: make([]Description, len(assets))}

	for i, asset := range assets {
		metadata := asset.GetMetadata()
		if metadata.GetAssetType() != atpb.AssetType_ASSET_TYPE_SERVICE {
			return nil, fmt.Errorf("assets list must only contain services, found %v", asset.GetMetadata().GetAssetType())
		}

		idVersion, err := idutils.IDVersionFromProto(metadata.GetIdVersion())
		if err != nil {
			return nil, err
		}
		ivp, err := idutils.NewIDVersionParts(idVersion)
		if err != nil {
			return nil, err
		}

		out.Services[i] = Description{
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

// IDVersionsString converts a Description to a string with one IDVersion per line.
func (sd Descriptions) IDVersionsString() string {
	lines := make([]string, len(sd.Services))
	for i, service := range sd.Services {
		lines[i] = fmt.Sprintf("%s", service.IDVersion)
	}
	sort.Strings(lines)
	return strings.Join(lines, "\n")
}
