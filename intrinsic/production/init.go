// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package intrinsic provides initialization functionality for Golang binaries.
package intrinsic

import (
	"flag"
)

// Init is the entry point for Golang binaries. It parses command line flags and performs
// other common initialization.
func Init() {
	flag.Parse()
	// Other calls can be added here.
}
