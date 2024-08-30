// Copyright 2023 Intrinsic Innovation LLC

// Package jwt provides helpers for JWT handling.
package jwt

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/pkg/errors"
)

// Data defines our relevant subset of the oauth standard plus our custom claims.
// Extend with more attributes when needed.
type Data struct {
	Aud           string `json:"aud"`
	Email         string `json:"email"`
	EmailVerified bool   `json:"email_verified"`
	ExpiresAt     int64  `json:"exp"`

	// intrinsic custom claims
	Authorized bool     `json:"authorized"`
	Projects   []string `json:"ps"`
}

// Claim keys and values found in the JWT.
const (
	ClaimEmailVerified = "email_verified"
	ClaimAuthorized    = "authorized"
	ClaimProjects      = "ps"
	ClaimProjectsAll   = "*"
)

// UnmarshalUnsafe unmarshals the JWT payload and returns the parsed data.
//
// Unsafe because the content can not be trusted if you do not also verify
// the signature of the JWT.
func UnmarshalUnsafe(jwtk string) (*Data, error) {
	bs, err := decodePayload(jwtk)
	if err != nil {
		return nil, fmt.Errorf("failed to decode JWT payload section: %w", err)
	}
	d := Data{}
	if err := json.Unmarshal(bs, &d); err != nil {
		return nil, fmt.Errorf("failed to unmarshal JWT payload section: %w", err)
	}
	return &d, nil
}

// PayloadUnsafe returns the unverified payload section of a given JWT.
// Use PayloadUnsafe if you need raw access to the JWT. Otherwise prefer ParseUnsafe.
//
// Unsafe because the content can not be trusted if you do not also verify
// the signature of the JWT.
func PayloadUnsafe(jwtk string) (map[string]any, error) {
	bs, err := decodePayload(jwtk)
	if err != nil {
		return nil, fmt.Errorf("failed to decode JWT payload section: %w", err)
	}
	dat := map[string]any{}
	err = json.Unmarshal(bs, &dat)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal JWT payload section: %w", err)
	}
	return dat, nil
}

// IsVerifiedAndAuthorizedUnsafe checks if the given JWT is verified and authorized.
//
// Unsafe because the content can not be trusted if you do not also verify
// the signature of the JWT.
func IsVerifiedAndAuthorizedUnsafe(tk string) error {
	d, err := UnmarshalUnsafe(tk)
	if err != nil {
		return fmt.Errorf("failed to unmarshal token: %v", err)
	}
	if !d.EmailVerified {
		return fmt.Errorf("email not verified")
	}
	if !d.Authorized {
		return fmt.Errorf("record not authorized")
	}
	return nil
}

func decodePayload(jwtk string) ([]byte, error) {
	parts := strings.Split(jwtk, ".")
	if len(parts) != 3 {
		return nil, errors.New("invalid JWT, token must have 3 parts")
	}
	d, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return nil, fmt.Errorf("failed to decode JWT payload section: %v", err)
	}
	return d, nil
}

// Email extracts the mail address of the user from the given JWT.
//
// Be aware that the signature of the JWT is not verified in this function.
func Email(t string) (string, error) {
	pl, err := PayloadUnsafe(t)
	if err != nil {
		return "", errors.Wrap(err, "decoding payload")
	}
	// We check "email" in firebase id-tokens and "uid" in custom token we create
	// from api-key usage. So far we have not found a way to align the fields.
	// "user_id" is populated by ID tokens generated from the API key auth path.
	for _, k := range []string{"email", "uid", "user_id"} {
		m, ok := pl[k].(string)
		if ok && m != "" {
			return m, nil
		}
	}
	return "", fmt.Errorf("failed to extract email from JWT")
}

// Aud extracts the audience from the given JWT.
//
// For Firebase ID tokens, we return the value of the `aud` field, which specifies the Firebase that
// issued/signed the JWT.
//
// Be aware that the signature of the JWT is not verified in this function.
func Aud(t string) (string, error) {
	pl, err := PayloadUnsafe(t)
	if err != nil {
		return "", errors.Wrap(err, "decoding payload")
	}

	// Look for a proper audience from a Firebase ID token.
	if aud, ok := pl["aud"].(string); ok && aud != "" && !strings.HasPrefix(aud, "https://") {
		return aud, nil
	}
	return "", fmt.Errorf("failed to extract audience from JWT")
}
