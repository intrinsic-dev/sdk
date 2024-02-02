// Copyright 2023 Intrinsic Innovation LLC

// Package info contains shared struct definitions about update info
package info

// Info contains update information about a cluster
type Info struct {
	Cluster     string `json:"cluster,omitempty"`
	State       string `json:"state,omitempty"`
	TargetBase  string `json:"targetBase,omitempty"`
	CurrentBase string `json:"currentBase,omitempty"`
	CurrentOS   string `json:"currentOS,omitempty"`
	TargetOS    string `json:"targetOS,omitempty"`
}
