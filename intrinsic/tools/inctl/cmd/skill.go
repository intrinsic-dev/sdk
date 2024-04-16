// Copyright 2023 Intrinsic Innovation LLC

// Package skill contains all commands for skill handling.
package skill

import (
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/tools/inctl/cmd/root"

	// Add subcommand "skill create"
	_ "intrinsic/skills/tools/skill/cmd/create"

	// Add subcommand "skill list".
	_ "intrinsic/skills/tools/skill/cmd/list"
	// Add subcommand "skill listreleased".
	_ "intrinsic/skills/tools/skill/cmd/list/listreleased"
	// Add subcommand "skill listreleasedversions".
	_ "intrinsic/skills/tools/skill/cmd/list/listreleasedversions"
	// Add subcommand "skill install".
	_ "intrinsic/skills/tools/skill/cmd/install"
	// Add subcommand "skill uninstall".
	_ "intrinsic/skills/tools/skill/cmd/install/uninstall"
	// Add subcommand "skill logs".
	_ "intrinsic/skills/tools/skill/cmd/logs"
	// Add subcommand "skill release".
	_ "intrinsic/skills/tools/skill/cmd/release"
)

func init() {
	root.RootCmd.AddCommand(cmd.SkillCmd)
}
