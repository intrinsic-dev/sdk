// Copyright 2023 Intrinsic Innovation LLC

// Package typeutils provides utilities for asset types.
package typeutils

import (
	"regexp"
	"strings"

	"golang.org/x/exp/slices"

	atypepb "intrinsic/assets/proto/asset_type_go_proto"
)

var (
	customAssetTypeToName = map[atypepb.AssetType]string{
		atypepb.AssetType_ASSET_TYPE_UNSPECIFIED: "asset",
	}

	regexEnumName             = regexp.MustCompile("ASSET_TYPE_(?P<asset_type>[A-Za-z0-9_]+)$")
	regexEnumNameGroups       = regexEnumName.SubexpNames()
	regexEnumNameAssetTypeIdx = slices.Index(regexEnumNameGroups, "asset_type")
)

// NameFromAssetType returns the name of an asset type.
func NameFromAssetType(a atypepb.AssetType) string {
	if name, ok := customAssetTypeToName[a]; ok {
		return name
	}
	if submatches := regexEnumName.FindStringSubmatch(a.String()); submatches != nil {
		submatch := submatches[regexEnumNameAssetTypeIdx]
		return strings.ReplaceAll(strings.ToLower(submatch), "_", " ")
	}
	return NameFromAssetType(atypepb.AssetType_ASSET_TYPE_UNSPECIFIED)
}
