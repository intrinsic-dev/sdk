// Copyright 2023 Intrinsic Innovation LLC

// Package logs defines a skill logs command which prints skill logs.
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

	"github.com/spf13/cobra"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/imageutils"
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
	"intrinsic/tools/inctl/auth"
)

const (
	keyFollow       = "follow"
	keyTimestamps   = "timestamps"
	keyTailLines    = "tail"
	keySinceSec     = "since"
	paramSkillID    = "skillID"
	paramFollow     = "follow"
	paramTimestamps = "timestamps"
	paramTailLines  = "tailLines"
	paramSinceSec   = "sinceSeconds"

	verboseDebugEnvName = "INTRINSIC_DEBUG_OUTPUT"

	platformUser = "user" // For now we have only single user
)

const (
	localhostURL = "localhost:17080"
)

var (
	verboseDebug           = false
	verboseOut   io.Writer = os.Stderr
)

var cmdFlags = cmdutils.NewCmdFlags()

type bodyReader = func(context.Context, io.Reader) (string, error)

func createFrontendURL(projectName string, clusterName string) *url.URL {
	var frontendURL url.URL
	if projectName == "" {
		frontendURL = url.URL{Host: localhostURL, Path: "frontend/api", Scheme: "http"}
	} else {
		frontendURL = url.URL{
			Host:   fmt.Sprintf("www.endpoints.%s.cloud.goog", projectName),
			Path:   fmt.Sprintf("frontend/client/%s/api", clusterName),
			Scheme: "https",
		}
	}
	return &frontendURL
}

type cmdParams struct {
	targetType  imageutils.TargetType
	target      string
	frontendURL *url.URL
	follow      bool
	timestamps  bool
	tailLines   int
	projectName string
}

func runLogsCmd(ctx context.Context, params *cmdParams, w io.Writer) error {
	skillID := ""
	var err error
	switch params.targetType {
	case imageutils.Build:
		skillID, err = imageutils.ExtractSkillIDFromBuildTargetLabel(params.target)
		if err != nil {
			return fmt.Errorf(
				"could not extract a skill id from the given build target %s: %w",
				params.target, err)
		}
	case imageutils.ID:
		skillID = params.target
	default:
		return fmt.Errorf("unknown or missing target type, select one of: %s, %s",
			imageutils.ID, imageutils.Build)
	}

	verboseOut.Write([]byte(fmt.Sprintf("%s\n", params.frontendURL.Path)))
	tokenURL := *params.frontendURL
	tokenURL.Path = path.Join(tokenURL.EscapedPath(), "token")
	authToken, err := getAuthToken(params.projectName)
	if err != nil {
		return err
	}

	xsrfToken, err := callEndpoint(ctx, http.MethodGet, &tokenURL, authToken, nil, nil,
		func(_ context.Context, body io.Reader) (string, error) {
			token, err := io.ReadAll(body)
			return string(token), err
		})
	if err != nil {
		return fmt.Errorf("could not obtain xsrf token: %w", err)
	}

	consoleLogsURL := *params.frontendURL
	consoleLogsURL.Path = path.Join(consoleLogsURL.EscapedPath(), "consoleLogs")
	consoleLogsQuery := make(url.Values)
	consoleLogsQuery.Set(paramSkillID, skillID)
	if params.follow {
		consoleLogsQuery.Set(paramFollow, fmt.Sprintf("%t", params.follow))
	} else {
		consoleLogsQuery.Set(paramTailLines, fmt.Sprintf("%d", params.tailLines))
	}
	consoleLogsQuery.Set(paramTimestamps, fmt.Sprintf("%t", params.timestamps))

	if d, ok, err := parseSinceSeconds(cmdFlags.GetString(keySinceSec)); ok && err == nil {
		// nit: our now is different from server now (at the time of processing),
		// so we can get drift of a second give or take
		// this is not generally problematic for this kind of logs.
		// To avoid this in the future, server should accept full timestamp, not duration
		sinceSeconds := fmt.Sprintf("%d", int64(d.Truncate(time.Second).Seconds()))
		consoleLogsQuery.Set(paramSinceSec, sinceSeconds)
	} else if err != nil {
		return fmt.Errorf("cannot parse parameter %s: %w", keySinceSec, err)
	}

	consoleLogsURL.RawQuery = consoleLogsQuery.Encode()

	xsrfHeader := http.Header{"X-XSRF-TOKEN": []string{xsrfToken}}

	_, err = callEndpoint(ctx, http.MethodGet, &consoleLogsURL, authToken, xsrfHeader, nil,
		func(_ context.Context, body io.Reader) (string, error) {
			if _, err := io.Copy(w, body); err != nil {
				return "", fmt.Errorf("error reading/writing logs: %w", err)
			}
			return "", nil
		})

	return err
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

var logsCmd = &cobra.Command{
	Use:   "logs --type=TYPE TARGET",
	Short: "Print skill logs",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		target := args[0]

		// we do not care about value, but about presence
		_, verboseDebug = os.LookupEnv(verboseDebugEnvName)
		verboseOut = cmd.OutOrStderr()

		context := cmdFlags.GetString(cmdutils.KeyContext)
		project := cmdFlags.GetFlagProject()
		org := cmdFlags.GetFlagOrganization()
		var serverAddr string
		if context == "minikube" {
			serverAddr = localhostURL
			project = ""
		} else {
			serverAddr = fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", project)
		}
		solution := cmdFlags.GetString(cmdutils.KeySolution)

		ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
			Address:  serverAddr,
			CredName: project,
			CredOrg:  org,
		})
		if err != nil {
			return fmt.Errorf("could not create connection: %v", err)
		}
		defer conn.Close()

		cluster, err := solutionutil.GetClusterNameFromSolutionOrDefault(
			ctx,
			conn,
			solution,
			context,
		)
		if err != nil {
			return fmt.Errorf("could not resolve solution to cluster: %s", err)
		}

		return runLogsCmd(ctx, &cmdParams{
			targetType:  imageutils.TargetType(cmdFlags.GetString(cmdutils.KeyType)),
			target:      target,
			frontendURL: createFrontendURL(project, cluster),
			follow:      cmdFlags.GetBool(keyFollow),
			timestamps:  cmdFlags.GetBool(keyTimestamps),
			tailLines:   cmdFlags.GetInt(keyTailLines),
			projectName: project,
		}, cmd.OutOrStdout())
	},
}

func init() {
	cmd.SkillCmd.AddCommand(logsCmd)
	cmdFlags.SetCommand(logsCmd)

	cmdFlags.AddFlagsProjectOrg()
	cmdFlags.OptionalEnvString(cmdutils.KeyContext, "", "The Kubernetes cluster to use.")
	cmdFlags.OptionalEnvString(cmdutils.KeySolution, "", "The solution to use.")

	cmdFlags.RequiredString(cmdutils.KeyType, fmt.Sprintf(`The target's type:
%s	skill id
%s	build target of the skill image`, imageutils.ID, imageutils.Build))
	cmdFlags.OptionalBool(keyFollow, false, "Whether to follow the skill logs.")
	cmdFlags.OptionalBool(keyTimestamps, false, "Whether to include timestamps on each log line.")
	cmdFlags.OptionalInt(keyTailLines, 10, "The number of recent log lines to display. An input number less than 0 shows all log lines.")
	cmdFlags.OptionalString(keySinceSec, "", "Show logs starting since value. Value is either relative (e.g 10m) or \ndate time in RFC3339 format (e.g: 2006-01-02T15:04:05Z07:00)")

	logsCmd.MarkFlagsMutuallyExclusive(cmdutils.KeyContext, cmdutils.KeySolution)
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
