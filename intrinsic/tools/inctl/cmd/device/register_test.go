// Copyright 2023 Intrinsic Innovation LLC

package device

import (
	"testing"
)

func TestValidHostname(t *testing.T) {
	testCases := []struct {
		name     string
		hostname string
		valid    bool
	}{
		{
			name:     "empty",
			hostname: "",
			valid:    false,
		},
		{
			name:     "single-char",
			hostname: "h",
			valid:    true,
		},
		{
			name:     "simple",
			hostname: "host",
			valid:    true,
		},
		{
			name:     "cmplex",
			hostname: "host-13245-123413240-998",
			valid:    true,
		},
		{
			name:     "with-alpha",
			hostname: "host123",
			valid:    true,
		},
		{
			name:     "with-dash",
			hostname: "host-123",
			valid:    true,
		},
		{
			name:     "no-starting-dash",
			hostname: "-host-123",
			valid:    false,
		},
		{
			name:     "no-ending-dash",
			hostname: "host-123-",
			valid:    false,
		},
		{
			name:     "no-capital",
			hostname: "HOST-123",
			valid:    false,
		},
		{
			name:     "no-underscore",
			hostname: "host_123",
			valid:    false,
		},
		{
			name:     "no-overlength",
			hostname: "host-123456790-123456790-123456790-123456790-123456790-123456790",
			valid:    false,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			if got, want := validHostname(tc.hostname), tc.valid; got != want {
				t.Errorf("validHostname(%q) = %t, want %t", tc.hostname, got, want)
			}
		})
	}
}
