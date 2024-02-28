// Copyright 2023 Intrinsic Innovation LLC

package main

import (
	_ "intrinsic/tools/inctl/cmd/auth"
	_ "intrinsic/tools/inctl/cmd/bazel"
	_ "intrinsic/tools/inctl/cmd/cluster"
	_ "intrinsic/tools/inctl/cmd/device"
	_ "intrinsic/tools/inctl/cmd/notebook"
	_ "intrinsic/tools/inctl/cmd/process"
	"intrinsic/tools/inctl/cmd/root"
	_ "intrinsic/tools/inctl/cmd/skill"
	_ "intrinsic/tools/inctl/cmd/solution"
	_ "intrinsic/tools/inctl/cmd/version"
)

func main() {
	root.Inctl()
}
