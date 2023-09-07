// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package main defines the ICON hardware module installer command-line tool binary.
package main

import (
	"intrinsic/icon/hal/tools/hwmodule/cmd/cmd"
	_ "intrinsic/icon/hal/tools/hwmodule/cmd/start"
	_ "intrinsic/icon/hal/tools/hwmodule/cmd/stop"
)

func main() {
	cmd.Execute()
}
