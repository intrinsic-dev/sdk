// Copyright 2023 Intrinsic Innovation LLC

package logs

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"path"
	"time"

	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
	"intrinsic/tools/inctl/auth"
)

const (
	paramSkillID    = "skillID"
	paramResourceID = "resourceName"
	paramFollow     = "follow"
	paramTimestamps = "timestamps"
	paramTailLines  = "tailLines"
	paramSinceSec   = "sinceSeconds"
)

const (
	localhostURL = "localhost:17080"
)

var (
	verboseDebug           = false
	verboseOut   io.Writer = os.Stderr
)

type endpoint struct {
	url       *url.URL
	xsrfToken string
	authToken *auth.ProjectToken
}

func getClusterName(ctx context.Context, params *cmdParams) (string, error) {
	serverAddr := fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", params.projectName)
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		Address:  serverAddr,
		CredName: params.projectName,
		CredOrg:  params.org,
	})
	if err != nil {
		return "", fmt.Errorf("could not create connection: %v", err)
	}
	defer conn.Close()

	cluster, err := solutionutil.GetClusterNameFromSolutionOrDefault(
		ctx,
		conn,
		params.solution,
		params.context,
	)
	if err != nil {
		return "", fmt.Errorf("could not resolve solution to cluster: %s", err)
	}
	return cluster, nil
}

// createEndpoint creates an endpoint for fetching logs. The endpoint contains the URL, XSRF token,
// and auth token required to fetch logs. The endpoint is different depending on whether the user
// is fetching logs from a local minikube route, a local onprem cluster via local IP route, or workcells/VMs via a cloud route.
func createEndpoint(ctx context.Context, params *cmdParams) (*endpoint, error) {
	var xsrfTokenURL *url.URL
	var authToken *auth.ProjectToken
	var localAddress string
	var clusterName string

	if params.context == "minikube" { // minikube local route
		localAddress = localhostURL
	} else if params.onpremAddress != "" { // onprem local route
		localAddress = params.onpremAddress
	} else { // cloud route
		var err error
		if params.context != "" { // if context is set, use it as the cluster name
			clusterName = params.context
		} else {
			clusterName, err = getClusterName(ctx, params)
			if err != nil {
				return nil, fmt.Errorf("could not resolve solution to cluster: %w", err)
			}
		}
	}

	if localAddress == "" {
		xsrfTokenURL = &url.URL{
			Host:   fmt.Sprintf("www.endpoints.%s.cloud.goog", params.projectName),
			Path:   fmt.Sprintf("frontend/client/%s/api/token", clusterName),
			Scheme: "https",
		}
		var err error
		authToken, err = getAuthToken(params.projectName)
		if err != nil {
			return nil, err
		}
	} else {
		xsrfTokenURL = &url.URL{
			Host:   localAddress,
			Path:   "frontend/api/token",
			Scheme: "http",
		}
	}

	xsrfToken, err := callEndpoint(ctx, http.MethodGet, xsrfTokenURL, authToken, nil, nil,
		func(_ context.Context, body io.Reader) (string, error) {
			token, err := io.ReadAll(body)
			return string(token), err
		})
	if err != nil {
		return nil, fmt.Errorf("could not obtain xsrf token: %w", err)
	}

	var logsURL *url.URL
	if localAddress != "" {
		logsURL = &url.URL{
			Host:   localAddress,
			Path:   "frontend/api/consoleLogs",
			Scheme: "http",
		}
	} else {
		logsURL = &url.URL{
			Host:   fmt.Sprintf("www.endpoints.%s.cloud.goog", params.projectName),
			Path:   fmt.Sprintf("frontend/client/%s/api/consoleLogs", clusterName),
			Scheme: "https",
		}
	}

	return &endpoint{
		url:       logsURL,
		xsrfToken: xsrfToken,
		authToken: authToken,
	}, nil
}

type bodyReader = func(context.Context, io.Reader) (string, error)

type resourceType int

const (
	rtService resourceType = iota
	rtSkill
	rtResource
)

type cmdParams struct {
	resourceType  resourceType
	resourceID    string
	follow        bool
	timestamps    bool
	tailLines     int
	projectName   string
	sinceSeconds  string
	onpremAddress string
	context       string
	solution      string
	org           string
}

func readLogsFromSolution(ctx context.Context, params *cmdParams, w io.Writer) error {
	endpoint, err := createEndpoint(ctx, params)
	if err != nil {
		return err
	}

	consoleLogsURL := endpoint.url
	consoleLogsURL.Path = path.Join(consoleLogsURL.EscapedPath(), "consoleLogs")
	consoleLogsQuery := setResourceID(params.resourceType, params.resourceID)
	if params.follow {
		consoleLogsQuery.Set(paramFollow, fmt.Sprintf("%t", params.follow))
	} else {
		consoleLogsQuery.Set(paramTailLines, fmt.Sprintf("%d", params.tailLines))
	}
	consoleLogsQuery.Set(paramTimestamps, fmt.Sprintf("%t", params.timestamps))

	if d, ok, err := parseSinceSeconds(params.sinceSeconds); ok && err == nil {
		// nit: our now is different from server now (at the time of processing),
		// so we can get drift of a second give or take
		// this is not generally problematic for this kind of logs.
		// To avoid this in the future, server should accept full timestamp, not duration
		sinceSeconds := fmt.Sprintf("%d", int64(d.Truncate(time.Second).Seconds()))
		consoleLogsQuery.Set(paramSinceSec, sinceSeconds)
	} else if err != nil {
		return fmt.Errorf("cannot parse parameter --%s: %w", keySinceSec, err)
	}

	consoleLogsURL.RawQuery = consoleLogsQuery.Encode()

	xsrfHeader := http.Header{"X-XSRF-TOKEN": []string{endpoint.xsrfToken}}

	_, err = callEndpoint(ctx, http.MethodGet, consoleLogsURL, endpoint.authToken, xsrfHeader, nil,
		func(_ context.Context, body io.Reader) (string, error) {
			if _, err := io.Copy(w, body); err != nil {
				return "", fmt.Errorf("error reading/writing logs: %w", err)
			}
			return "", nil
		})

	return err
}

func setResourceID(resType resourceType, id string) url.Values {
	result := make(url.Values)
	switch resType {
	case rtSkill:
		result.Add(paramSkillID, id)
	case rtResource:
	case rtService:
		result.Add(paramResourceID, id)
	default:
	}
	return result
}

// callEndpoint calls given endpoint URL and handles all edge cases. If response is 200 OK
// and response body processing function (bodyFx) is present, response body is passed
// for processing. Otherwise, "", nil is return value.
func callEndpoint(ctx context.Context, method string, endpoint *url.URL, authToken *auth.ProjectToken, headers http.Header, payload io.Reader, bodyFx bodyReader) (string, error) {
	if verboseDebug {
		fmt.Fprintf(verboseOut, "URL: '%s'\n", endpoint)
	}

	req, err := http.NewRequestWithContext(ctx, method, endpoint.String(), payload)
	if len(headers) > 0 {
		req.Header = headers
	}
	if err != nil {
		return "", fmt.Errorf("could not create request: %w", err)
	}

	if authToken != nil {
		req, err = authToken.HTTPAuthorization(req)
		if err != nil {
			return "", fmt.Errorf("cannot obtain credentials: %w", err)
		}
	}

	printRequest(req)
	response, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("request to target failed: %w", err)
	}
	if response.StatusCode == http.StatusNotFound {
		resourceName := endpoint.Query().Get(paramResourceID)
		return "", fmt.Errorf("'%s' is not found, please check the provided name is correct", resourceName)
	}
	if response.StatusCode != http.StatusOK {
		printResponse(response)
		return "", fmt.Errorf("unexpected response: %s", response.Status)
	}
	defer response.Body.Close()
	if bodyFx != nil {
		return bodyFx(ctx, response.Body)
	}

	// empty body consumer is valid
	return "", nil
}

// Prints request headers and body (if present) into std_err.
func printRequest(req *http.Request) {
	if !verboseDebug || req == nil {
		return
	}
	if out, err := httputil.DumpRequest(req, true); err == nil {
		fmt.Fprintln(verboseOut, "-- REQUEST ------------------------------------------")
		fmt.Fprintln(verboseOut, string(out))
		fmt.Fprintln(verboseOut, "-----------------------------------------------------")
	} else {
		fmt.Fprintf(verboseOut, "cannot print request: %s\n", err)
	}
}

// Prints response headers and body (if present) into std_err.
func printResponse(res *http.Response) {
	if !verboseDebug || res == nil {
		return
	}
	if out, err := httputil.DumpResponse(res, true); err == nil {
		fmt.Fprintln(verboseOut, "-- RESPONSE -----------------------------------------")
		fmt.Fprintln(verboseOut, string(out))
		fmt.Fprintln(verboseOut, "-----------------------------------------------------")
	} else {
		fmt.Fprintf(verboseOut, "cannot print response: %s\n", err)
	}
}

// parseSinceSeconds implements manual handling of duration parsing in order to allow
// user to specify relative duration or use RFC3339 datum format.
func parseSinceSeconds(since string) (time.Duration, bool, error) {
	if since == "" {
		return 0, false, nil
	}
	// let's try to parse duration, as that is more realistic
	if d, err := time.ParseDuration(since); err == nil {
		// duration accepts signed value, we ignore that as we cannot read logs from future
		if d < 0 {
			d = -d
		}
		return d, true, nil
	} else if verboseDebug {
		fmt.Fprintf(verboseOut, "failed to parse %s as duration (may not be an issue): %s", keySinceSec, err)
	}

	t, err := time.Parse(time.RFC3339, since)
	if err != nil {
		if verboseDebug {
			fmt.Fprintf(verboseOut, "failed to %s since as RFC-3339 time: %s", keySinceSec, err)
		}
		return 0, true, fmt.Errorf("cannot convert %s to duration", keySinceSec)

	}

	if t.After(time.Now()) {
		return 0, true, fmt.Errorf("time %s is in future, cannot proceed", keySinceSec)
	}
	return time.Now().Sub(t), true, nil
}

func getAuthToken(project string) (*auth.ProjectToken, error) {
	if project == "" {
		// No authorization required (e.g. local call in tests)
		return nil, nil
	}

	config, err := auth.NewStore().GetConfiguration(project)
	if err != nil {
		return nil, err
	}
	return config.GetDefaultCredentials()
}
