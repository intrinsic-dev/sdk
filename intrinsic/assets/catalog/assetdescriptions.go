// Copyright 2023 Intrinsic Innovation LLC

// Package assetdescriptions contains utils for commands that list released assets.
package assetdescriptions

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"

	acpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	"intrinsic/assets/idutils"
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

// Descriptions wraps the required data for the output of asset list commands.
type Descriptions struct {
	Assets []Description `json:"assets"`
}

// IDVersionsStringView wraps a Descriptions and defines String() which returns
// one asset IDVersion per line. It also defines MarshalJSON() which just
// marshals the wrapped Descriptions (unlike String this includes all fields).
type IDVersionsStringView struct {
	Descriptions *Descriptions
}

// FromCatalogAssets creates a Descriptions instance from catalog.v1.Asset protos.
func FromCatalogAssets(assets []*acpb.Asset) (*Descriptions, error) {
	out := Descriptions{Assets: make([]Description, len(assets))}

	for i, asset := range assets {
		metadata := asset.GetMetadata()
		idVersion, err := idutils.IDVersionFromProto(metadata.GetIdVersion())
		if err != nil {
			return nil, err
		}
		ivp, err := idutils.NewIDVersionParts(idVersion)
		if err != nil {
			return nil, err
		}

		out.Assets[i] = Description{
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

// MarshalJSON marshals the underlying asset descriptions.
func (v IDVersionsStringView) MarshalJSON() ([]byte, error) {
	return json.Marshal(v.Descriptions)
}

// String returns a string with one IDVersion per line.
func (v IDVersionsStringView) String() string {
	var lines []string
	for _, asset := range v.Descriptions.Assets {
		lines = append(lines, fmt.Sprintf("%s", asset.IDVersion))
	}
	sort.Strings(lines)
	return strings.Join(lines, "\n")
}
