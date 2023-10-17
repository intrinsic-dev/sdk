// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
)

// Same as authtest.NewStoreForTest which is not accessible here as long as
// this test is in the 'auth' package (cyclic dependency).
func newStoreForTest(t *testing.T) *Store {
	configDir := t.TempDir()
	return &Store{func() (string, error) { return configDir, nil }}
}

func TestRFC3339Time_Marshaling(t *testing.T) {
	tests := []struct {
		input *RFC3339Time
		// ignores want, just ensures that it can get the same value
		biDirectional bool
		want          string
	}{
		{input: toRFC3339Time(time.Now().Truncate(time.Second)), biDirectional: true},
		{input: toRFC3339Time(time.Date(2000, 1, 10, 10, 9, 8, 0, time.UTC)), biDirectional: true},
		{input: toRFC3339Time(time.Date(2023, 4, 5, 0, 8, 47, 0, time.UTC)), want: "2023-04-05T00:08:47Z"},
	}

	for _, test := range tests {
		value, err := test.input.MarshalText()
		if err != nil {
			t.Errorf("cannot marshal time: %v", err)
		}
		if test.biDirectional {
			helper := new(RFC3339Time)
			if err = helper.UnmarshalText(value); err != nil {
				t.Errorf("cannot unmarshal time (%s): %v", value, err)
			}
			input := time.Time(*test.input)
			got := time.Time(*helper)
			if !input.Equal(got) {
				t.Errorf("output mismatch: got %s; wants: %s", got, input)
			}
		} else {
			// compares with fixed want value on string basis
			if string(value) != test.want {
				t.Errorf("output mismatch: got %s; want: %s", string(value), test.want)
			}
		}
	}
}

func TestStore_HasConfiguration(t *testing.T) {
	store := newStoreForTest(t)
	mustPrepareDirectoryStructure(t, store)

	tests := []struct {
		project    string
		setMode    os.FileMode
		skipCreate bool
		wants      bool
	}{
		{project: "hello-dolly-1", setMode: 0124, wants: false},
		{project: "hello-dolly-2", setMode: fileMode, wants: true},
		{project: "hello-dolly-3", setMode: directoryMode, wants: true},
		{project: "hello-dolly-4", setMode: 0200, wants: false},
		{project: "hello-dolly-5", setMode: 0277, wants: false},
		{project: "hello-dolly-6", setMode: 0777, wants: true},
		{project: "hello-dolly-7", setMode: 0100, wants: false},
		{project: "hello-dolly-8", setMode: 0400, wants: false},
		{project: "this-file-does-not-exists", skipCreate: true, wants: false},
	}

	for _, test := range tests {
		filename, err := store.getConfigurationFilename(test.project)
		if err != nil {
			t.Errorf("cannot get filename for project: %s", err)
		}
		if !test.skipCreate {
			err = os.WriteFile(filename, []byte(test.project), test.setMode)
			if err != nil {
				t.Errorf("cannot create mock credentials file: %s", err)
			}
		}
		result := store.HasConfiguration(test.project)
		if result != test.wants {
			t.Errorf("unexpected output: got %t; wants %t", result, test.wants)
		}
	}
}

func mustPrepareDirectoryStructure(t *testing.T, store *Store) {
	t.Helper()
	// throw away to establish directory structure
	filename, err := store.getConfigurationFilename("foo")
	if err != nil {
		t.Fatalf("giving up: cannot obtain directory structure: %v", err)
	}
	if err = os.MkdirAll(filepath.Dir(filename), directoryMode); err != nil {
		t.Fatalf("giving up: cannot create necessary directory tree: %v", err)
	}
}

func TestStore_GetConfiguration(t *testing.T) {
	store := newStoreForTest(t)

	projectName := "hello-dolly"
	config := &ProjectConfiguration{
		Name: projectName,
		Tokens: map[string]*ProjectToken{
			AliasDefaultToken: {
				APIKey:     "abcdefg.xyz",
				ValidUntil: toRFC3339Time(time.Now().Add(24 * time.Hour)),
			},
			"expired": {
				APIKey:     "abcdefg.xyz",
				ValidUntil: toRFC3339Time(time.Now().Add(-24 * time.Hour)),
			},
			"no-key": {
				APIKey:     "",
				ValidUntil: toRFC3339Time(time.Now().Add(24 * time.Hour)),
			},
			"empty-value": {},
			"nil-value":   nil,
		},
	}
	goldConfig, err := store.WriteConfiguration(config)
	if err != nil {
		t.Errorf("error writing configuration to persistent store: %v", err)
	}

	if !store.HasConfiguration(projectName) {
		t.Errorf("project configuration expected but not found")
	}

	config, err = store.GetConfiguration(projectName)
	if err != nil {
		t.Errorf("cannot load project configuration: %v", err)
	}

	diff := cmp.Diff(goldConfig, config, cmpopts.IgnoreUnexported(RFC3339Time{}))

	if diff != "" {
		t.Errorf("unexpected configuration value: %s", diff)
	}

	tests := []struct {
		alias   string
		isValid bool
	}{
		{alias: AliasDefaultToken, isValid: true},
		{alias: "empty-value", isValid: false},
		{alias: "nil-value", isValid: false},
		{alias: "expired", isValid: false},
		{alias: "no-key", isValid: false},
	}

	for _, test := range tests {
		credentials, err := config.GetCredentials(test.alias)
		if err != nil {
			t.Errorf("cannot get credentials for alias '%s': %v", test.alias, err)
		}
		err = credentials.Validate()
		if err != nil && test.isValid {
			t.Errorf("expecting valid credentials for alias '%s' but got error: %v", test.alias, err)
		} else if err == nil && !test.isValid {
			t.Errorf("expecting invalid credentials for alias '%s' but got valid", test.alias)
		}
	}
}

func toRFC3339Time(time time.Time) *RFC3339Time {
	result := RFC3339Time(time)
	return &result
}

func TestStore_OrgInfoEquality(t *testing.T) {
	tests := []struct {
		name string
		want OrgInfo
	}{
		{
			name: "simple",
			want: OrgInfo{Organization: "org", Project: "project"},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			s := newStoreForTest(t)
			err := s.WriteOrgInfo(&tc.want)
			if err != nil {
				t.Fatalf("WriteOrgInfo returned an unexpected error: %v", err)
			}

			got, err := s.ReadOrgInfo(tc.want.Organization)
			if err != nil {
				t.Fatalf("OrgInfo returned an unexpected error: %v", err)
			}

			if diff := cmp.Diff(tc.want, got); diff != "" {
				t.Errorf("OrgInfo returned an unexpected diff (-want +got): %v", diff)
			}
		})
	}
}
