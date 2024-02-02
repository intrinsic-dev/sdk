// Copyright 2023 Intrinsic Innovation LLC

// Package messages contains the message definitions to send to the updatemanager
package messages

// ModeRequest is a request message to update the mode field
type ModeRequest struct {
	Mode string `json:"mode"`
}

// ClusterProjectTargetResponse is the response to the cluster project target request
type ClusterProjectTargetResponse struct {
	OS   string `json:"os"`
	Base string `json:"base"`
}
