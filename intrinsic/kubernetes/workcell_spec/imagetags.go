// Copyright 2023 Intrinsic Innovation LLC

// Package imagetags contains logic to generate default tags for container images.
package imagetags

import (
	"os"
	"os/user"

	"github.com/pborman/uuid"
	"github.com/pkg/errors"
)

const (
	// DevPrefix is the prefix for dev images tags.
	DevPrefix                = "dev."
	intrinsicDevContainerEnv = "INTRINSIC_DEV_CONTAINER"
	userVSCode               = "vscode"
	userCodespaces           = "codespaces"
	dockerMarkerFile         = "/.dockerenv"
	termProgramEnv           = "TERM_PROGRAM"
	termProgramEnvValue      = "vscode"
)

// DefaultTag generates a tag for container images.
func DefaultTag() (string, error) {
	user, err := user.Current()
	if err != nil {
		return "", errors.Wrapf(err, "getting current user")
	}
	result := DevPrefix + user.Username

	if isIntrinsicDevContainer(user.Username) {
		result += "-" + uuid.NewRandom().String()[:8]
	}

	return result, nil
}

func isIntrinsicDevContainer(username string) bool {
	// If this is set, we are sure we have intrinsic dev container
	// we do not care about value
	if _, exists := os.LookupEnv(intrinsicDevContainerEnv); exists {
		return true
	}
	// Even if we do not have dev container marker, we will try to guess if we are running
	// in container by any chance. This is mostly temporary fallback
	mayBeContainer := username == userVSCode || username == userCodespaces ||
		os.Getenv(termProgramEnv) == termProgramEnvValue
	if mayBeContainer {
		// For caveat see https://superuser.com/questions/1021834/what-are-dockerenv-and-dockerinit
		_, err := os.Stat(dockerMarkerFile)
		return err == nil
	}
	// We are not in dev container or we cannot determine the environment.
	return false
}
