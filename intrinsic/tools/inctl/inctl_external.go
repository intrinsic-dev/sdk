// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package main

import (
	_ "intrinsic/tools/inctl/cmd/auth/auth"
	_ "intrinsic/tools/inctl/cmd/bazel/bazel"
	_ "intrinsic/tools/inctl/cmd/cluster/cluster"
	_ "intrinsic/tools/inctl/cmd/device/device"
	"intrinsic/tools/inctl/cmd/root"
	_ "intrinsic/tools/inctl/cmd/skill"
	_ "intrinsic/tools/inctl/cmd/solution/solution"
	_ "intrinsic/tools/inctl/cmd/version/version"
)

func main() {
	root.Inctl()
}
