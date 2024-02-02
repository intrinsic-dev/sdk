// Copyright 2023 Intrinsic Innovation LLC

// Package messages contains the message definitions to send to the updatemanager
package messages

// ModeRequest is a request message to update the mode field
type ModeRequest struct {
	Mode string `json:"mode"`
}
