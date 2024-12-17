// Copyright 2023 Intrinsic Innovation LLC

// Package skill contains all commands for skill handling.
package skill

import (
	"intrinsic/skills/tools/skill/cmd/cmd"
	_ "intrinsic/skills/tools/skill/cmd/create/create"             // Add subcommand "skill create"
	_ "intrinsic/skills/tools/skill/cmd/defaults/cleardefault"     // Add subcommand "skill clear_default"
	_ "intrinsic/skills/tools/skill/cmd/install/install"           // Add subcommand "skill install".
	_ "intrinsic/skills/tools/skill/cmd/install/uninstall"         // Add subcommand "skill uninstall".
	_ "intrinsic/skills/tools/skill/cmd/list/list"                 // Add subcommand "skill list".
	_ "intrinsic/skills/tools/skill/cmd/list/listreleased"         // Add subcommand "skill list_released".
	_ "intrinsic/skills/tools/skill/cmd/list/listreleasedversions" // Add subcommand "skill list_released_versions".
	_ "intrinsic/skills/tools/skill/cmd/logs/logs"                 // Add subcommand "skill logs".
	_ "intrinsic/skills/tools/skill/cmd/release/release"           // Add subcommand "skill release".
	"intrinsic/tools/inctl/cmd/root"
)

func init() {
	root.RootCmd.AddCommand(cmd.SkillCmd)
}
