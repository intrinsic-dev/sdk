// Copyright 2023 Intrinsic Innovation LLC

package orgutil

import (
	"testing"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/auth"
	"intrinsic/tools/inctl/auth/authtest"
)

func TestWrapCmd(t *testing.T) {
	t.Run("empty-args", func(t *testing.T) {
		t.Parallel()

		vi := viper.New()
		cmd := WrapCmd(&cobra.Command{
			Run: func(*cobra.Command, []string) {
				t.Errorf("Did not expect Run to be called")
			},
		}, vi)

		cmd.SetArgs([]string{})
		if err := cmd.Execute(); err != nil {
			if !errors.Is(err, errNotXor) {
				t.Errorf("Expected errNotXor. Got error: %v", err)
			}
		} else {
			t.Errorf("Should fail with neither --project nor --org")
		}
	})

	t.Run("both-args", func(t *testing.T) {
		t.Parallel()

		vi := viper.New()
		cmd := WrapCmd(&cobra.Command{
			Run: func(*cobra.Command, []string) {
				t.Errorf("Did not expect Run to be called")
			},
		}, vi)

		cmd.SetArgs([]string{"--org=defaultorg", "--project=example-project"})
		if err := cmd.Execute(); err != nil {
			if !errors.Is(err, errNotXor) {
				t.Errorf("Expected errNotXor. Got error: %v", err)
			}
		} else {
			t.Errorf("Should fail with both --project nor --org")
		}
	})

	t.Run("project-only", func(t *testing.T) {
		t.Parallel()

		vi := viper.New()
		cmd := WrapCmd(&cobra.Command{
			Run: func(*cobra.Command, []string) {
				projectName := vi.GetString(KeyProject)
				orgName := vi.GetString(KeyOrganization)

				if projectName != "example-project" {
					t.Errorf("Expected project to be example-project. Got: %q", projectName)
				}

				if orgName != "" {
					t.Errorf("Expect org to be empty. Instead got: %q", orgName)
				}
			},
		}, vi)

		cmd.SetArgs([]string{"--project=example-project"})
		if err := cmd.Execute(); err != nil {
			t.Errorf("Unexpected error during test-run: %v", err)
		}
	})

	t.Run("org-simple", func(t *testing.T) {
		// This one cannot be run in parallel as it touches the authStore
		authStore = authtest.NewStoreForTest(t)
		authStore.WriteOrgInfo(&auth.OrgInfo{Project: "example-project", Organization: "otherorg"})

		vi := viper.New()
		cmd := WrapCmd(&cobra.Command{
			Run: func(*cobra.Command, []string) {
				projectName := vi.GetString(KeyProject)
				orgName := vi.GetString(KeyOrganization)

				if projectName != "example-project" {
					t.Errorf("Expected project to be example-project. Got: %q", projectName)
				}

				if orgName != "otherorg" {
					t.Errorf("Expect org to be otherorg. Instead got: %q", orgName)
				}
			},
		}, vi)

		cmd.SetArgs([]string{"--org=otherorg"})
		if err := cmd.Execute(); err != nil {
			t.Errorf("Unexpected error during test-run: %v", err)
		}
	})

	t.Run("org-complex", func(t *testing.T) {
		// This one cannot be run in parallel as it touches the authStore
		authStore = authtest.NewStoreForTest(t)
		authStore.WriteOrgInfo(&auth.OrgInfo{Project: "example-project", Organization: "defaultorg@example-project"})

		vi := viper.New()
		cmd := WrapCmd(&cobra.Command{
			Run: func(*cobra.Command, []string) {
				projectName := vi.GetString(KeyProject)
				orgName := vi.GetString(KeyOrganization)

				if projectName != "example-project" {
					t.Errorf("Expected project to be example-project. Got: %q", projectName)
				}

				if orgName != "defaultorg" {
					t.Errorf("Expect org to be defaultorg. Instead got: %q", orgName)
				}
			},
		}, vi)

		cmd.SetArgs([]string{"--org=defaultorg@example-project"})
		if err := cmd.Execute(); err != nil {
			t.Errorf("Unexpected error during test-run: %v", err)
		}
	})

	t.Run("no-such-org", func(t *testing.T) {
		// This one cannot be run in parallel as it touches the authStore
		authStore = authtest.NewStoreForTest(t)

		vi := viper.New()
		cmd := WrapCmd(&cobra.Command{
			Run: func(*cobra.Command, []string) {
				t.Errorf("Did not expect Run to be called")
			},
		}, vi)

		cmd.SetArgs([]string{"--org=defaultorg@example-project"})
		// We expect an error here!
		if err := cmd.Execute(); err != nil {
			var orgErr *ErrOrgNotFound
			if !errors.As(err, &orgErr) {
				t.Errorf("Expected ErrOrgNotFound. Got error: %v", err)
			}
		} else {
			t.Errorf("Expected error during test-run")
		}
	})

	t.Run("subcommand", func(t *testing.T) {
		t.Parallel()

		called := false
		vi := viper.New()
		cmd := WrapCmd(&cobra.Command{}, vi)
		cmd.AddCommand(&cobra.Command{
			Use: "subcommand",
			Run: func(*cobra.Command, []string) {
				called = true
				projectName := vi.GetString(KeyProject)
				orgName := vi.GetString(KeyOrganization)

				if projectName != "example-project" {
					t.Errorf("Expected project to be example-project. Got: %q", projectName)
				}

				if orgName != "" {
					t.Errorf("Expect org to be empty. Instead got: %q", orgName)
				}
			},
		})

		cmd.SetArgs([]string{"--project=example-project", "subcommand"})
		if err := cmd.Execute(); err != nil {
			t.Errorf("Unexpected error during test-run: %v", err)
		}

		if !called {
			t.Errorf("Expected subcommand to be called")
		}
	})
}

func TestEditDistance(t *testing.T) {
	testCases := []struct {
		name     string
		left     string
		right    string
		expected int
	}{
		{
			name:     "empty",
			left:     "",
			right:    "",
			expected: 0,
		},
		{
			name:     "simple",
			left:     "simple",
			right:    "simple",
			expected: 0,
		},
		{
			name:     "add",
			left:     "simple",
			right:    "simpler",
			expected: 1,
		},
		{
			name:     "subtract",
			left:     "simple",
			right:    "simpl",
			expected: 1,
		},
		{
			name:     "replaced",
			left:     "simple",
			right:    "siMple",
			expected: 1,
		},
		{
			name:     "swap",
			left:     "simple",
			right:    "smiple",
			expected: 2,
		},
		{
			name:     "unicode",
			left:     "work",
			right:    "wörk",
			expected: 1,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			if got := editDistance(tc.left, tc.right); got != tc.expected {
				t.Errorf("Expected editDistance(%q, %q) = %d, but got %d", tc.left, tc.right, tc.expected, got)
			}
		})
	}
}
