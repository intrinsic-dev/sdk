// Copyright 2023 Intrinsic Innovation LLC

// Package info contains shared struct definitions about update info
package info

import (
	"time"
)

// IPCInfo contains update information about an IPC Node in a cluster
type IPCInfo struct {
	Name       string `json:"name,omitempty"`
	LastSeenTS string `json:"lastSeenTS,omitempty"`
	OSVersion  string `json:"osVersion,omitempty"`
	ISControl  bool   `json:"isControl,omitempty"`
}

// LastSeen returns when the IPC was last seen (parsing the heartbeat string timestamp into a time.Time)
func (i *IPCInfo) LastSeen() (time.Time, error) {
	return time.Parse(time.RFC3339, i.LastSeenTS)
}

// Info contains update information about a cluster
type Info struct {
	Cluster      string     `json:"cluster,omitempty"`
	State        string     `json:"state,omitempty"`
	OSState      string     `json:"osState,omitempty"`
	BaseState    string     `json:"baseState,omitempty"`
	BaseManager  string     `json:"baseManager,omitempty"`
	Mode         string     `json:"mode,omitempty"`
	CurrentBase  string     `json:"currentBase,omitempty"`
	TargetBase   string     `json:"targetBase,omitempty"`
	CurrentOS    string     `json:"currentOS,omitempty"`
	TargetOS     string     `json:"targetOS,omitempty"`
	RollbackOS   string     `json:"rollbackOS,omitempty"`
	RollbackBase string     `json:"rollbackBase,omitempty"`
	LastSeenTS   string     `json:"lastSeenTS,omitempty"`
	Nodes        []*IPCInfo `json:"nodes,omitempty"`
}

// LastSeen returns when the control plane was last seen
func (i *Info) LastSeen() (time.Time, error) {
	return time.Parse(time.RFC3339, i.LastSeenTS)
}

// RollbackAvailable reports whether a rollback is available according to this info object
func (i *Info) RollbackAvailable() bool {
	return i.RollbackOS != "" && i.RollbackBase != ""
}

// OSUpdateDone returns true when the OS is in a deployed state
func (i *Info) OSUpdateDone() bool {
	return i.OSState == "Deployed"
}

// UpdateDone returns true when the system is in a deployed state
func (i *Info) UpdateDone() bool {
	return i.State == "Deployed"
}
