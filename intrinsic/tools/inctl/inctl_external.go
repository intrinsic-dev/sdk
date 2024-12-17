// Copyright 2023 Intrinsic Innovation LLC

package main

import (
	_ "intrinsic/assets/services/inctl/service"
	_ "intrinsic/tools/inctl/cmd/auth/auth"
	_ "intrinsic/tools/inctl/cmd/bazel/bazel"
	_ "intrinsic/tools/inctl/cmd/cluster/cluster"
	_ "intrinsic/tools/inctl/cmd/device/device"
	_ "intrinsic/tools/inctl/cmd/logs/logs"
	_ "intrinsic/tools/inctl/cmd/notebook/notebook"
	_ "intrinsic/tools/inctl/cmd/process/process"
	"intrinsic/tools/inctl/cmd/root"
	_ "intrinsic/tools/inctl/cmd/skill"
	_ "intrinsic/tools/inctl/cmd/solution/solution"
	_ "intrinsic/tools/inctl/cmd/version/version"
)

func main() {
	root.Inctl()
}
