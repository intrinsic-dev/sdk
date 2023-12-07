// Copyright 2023 Intrinsic Innovation LLC

// Package skillid provides skill-specific ID utils.
package skillid

import (
	"encoding/base32"
	"fmt"
	"strings"

	"github.com/google/uuid"
	"intrinsic/assets/idutils"
)

const (
	sideloadedSkillVersionPrefix = "0.0.1+sideloaded"
)

// IsSideloaded determines whether the given id_version matches that of a sideloaded skill.
func IsSideloaded(skillIDVersion string) bool {
	return strings.Contains(skillIDVersion, sideloadedSkillVersionPrefix)
}

// CreateSideloadedIDVersion creates a sideloaded skill id_version for the provided skill id.
func CreateSideloadedIDVersion(skillID string) (string, error) {
	id := uuid.New()
	version := sideloadedSkillVersionPrefix + strings.Replace(base32.StdEncoding.EncodeToString(id[:]), "=", "", -1)
	pkg, err := idutils.PackageFrom(skillID)
	if err != nil {
		return "", fmt.Errorf("parse package from id: %v", err)
	}
	name, err := idutils.NameFrom(skillID)
	if err != nil {
		return "", fmt.Errorf("parse name from id: %v", err)
	}
	idVersion, err := idutils.IDVersionFrom(pkg, name, version)
	if err != nil {
		return "", fmt.Errorf("create id_version: %v", err)
	}
	return idVersion, nil
}
