// Copyright 2023 Intrinsic Innovation LLC

// Package auth manages API keys in a local config files.
package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"google.golang.org/grpc/metadata"
)

const (

	// AliasDefaultToken is the alias under which the default token is stored.
	AliasDefaultToken = "default"

	storeDirectory      = "intrinsic/projects"
	orgStoreDirectory   = "intrinsic/organizations"
	authConfigExtension = ".user-token"

	// OrgIDHeader is the header name for providing the org in requests to our services.
	OrgIDHeader = "org-id"

	directoryMode  os.FileMode = 0700
	fileMode       os.FileMode = 0600
	writeFileFlags             = os.O_WRONLY | os.O_CREATE | os.O_TRUNC
)

// RFC3339Time is type alias to correct (un)marshaling time.Time in RFC3339 format
type RFC3339Time time.Time

func (t *RFC3339Time) String() string {
	return time.Time(*t).Format(time.RFC3339)
}

// UnmarshalText implements encoding.TextUnmarshaler interface to unmarshal
// from RFC3339 formatted timestamp
func (t *RFC3339Time) UnmarshalText(text []byte) error {
	tx, err := time.Parse(time.RFC3339, string(text))
	if err != nil {
		return err
	}
	*t = RFC3339Time(tx)
	return nil
}

// MarshalText implements encoding.TextMarshaler interface to output
// timestamp in RFC3339 format.
func (t *RFC3339Time) MarshalText() (text []byte, err error) {
	return []byte((time.Time(*t)).Format(time.RFC3339)), nil
}

// OrgInfo encapsulates the information needed to use organization names in inctl.
type OrgInfo struct {
	Organization string `json:"org"`
	Project      string `json:"project"`
}

// ProjectToken represents cloud project bound API Token for user authorization
type ProjectToken struct {
	APIKey string `json:"apiKey"`
	// Reserved for future use, as we do not have this information yet
	ValidUntil *RFC3339Time `json:"validUntil,omitempty"`
}

// Validate performs validation of API Token
func (p *ProjectToken) Validate() error {
	if p == nil {
		return fmt.Errorf("nil token")
	}
	if p.ValidUntil != nil {
		if time.Now().After(time.Time(*p.ValidUntil)) {
			return fmt.Errorf("project token expired: %s", p.ValidUntil)
		}
	}
	if p.APIKey == "" {
		return fmt.Errorf("missing api key")
	}

	return nil
}

func (p *ProjectToken) GetRequestMetadata(_ context.Context, _ ...string) (map[string]string, error) {
	return map[string]string{
		"authorization": fmt.Sprintf("Bearer %s", p.APIKey),
	}, p.Validate()
}

// RequireTransportSecurity always return true to protect credentials
func (p *ProjectToken) RequireTransportSecurity() bool {
	return true
}

// HTTPAuthorization sets Authorization header to given request using project token.
func (p *ProjectToken) HTTPAuthorization(req *http.Request) (*http.Request, error) {
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", p.APIKey))
	return req, p.Validate()
}

// ProjectConfiguration contains list of API tokens related to given project
type ProjectConfiguration struct {
	Name string `json:"name"`
	// Tokens map individual API tokens for given project.
	// It is a map of alias: {api_key...}
	Tokens map[string]*ProjectToken `json:"tokens,omitempty"`

	// LastUpdated tracks when the file was last written by store, may be omitted
	LastUpdated *RFC3339Time `json:"lastUpdated,omitempty"`
}

// SetCredentials sets given apiKey to given alias in project configuration and optionally setting validity period.
func (p *ProjectConfiguration) SetCredentials(alias string, apiKey string, validUntil ...time.Time) (*ProjectConfiguration, error) {
	token := &ProjectToken{
		APIKey: apiKey,
	}
	if len(validUntil) > 0 && !validUntil[0].IsZero() {
		expires := RFC3339Time(validUntil[0])
		token.ValidUntil = &expires
	}
	p.Tokens[alias] = token

	return p, token.Validate()
}

// SetDefaultCredentials sets given apiKey to default alias, optionally setting validity period
func (p *ProjectConfiguration) SetDefaultCredentials(apiKey string, validUntil ...time.Time) (*ProjectConfiguration, error) {
	return p.SetCredentials(AliasDefaultToken, apiKey, validUntil...)
}

// HasCredentials checks if given project configuration has apiKey assigned to given alias.
func (p *ProjectConfiguration) HasCredentials(alias string) bool {
	_, ok := p.Tokens[alias]
	return ok
}

// GetCredentials returns ProjectToken object assigned to given alias or error if
// alias was not found.
func (p *ProjectConfiguration) GetCredentials(alias string) (*ProjectToken, error) {
	token, ok := p.Tokens[alias]
	if !ok {
		return nil, fmt.Errorf("token with alias '%s' not found", alias)
	}
	return token, nil
}

// GetDefaultCredentials returns ProjectToken object assigned to default alias,
// or error if not found.
func (p *ProjectConfiguration) GetDefaultCredentials() (*ProjectToken, error) {
	return p.GetCredentials(AliasDefaultToken)
}

// Store provides access to a collection of ProjectConfigurations stored as
// files in the users config directory.
type Store struct {
	// GetConfigDirFx is an indirection allowing to use custom config dirs in tests.
	GetConfigDirFx func() (string, error)
}

// NewStore returns a new Store instance.
func NewStore() *Store {
	return &Store{}
}

func (s *Store) getConfigDir() (string, error) {
	if s.GetConfigDirFx == nil {
		return os.UserConfigDir()
	}
	return s.GetConfigDirFx()
}

// HasConfiguration check if configuration with given name exists. Name usually
// matches name of cloud project.
func (s *Store) HasConfiguration(name string) bool {
	filename, err := s.getConfigurationFilename(name)
	if err != nil {
		return false
	}
	// we need to open filename to ensure we have read rights to it.
	info, err := os.Stat(filename)
	if err != nil {
		return false
	}
	// validate minimal required access permissions
	return (info.Mode().Perm() & fileMode) == fileMode
}

func (s *Store) getStoreLocation() (string, error) {
	configDir, err := s.getConfigDir()
	return filepath.Join(configDir, storeDirectory), err
}

func (s *Store) getConfigurationFilename(name string) (string, error) {
	if name == "" {
		return "", fmt.Errorf("name name is required")
	}
	storeDir, err := s.getStoreLocation()
	if err != nil {
		return "", fmt.Errorf("cannot find configurations: %w", err)
	}
	projectFile := fmt.Sprintf("%s%s", name, authConfigExtension)
	return filepath.Join(storeDir, projectFile), nil
}

// NewConfiguration returns a new, empty ProjectConfiguration for the given
// project name.
func NewConfiguration(name string) *ProjectConfiguration {
	return &ProjectConfiguration{
		Name:        name,
		Tokens:      make(map[string]*ProjectToken, 0),
		LastUpdated: nil,
	}
}

// GetConfiguration reads configuration with given name from persistent storage
// or returns error if such configuration is not found or cannot be opened.
func (s *Store) GetConfiguration(name string) (*ProjectConfiguration, error) {
	filename, err := s.getConfigurationFilename(name)
	if err != nil {
		return nil, fmt.Errorf("cannot open configuration for name '%s': %w", name, err)
	}

	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("cannot open configuration file: %w", err)
	}
	defer file.Close()

	var result ProjectConfiguration
	err = json.NewDecoder(file).Decode(&result)
	if err != nil {
		err = fmt.Errorf("cannot read name configuration: %w", err)
	}
	// ensure that tokens are always populated
	if result.Tokens == nil {
		result.Tokens = map[string]*ProjectToken{}
	}
	return &result, err
}

// WriteConfiguration will always return config supplied as parameter. Any error
// returned from this method indicates unsuccessful write to persistent storage.
func (s *Store) WriteConfiguration(config *ProjectConfiguration) (*ProjectConfiguration, error) {
	filename, err := s.getConfigurationFilename(config.Name)
	if err != nil {
		return config, err
	}
	// we make sure we have whole directory structure before we create file.
	// os.MkdirAll() calls os.Stat() on path, so there is no point to do it here.
	if err = os.MkdirAll(filepath.Dir(filename), directoryMode); err != nil {
		return config, fmt.Errorf("cannot create target directory: %w", err)
	}

	file, err := os.OpenFile(filename, writeFileFlags, fileMode)
	if err != nil {
		return config, fmt.Errorf("cannot open configuration file: %w", err)
	}

	defer file.Close()

	// update last modified in UTC time
	now := RFC3339Time(time.Now().UTC())
	config.LastUpdated = &now

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err = encoder.Encode(config); err != nil {
		return config, fmt.Errorf("cannot serialize configuration: %w", err)
	}

	// if sync fails, we did not write into store.
	return config, file.Sync()
}

// ListConfigurations gives a list of known configurations. It works on
// filesystem level and does not attempt to read the content of configuration.
// Membership in this list does not guarantee valid configuration for given name
// exists. Results is not sorted and is returned in same order as blobbed on
// filesystem.
func (s *Store) ListConfigurations() ([]string, error) {
	storeLocation, err := s.getStoreLocation()
	if err != nil {
		return nil, fmt.Errorf("cannot find configuration store: %w", err)
	}

	globPattern := filepath.Join(storeLocation, "*"+authConfigExtension)
	matches, err := filepath.Glob(globPattern)
	if err != nil {
		panic(fmt.Errorf("invalid glob pattern, programmer error: %w", err))
	}
	if len(matches) == 0 {
		// this is valid response, there are no projects found.
		return nil, nil
	}
	result := make([]string, 0, len(matches))
	for _, match := range matches {
		filename := filepath.Base(match)
		result = append(result, strings.TrimSuffix(filename, authConfigExtension))
	}

	return result, nil
}

func (s *Store) removeAlias(configurationName string, alias string) error {
	configuration, err := s.GetConfiguration(configurationName)
	if err != nil {
		return err
	}
	delete(configuration.Tokens, alias)
	_, err = s.WriteConfiguration(configuration)
	return err
}

// RemoveConfiguration removes the stored configuration for the given project
// name. Returns nil if no such configuration exists.
func (s *Store) RemoveConfiguration(name string) error {
	filename, err := s.getConfigurationFilename(name)
	if err != nil {
		return fmt.Errorf("cannot remove configuration: %w", err)
	}
	return os.RemoveAll(filename)
}

// AuthorizeContext retrieves the default credentials for the given project and adds authorization
// information directly to a context derived from the given context. If the context already has
// authorization information this function will *not* modify the context.
func (s *Store) AuthorizeContext(ctx context.Context, projectName string) (context.Context, error) {
	configuration, err := s.GetConfiguration(projectName)
	if err != nil {
		return ctx, fmt.Errorf("cannot get configuration: %w", err)
	}
	pt, err := configuration.GetDefaultCredentials()
	if err != nil {
		return ctx, fmt.Errorf("cannot get default credentials: %w", err)
	}
	if err := pt.Validate(); err != nil {
		return ctx, fmt.Errorf("invalid credentials: %w", err)
	}
	md, ok := metadata.FromOutgoingContext(ctx)
	if ok && len(md.Get("authorization")) > 0 {
		return ctx, nil
	}
	return metadata.AppendToOutgoingContext(ctx, "authorization", fmt.Sprintf("Bearer %s", pt.APIKey)), nil
}

func (s *Store) orgStoreLocation() (string, error) {
	configDir, err := s.getConfigDir()
	if err != nil {
		return "", fmt.Errorf("get config directory: %w", err)
	}

	return filepath.Join(configDir, orgStoreDirectory), nil
}

func (s *Store) orgFilename(name string) (string, error) {
	orgDir, err := s.orgStoreLocation()
	if err != nil {
		return "", fmt.Errorf("get config directory: %w", err)
	}

	return filepath.Join(orgDir, fmt.Sprintf("%s.json", name)), nil
}

// WriteOrgInfo writes the information we have about an org to file
func (s *Store) WriteOrgInfo(o *OrgInfo) error {
	filename, err := s.orgFilename(o.Organization)
	if err != nil {
		return err
	}

	// we make sure we have whole directory structure before we create file.
	// os.MkdirAll() calls os.Stat() on path, so there is no point to do it here.
	if err = os.MkdirAll(filepath.Dir(filename), directoryMode); err != nil {
		return fmt.Errorf("create target directory: %w", err)
	}

	file, err := os.OpenFile(filename, writeFileFlags, fileMode)
	if err != nil {
		return fmt.Errorf("open configuration file: %w", err)
	}

	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(o); err != nil {
		return fmt.Errorf("serialize configuration: %w", err)
	}

	// if sync fails, we did not write into store.
	return file.Sync()
}

// ReadOrgInfo reads the information about an organization previously written to the auth store.
func (s *Store) ReadOrgInfo(orgName string) (OrgInfo, error) {
	filename, err := s.orgFilename(orgName)
	if err != nil {
		return OrgInfo{}, err
	}

	file, err := os.Open(filename)
	if err != nil {
		return OrgInfo{}, fmt.Errorf("open configuration: %w", err)
	}
	defer file.Close()

	ret := OrgInfo{}
	if err := json.NewDecoder(file).Decode(&ret); err != nil {
		return OrgInfo{}, fmt.Errorf("deserialize configuration: %w", err)
	}

	return ret, nil
}

// ListOrgs gives a list of known organizations. It works on
// filesystem level and does not attempt to read the content of configuration.
// Results are not sorted and the order may change at any time.
func (s *Store) ListOrgs() ([]string, error) {
	storeLocation, err := s.orgStoreLocation()
	if err != nil {
		return nil, fmt.Errorf("cannot find configuration store: %w", err)
	}

	globPattern := filepath.Join(storeLocation, "*.json")
	matches, err := filepath.Glob(globPattern)
	if err != nil {
		panic(fmt.Errorf("invalid glob pattern, programmer error: %w", err))
	}

	result := make([]string, 0, len(matches))
	for _, match := range matches {
		filename := filepath.Base(match)
		result = append(result, strings.TrimSuffix(filename, ".json"))
	}

	return result, nil
}
