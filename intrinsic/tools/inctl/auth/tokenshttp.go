// Copyright 2023 Intrinsic Innovation LLC

package auth

// This module provides a minimal HTTP-based client for the accounts tokens service.
// It is used by inctl to exchange API keys for ID tokens.

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

// TokensServiceClient is a HTTP-based client for the accounts tokens service.
type TokensServiceClient struct {
	client *http.Client
	addr   string
}

// GetIDTokenRequest is the HTTP payload to request an ID token.
type GetIDTokenRequest struct {
	APIKey   string `json:"api_key"`
	DoFanOut bool   `json:"do_fan_out"`
}

// GetIDTokenResponse is the body format of a successful ID token response.
type GetIDTokenResponse struct {
	IDToken string `json:"IdToken"`
}

// NewTokensServiceClient creates a new client for the accounts tokens service.
// addr is typically "flowstate.intrinsic.ai".
func NewTokensServiceClient(client *http.Client, addr string) (*TokensServiceClient, error) {
	return &TokensServiceClient{client: client, addr: addr}, nil
}

func (t *TokensServiceClient) Token(ctx context.Context, apiKey string) (string, error) {
	resp, err := GetIDToken(ctx, t.client, t.addr, &GetIDTokenRequest{
		APIKey:   apiKey,
		DoFanOut: true,
	})
	if err != nil {
		return "", fmt.Errorf("failed to get ID token: %v", err)
	}
	return resp.IDToken, nil
}

// GetIDToken exchanges an API key for an ID token using the accounts tokens service via HTTP.
func GetIDToken(ctx context.Context, cl *http.Client, addr string, req *GetIDTokenRequest) (*GetIDTokenResponse, error) {
	url := fmt.Sprintf("https://%s/api/v1/accountstokens:idtoken", addr)
	bd, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	r, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(bd))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}
	r.Header.Set("Content-Type", "application/json")
	resp, err := cl.Do(r)
	if err != nil {
		return nil, fmt.Errorf("failed to call accounts service: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("accounts service returned %d", resp.StatusCode)
	}
	var res GetIDTokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	if res.IDToken == "" {
		return nil, fmt.Errorf("empty id token")
	}
	return &res, nil
}
