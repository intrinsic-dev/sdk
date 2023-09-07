// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package skill contains all commands for skill handling.
package skill

import (
	"intrinsic/skills/tools/skill/cmd/cmd"
	"intrinsic/tools/inctl/cmd/root"

	// Add subcommand "skill create"
	_ "intrinsic/skills/tools/skill/cmd/create/create"
	// Add subcommand "skill list".
	_ "intrinsic/skills/tools/skill/cmd/list/list"
	// Add subcommand "skill listreleased".
	_ "intrinsic/skills/tools/skill/cmd/list/listreleased"
	// Add subcommand "skill listreleasedversions".
	_ "intrinsic/skills/tools/skill/cmd/list/listreleasedversions"
	// Add subcommand "skill logs".
	_ "intrinsic/skills/tools/skill/cmd/logs/logs"
	// Add subcommand "skill release".
	_ "intrinsic/skills/tools/skill/cmd/release/release"
	// Add subcommand "skill start".
	_ "intrinsic/skills/tools/skill/cmd/sideload/start"
	// Add subcommand "skill stop".
	_ "intrinsic/skills/tools/skill/cmd/sideload/stop"
)

func init() {
	root.RootCmd.AddCommand(cmd.SkillCmd)
}
