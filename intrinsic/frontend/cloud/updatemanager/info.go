// Copyright 2023 Intrinsic Innovation LLC

// Package info contains shared struct definitions about update info
package info

import (
	"time"
)

// Info contains update information about a cluster
type Info struct {
	Cluster      string `json:"cluster,omitempty"`
	State        string `json:"state,omitempty"`
	Mode         string `json:"mode,omitempty"`
	CurrentBase  string `json:"currentBase,omitempty"`
	TargetBase   string `json:"targetBase,omitempty"`
	CurrentOS    string `json:"currentOS,omitempty"`
	TargetOS     string `json:"targetOS,omitempty"`
	RollbackOS   string `json:"rollbackOS,omitempty"`
	RollbackBase string `json:"rollbackBase,omitempty"`
	LastSeenTS   string `json:"lastSeenTS,omitempty"`
}

// LastSeen returns when the control plane was last seen
func (i *Info) LastSeen() (time.Time, error) {
	return time.Parse(time.RFC3339, i.LastSeenTS)
}

// RollbackAvailable reports whether a rollback is available according to this info object
func (i *Info) RollbackAvailable() bool {
	return i.RollbackOS != "" && i.RollbackBase != ""
}
