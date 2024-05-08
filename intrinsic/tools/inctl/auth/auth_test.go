// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"context"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
	"google.golang.org/grpc/metadata"
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

func TestStore_AuthorizeContext(t *testing.T) {
	projectName := "friendly-name"

	tests := []struct {
		name                      string
		givenProjectConfiguration *ProjectConfiguration
		ctx                       context.Context
		projectName               string
		wantOutgoingMetadata      metadata.MD
		wantErr                   bool
	}{
		{
			name: "adds authorization header to the context",
			givenProjectConfiguration: &ProjectConfiguration{
				Name: projectName,
				Tokens: map[string]*ProjectToken{
					AliasDefaultToken: {
						APIKey:     "abcdefg.xyz",
						ValidUntil: toRFC3339Time(time.Now().Add(24 * time.Hour)),
					},
				},
			},
			ctx:                  context.Background(),
			projectName:          projectName,
			wantOutgoingMetadata: metadata.Pairs("authorization", "Bearer abcdefg.xyz"),
		},
		{
			name: "does not change an existing authorization header",
			givenProjectConfiguration: &ProjectConfiguration{
				Name: projectName,
				Tokens: map[string]*ProjectToken{
					AliasDefaultToken: {
						APIKey:     "abcdefg.xyz",
						ValidUntil: toRFC3339Time(time.Now().Add(24 * time.Hour)),
					},
				},
			},
			ctx: metadata.NewOutgoingContext(
				context.Background(),
				metadata.Pairs("authorization", "Bearer existing.token"),
			),
			projectName:          projectName,
			wantOutgoingMetadata: metadata.Pairs("authorization", "Bearer existing.token"),
		},
		{
			name: "fails if there is no authorization information for the project",
			givenProjectConfiguration: &ProjectConfiguration{
				Name: projectName,
				Tokens: map[string]*ProjectToken{
					AliasDefaultToken: {
						APIKey:     "abcdefg.xyz",
						ValidUntil: toRFC3339Time(time.Now().Add(24 * time.Hour)),
					},
				},
			},
			ctx:         context.Background(),
			projectName: "other-project",
			wantErr:     true,
		},
		{
			name: "fails if there is no default credential for the project",
			givenProjectConfiguration: &ProjectConfiguration{
				Name: projectName,
				Tokens: map[string]*ProjectToken{
					"not-default": {
						APIKey:     "abcdefg.xyz",
						ValidUntil: toRFC3339Time(time.Now().Add(24 * time.Hour)),
					},
				},
			},
			ctx:         context.Background(),
			projectName: projectName,
			wantErr:     true,
		},
		{
			name: "fails if the default credential for the project is invalid",
			givenProjectConfiguration: &ProjectConfiguration{
				Name: projectName,
				Tokens: map[string]*ProjectToken{
					AliasDefaultToken: {
						APIKey:     "", // empty key is invalid
						ValidUntil: toRFC3339Time(time.Now().Add(24 * time.Hour)),
					},
				},
			},
			ctx:         context.Background(),
			projectName: projectName,
			wantErr:     true,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			store := newStoreForTest(t)

			if _, err := store.WriteConfiguration(tc.givenProjectConfiguration); err != nil {
				t.Fatalf("WriteConfiguration(%v) returned an unexpected error: %v", tc.givenProjectConfiguration, err)
			}

			got, err := store.AuthorizeContext(tc.ctx, tc.projectName)
			if !tc.wantErr && err != nil {
				t.Errorf("AuthorizeContext(%v) returned an unexpected error: %v", tc.projectName, err)
			}
			if tc.wantErr && err == nil {
				t.Errorf("AuthorizeContext(%v) returned no error, want error", tc.projectName)
			}

			gotOutgoingMetadata, _ := metadata.FromOutgoingContext(got)
			if diff := cmp.Diff(tc.wantOutgoingMetadata, gotOutgoingMetadata); diff != "" {
				t.Errorf("AuthorizeContext(%v) has unexpected metadata (-want +got): %v", tc.projectName, diff)
			}
		})
	}
}

func TestStore_RemoveOrganization(t *testing.T) {
	type fields struct {
		projects []ProjectConfiguration
		orgs     []OrgInfo
	}
	type args struct {
		name string
	}
	type wants struct {
		projects []string
		orgs     []string
		wantErr  bool
	}
	tests := []struct {
		name   string
		fields fields
		args   args
		wants  wants
	}{
		{
			name: "single-organization",
			fields: fields{
				orgs: []OrgInfo{
					{Organization: "first-org", Project: "first-project"},
				},
				projects: []ProjectConfiguration{
					{Name: "first-project"},
				},
			},
			args:  args{name: "first-org"},
			wants: wants{wantErr: false},
		},
		{
			name: "shared-project-not-removed",
			fields: fields{orgs: []OrgInfo{
				{Organization: "first-org", Project: "first-project"},
				{Organization: "second-org", Project: "first-project"},
			}, projects: []ProjectConfiguration{{Name: "first-project"}},
			},
			args: args{name: "first-org"},
			wants: wants{
				projects: []string{"first-project"},
				orgs:     []string{"second-org"},
				wantErr:  false,
			},
		},
		{
			name: "fail-remove-non-existent",
			fields: fields{
				orgs: []OrgInfo{
					{Organization: "first-org", Project: "first-project"},
				},
				projects: []ProjectConfiguration{
					{Name: "first-project"},
				},
			},
			args: args{name: "second-org"},
			wants: wants{
				projects: []string{"first-project"},
				orgs:     []string{"first-org"},
				wantErr:  true,
			},
		},
		{
			name: "ignore-missing-project",
			fields: fields{
				orgs: []OrgInfo{
					{Organization: "first-org", Project: "first-project"},
				},
				projects: []ProjectConfiguration{
					{Name: "second-project"},
				},
			},
			args: args{name: "first-org"},
			wants: wants{
				projects: []string{"second-project"},
				wantErr:  false,
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			s := newStoreForTest(t)

			for _, project := range tt.fields.projects {
				_, err := s.WriteConfiguration(&project)
				if err != nil {
					t.Errorf("cannot write project %v: %s", project, err)
				}
			}

			for _, org := range tt.fields.orgs {
				if err := s.WriteOrgInfo(&org); err != nil {
					t.Errorf("cannot write organization %v: %s", org, err)
				}
			}

			if err := s.RemoveOrganization(tt.args.name); (err != nil) != tt.wants.wantErr {
				t.Errorf("RemoveOrganization() error = %v, wantErr %v", err, tt.wants.wantErr)
			}

			projects, err := s.ListConfigurations()
			if err != nil {
				t.Errorf("unexpected error listing projects: %s", err)
			}
			slices.Sort(projects)
			slices.Sort(tt.wants.projects)
			orgs, err := s.ListOrgs()
			if err != nil {
				t.Errorf("unexpected error listing orgs: %s", err)
			}
			slices.Sort(orgs)
			slices.Sort(tt.wants.orgs)
			if diff := cmp.Diff(projects, tt.wants.projects); diff != "" {
				t.Errorf("unexpected projects: %q", diff)
			}
			if diff := cmp.Diff(orgs, tt.wants.orgs); diff != "" {
				t.Errorf("unexpected organizations: %q", diff)
			}
		})
	}
}

func TestStore_RemoveAllKnownCredentials(t *testing.T) {
	type fields struct {
		projects []ProjectConfiguration
		orgs     []OrgInfo
	}
	type args struct {
		name string
	}
	tests := []struct {
		name    string
		fields  fields
		wantErr bool
	}{
		{
			name: "single-organization",
			fields: fields{
				orgs: []OrgInfo{
					{Organization: "first-org", Project: "first-project"},
				},
				projects: []ProjectConfiguration{
					{Name: "first-project"},
				},
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			s := newStoreForTest(t)

			for _, project := range tt.fields.projects {
				_, err := s.WriteConfiguration(&project)
				if err != nil {
					t.Errorf("cannot write project %v: %s", project, err)
				}
			}

			for _, org := range tt.fields.orgs {
				if err := s.WriteOrgInfo(&org); err != nil {
					t.Errorf("cannot write organization %v: %s", org, err)
				}
			}

			if err := s.RemoveAllKnownCredentials(); (err != nil) != tt.wantErr {
				t.Errorf("RemoveOrganization() error = %v, wantErr %v", err, tt.wantErr)
			}

			projects, err := s.ListConfigurations()
			if err != nil {
				t.Errorf("unexpected error listing projects: %s", err)
			}
			if len(projects) != 0 {
				t.Errorf("unexpected projects found: %q", strings.Join(projects, ", "))
			}

			orgs, err := s.ListOrgs()
			if err != nil {
				t.Errorf("unexpected error listing orgs: %s", err)
			}
			if len(orgs) != 0 {
				t.Errorf("unexpected organizations found: %q", strings.Join(orgs, ", "))
			}
		})
	}
}
