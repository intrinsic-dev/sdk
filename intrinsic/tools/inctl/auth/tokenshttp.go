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
	p      string
	url    string
}

var knownDomains = map[string]bool{
	"flowstate-dev.intrinsic.ai": true,
	"flowstate-qa.intrinsic.ai":  true,
	"flowstate.intrinsic.ai":     true,
}

type getIDTokenRequest struct {
	APIKey   string `json:"api_key"`
	DoFanOut bool   `json:"do_fan_out"`
}

type getIDTokenResponse struct {
	IDToken string `json:"IdToken"`
}

// NewTokensServiceClient creates a new client for the accounts tokens service.
func NewTokensServiceClient(client *http.Client, gwDomain string) (*TokensServiceClient, error) {
	if !knownDomains[gwDomain] {
		return nil, fmt.Errorf("invalid flowstate domain: %q", gwDomain)
	}
	url := fmt.Sprintf("https://%s/api/v1/accountstokens:idtoken", gwDomain)
	return &TokensServiceClient{client: client, url: url}, nil
}

func (t *TokensServiceClient) Token(ctx context.Context, apiKey string) (string, error) {
	req := &getIDTokenRequest{
		APIKey:   apiKey,
		DoFanOut: true,
	}
	bd, err := json.Marshal(req)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %v", err)
	}
	r, err := http.NewRequestWithContext(ctx, http.MethodPost, t.url, bytes.NewBuffer(bd))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %v", err)
	}
	r.Header.Set("Content-Type", "application/json")
	resp, err := t.client.Do(r)
	if err != nil {
		return "", fmt.Errorf("failed to call accounts service: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("accounts service returned %d", resp.StatusCode)
	}
	var res getIDTokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return "", fmt.Errorf("failed to decode response: %v", err)
	}
	if res.IDToken == "" {
		return "", fmt.Errorf("empty id token")
	}
	return res.IDToken, nil
}
