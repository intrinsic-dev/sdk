// Copyright 2023 Intrinsic Innovation LLC

// Package root contains the root command for the inctl CLI.
package root

import (
	"context"
	"fmt"
	"os"
	"strings"

	"flag"
	log "github.com/golang/glog"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"go.opencensus.io/trace"
	"golang.org/x/exp/slices"
	intrinsic "intrinsic/production/intrinsic"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/printer"

	grpccodes "google.golang.org/grpc/codes"
	grpcstatus "google.golang.org/grpc/status"
)

const (
	// ClusterCmdName is the name of the `inctl cluster` command.
	ClusterCmdName = "cluster"
	// SolutionCmdName is the name of the `inctl solution` command.
	SolutionCmdName = "solution"
	// SolutionsCmdName is the alias for the `inctl solution` command.
	SolutionsCmdName = "solutions"
	// SkillCmdName is the name of the `inctl skill` command.
	SkillCmdName = "skill"
)

var (
	// FlagOutput holds the value of the --output flag.
	FlagOutput = printer.TextOutputFormat
)

// RootCmd is the top level command of inctl.
var RootCmd = &cobra.Command{
	Use:   "inctl",
	Short: "inctl is the Intrinsic commandline tool",
	Long:  `inctl (pronounced "in control") provides access to high-level APIs and utilities of the Intrinsic stack to application developers.`,
	// Do not print usage when a command exits with an error.
	SilenceUsage: true,
	// Silence errors so we can control how they are printed.
	SilenceErrors: true,
}

type executionContext struct {
}

// RewriteError looks at the root cause of an error and tries to add an
// actionable suggestion for how to resolve it.
func (e *executionContext) RewriteError(err error, cmdNames []string) string {
	cause := errors.Cause(err)

	// Guess the cause of the error. As these errors don't support errors.Is(), we
	// have to use typecasting and string comparison.
	if strings.HasPrefix(cause.Error(), "unknown command") {
		// Probably a Cobra error caused by an unknown top-level command (eg inctl asdf).
		return fmt.Sprintf("%v\nRun 'inctl --help' for usage.", err)
	}

	// This will also find wrapped gRPC error/statuses.
	if grpcStatus, ok := grpcstatus.FromError(cause); ok {
		if grpcStatus.Code() == grpccodes.Unauthenticated {
			return fmt.Sprintf("%v\nStored credentials are invalid. (Re-)Run 'inctl auth login'.", err)
		}

		// Restrict to certain commands. Otherwise this error hint is too noisy
		// (see b/292218614).
		if grpcStatus.Code() == grpccodes.Unavailable && len(cmdNames) > 0 &&
			slices.Contains([]string{
				ClusterCmdName, SolutionCmdName, SolutionsCmdName, SkillCmdName}, cmdNames[0]) {

			return fmt.Sprintf("%v\nThe GCP project given by --project is not reachable at the "+
				"moment or is not valid.", err)
		}
	}

	// Some commands don't have the --project flag as a hard requirement but have
	// execution paths which require it so that the correct API keys can be loaded.
	if errors.Is(cause, dialerutil.ErrCredentialsRequired) {
		return fmt.Sprintf("%v\nThe --project flag is required to load the appropriate "+
			"credentials.", err)
	}

	// User org not known
	var orgErr *orgutil.ErrOrgNotFound
	if errors.As(cause, &orgErr) {
		base := fmt.Sprintf("Credentials for given organization %q not found.", orgErr.OrgName)
		additions := []string{}
		if len(orgErr.CandidateOrgs) > 0 {
			additions = append(additions, "There's similar organizations in your store:")
			for _, org := range orgErr.CandidateOrgs {
				additions = append(additions, fmt.Sprintf(" - %s", org))
			}
		}

		if len(additions) > 0 {
			return fmt.Sprintf("%s\n%s\nTo add %q run 'inctl auth login --org %s'.", base, strings.Join(additions, "\n"), orgErr.OrgName, orgErr.OrgName)
		}

		return fmt.Sprintf("%s\nRun 'inctl auth login --org %s' to add it.", base, orgErr.OrgName)
	}

	// User not logged in.
	var credErr *dialerutil.ErrCredentialsNotFound
	if errors.As(cause, &credErr) {
		return fmt.Sprintf("%v\nCredentials for given project not found. Run "+
			"'inctl auth login --project %s'.", err, credErr.CredentialName)
	}

	return err.Error()
}

// getCommandNames returns a vector of subcommand names - e.g. ["app", "status"]
// for "inctl app status" or [] for "inctl". Returns an error if there is no
// matching command, e.g. because the user misspelled the command name(s).
//
// DO NOT CALL this before executing the root command or it might behave
// unexpectedly (e.g. for "inctl help" it will return an error instead of
// ["help"]).
func getCommandNames() ([]string, error) {
	cmd, _, err := RootCmd.Find(flag.Args())
	if err != nil {
		return nil, err
	}

	var names []string
	for node := cmd; node.HasParent(); node = node.Parent() {
		names = append([]string{node.Name()}, names...)
	}
	return names, nil
}

// Execute is the top level function that runs the app and prints any errors.
// It returns true if the command was successful.
// rewriteError rewrites an error into a helpful string.
func Execute(ec executionContext) bool {
	ctx := context.Background()
	RootCmd.SetArgs(flag.Args())

	ctx, span := trace.StartSpan(ctx, "inctl", trace.WithSampler(trace.AlwaysSample()))
	defer span.End()

	success := true
	if err := RootCmd.ExecuteContext(ctx); err != nil {
		cmdNames, _ := getCommandNames() // ignore error, cmdNames will simply be nil
		fmt.Fprintln(os.Stderr, "Error:", ec.RewriteError(err, cmdNames))
		success = false
	}

	return success
}

// Inctl launches inctl with the currently configured commands.
func Inctl() {
	intrinsic.Init()

	success := Execute(executionContext{})

	if !success {
		log.Warning("Command failed")
		os.Exit(1)
	}
}

func init() {
	RootCmd.PersistentFlags().StringVarP(
		&FlagOutput, printer.KeyOutput, "o", printer.TextOutputFormat,
		fmt.Sprintf("(optional) Output format. One of: (%s)", strings.Join(printer.AllowedFormats, ", ")))
}
