// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package create defines the skill create command.
package create

import (
	"bytes"
	"embed"
	"fmt"
	"io"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"text/template"

	"github.com/bazelbuild/buildtools/edit"
	"github.com/spf13/cobra"
	strcase "github.com/stoewer/go-strcase"
	"intrinsic/assets/idutils"
	skillCmd "intrinsic/skills/tools/skill/cmd/cmd"
	"intrinsic/tools/inctl/cmd/bazel/bazel"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/cmd/version/version"
	"intrinsic/tools/inctl/util/printer"
	"intrinsic/tools/inctl/util/templateutil"
)

type projectFolder struct {
	buildTemplateFilename string
	buildozerCommands     []string
	files                 []projectFile
}

type projectFile struct {
	extension        string
	templateFilename string
}

// Map of project folder layouts, by language key.
var projectLayouts = map[string]projectFolder{
	"python": projectFolder{
		buildTemplateFilename: "BUILD_py_fragment.template",
		buildozerCommands: []string{
			"new_load @rules_proto//proto:defs.bzl proto_library",
			"new_load @com_github_grpc_grpc//bazel:python_rules.bzl py_proto_library",
			"new_load @ai_intrinsic_sdks//bazel:skills.bzl py_skill",
			"new_load @ai_intrinsic_sdks//bazel:skills.bzl skill_manifest",
		},
		files: []projectFile{
			projectFile{
				extension:        ".py",
				templateFilename: "skill_py.template",
			},
			projectFile{
				extension:        ".proto",
				templateFilename: "skill_params_proto.template",
			},
			projectFile{
				extension:        ".manifest.textproto",
				templateFilename: "skill_py_manifest.template",
			},
		},
	},
	"cpp": projectFolder{
		buildTemplateFilename: "BUILD_cc_fragment.template",
		buildozerCommands: []string{
			"new_load @rules_proto//proto:defs.bzl proto_library",
			"new_load @rules_cc//cc:defs.bzl cc_proto_library",
			"new_load @ai_intrinsic_sdks//bazel:skills.bzl cc_skill",
			"new_load @ai_intrinsic_sdks//bazel:skills.bzl skill_manifest",
		},
		files: []projectFile{
			projectFile{
				extension:        ".h",
				templateFilename: "skill_h.template",
			},
			projectFile{
				extension:        ".cc",
				templateFilename: "skill_cc.template",
			},
			projectFile{
				extension:        ".proto",
				templateFilename: "skill_params_proto.template",
			},
			projectFile{
				extension:        ".manifest.textproto",
				templateFilename: "skill_cc_manifest.template",
			},
		},
	},
}

// Default language to generate, must be one of the keys in the projectLayouts map.
const defaultLanguage = "python"

// Get the languages for which a project can be generated.
func supportedLanguages() []string {
	var supportedLanguages = make([]string, 0, len(projectLayouts))
	for languageKey := range projectLayouts {
		supportedLanguages = append(supportedLanguages, languageKey)
	}
	sort.Strings(supportedLanguages)
	return supportedLanguages
}

func bazelWorkspaceFilenames() [2]string {
	return [2]string{"WORKSPACE", "WORKSPACE.bazel"}
}

var (
	flagWorkspaceRoot string
	flagBazelPackage  string
	flagSDKRepository string
	flagSDKVersion    string
	flagProtoPackage  string
	flagLanguage      string
	flagDryRun        bool
)

type cmdParams struct {
	argSkillID        string
	flagBazelPackage  string
	flagDryRun        bool
	flagOutput        string
	flagProtoPackage  string
	flagSDKRepository string
	flagSDKVersion    string
	flagWorkspaceRoot string
	flagLanguage      string
}

//go:embed templates/*
var embeddedTemplates embed.FS

type templateParams struct {
	SkillNameUpperSnakeCase string // e.g. "MY_MOVE"
	SkillNameUpperCamelCase string // e.g. "MyMove"
	SkillNameSnakeCase      string // e.g. "my_move"
	SkillPackageName        string // e.g. "com.my_org"

	// Package of skill parameter proto. E.g. "my_org.motion" becomes
	// ["my_org", "motion"]. Stored as a string array so that it can be
	// flexibly string-joined later.
	// - Cpp: Determines namespace of generated proto class.
	// - Python: No effect (but needs to be set so that we don't use the global
	//   namespace).
	ProtoPackage []string
	ProtoName    string

	// Bazel package (=path from WORKSPACE root to skill directory). Stored as a
	// string array so that it can be flexibly string-joined later.
	// E.g. ["motion_skills", "my_move"] for the package
	// "//motion_skills/my_move".
	BazelPackage               []string
	BazelPackageUpperSnakeCase string // e.g. "MOTION_SKILLS_MY_MOVE"
}

// parseSkillID verifies the format of the given skill id and splits it into
// package and skill name. E.g.:
//
//	"my_org.subpackage.my_move" -> ("my_org.subpackage", "my_move")
//
// If the given skill id is invalid, returns a helpful error specifying
// exactly what is wrong about the given value (e.g. which character is not
// allowed).
func parseSkillID(skillID string) (string, string, error) {

	if idutils.IsID(skillID) {
		// we validated this is actual valid ID according to runtime definition
		// following methods use the same validation so they will never return error
		// if this skillID is valid skill ID.
		pkg, _ := idutils.PackageFrom(skillID)
		name, _ := idutils.NameFrom(skillID)
		return pkg, name, nil
	}
	// So the runtime ID check failed, let's try to explain to user where they made mistake.

	// This is only executed once (globally) so these can be local variables.
	invalidCharRegexp := regexp.MustCompile("[^a-z0-9_]")
	invalidStartCharRegexp := regexp.MustCompile("^[0-9_]")
	invalidEndCharRegexp := regexp.MustCompile("_$")

	parts := strings.Split(skillID, ".")

	if len(parts) <= 2 {
		return "", "", fmt.Errorf("must be in the form com.example.skill_name (requires three segments)")
	}

	for i, part := range parts {
		partName := ""
		if i == 0 {
			partName = "package"
		} else if i == len(parts)-1 {
			partName = "name"
		} else {
			partName = "subpackage"
		}

		if part == "" {
			return "", "", fmt.Errorf("%s is empty", partName)
		}
		if invalidChar := invalidCharRegexp.FindString(part); invalidChar != "" {
			return "", "", fmt.Errorf("%s contains invalid character %q", partName, invalidChar)
		}
		if invalidChar := invalidStartCharRegexp.FindString(part); invalidChar != "" {
			return "", "", fmt.Errorf("%s may not start with %q", partName, invalidChar)
		}
		if invalidChar := invalidEndCharRegexp.FindString(part); invalidChar != "" {
			return "", "", fmt.Errorf("%s may not end with %q", partName, invalidChar)
		}
	}

	// at this point this is essentially unreachable statement as at least one of previous
	// validation were supposed to fail. If we get here, we do not validate correctly.
	return "", "", fmt.Errorf("invalid skill id, but no further information available")
}

// isBazelWorkspaceRoot checks if the directory is a Bazel workspace root.
// The given directory path does not have to exist yet.
func isBazelWorkspaceRoot(directory string) bool {
	for _, workspaceFilename := range bazelWorkspaceFilenames() {
		if _, err := os.Stat(filepath.Join(directory, workspaceFilename)); err == nil {
			return true
		}
	}

	return false
}

func createBazelWorkspaceIfNeeded(workspaceRoot string, params *cmdParams, stdout io.Writer) (bazel.InitSuccessMessage, error) {
	if isBazelWorkspaceRoot(workspaceRoot) {
		// nothing to do
		return bazel.InitSuccessMessage{}, nil
	}

	if params.flagSDKRepository == "" {
		return bazel.InitSuccessMessage{}, fmt.Errorf("bazel workspace not found at %s", workspaceRoot)
	}

	sdkVersion := params.flagSDKVersion
	if params.flagSDKVersion == "" {
		// Fallback to default SDK version
		sdkVersion = version.SDKVersion
	}

	bazelinitParams := &bazel.InitCmdParams{
		WorkspaceRoot: workspaceRoot,
		SdkRepository: params.flagSDKRepository,
		SdkVersion:    sdkVersion,
		DryRun:        params.flagDryRun,
	}

	return bazel.RunInitCmd(bazelinitParams)
}

// executeBuildozerCommands runs the given package-level buildozer commands
// (which have the form "buildozer ... //my_package:__pkg__"). Modify or
// fork this function if you need to run non-package-level buildozer commands.
func executeBuildozerCommands(cmds []string, bazelWorkspaceDir string, bazelPackage []string) error {
	opts := edit.NewOpts()
	opts.RootDir = bazelWorkspaceDir
	packageLabel := fmt.Sprintf("//%s:__pkg__", strings.Join(bazelPackage, "/"))

	for _, cmd := range cmds {
		// Capture and suppress output (buildozer uses stdout/stderr by default)
		// and only print it in case of an error (see below).
		var out, err bytes.Buffer
		opts.OutWriter = &out
		opts.ErrWriter = &err

		args := []string{cmd, packageLabel}
		result := edit.Buildozer(opts, args)

		// Buildozer return codes:
		// 0: success
		// 3: no error, but no files were modified
		if result != 0 && result != 3 {
			return fmt.Errorf("command %q returned with error code %d:\n%s",
				strings.Join(args, " "), result, err.String())
		}
	}

	return nil
}

func createOrUpdateBuildFile(bazelWorkspaceDir string, bazelPackage []string, buildozerCmds []string, params *templateParams, buildTemplateName string, templateSet *template.Template) error {
	path := filepath.Join(bazelWorkspaceDir, strings.Join(bazelPackage, "/"), "BUILD")

	// Create the file if it does not exist.
	file, err := os.OpenFile(path, os.O_RDONLY|os.O_CREATE, 0660 /*rw-rw----*/)
	if err != nil {
		return fmt.Errorf("creating file %s: %w", path, err)
	}
	file.Close()

	// Add new or update existing load statements.
	if err := executeBuildozerCommands(buildozerCmds, bazelWorkspaceDir, bazelPackage); err != nil {
		return fmt.Errorf("updating BUILD file with buildozer: %w", err)
	}

	// Append new build targets for skill.
	err = templateutil.AppendToExistingFileFromTemplate(
		path, buildTemplateName, params, templateSet)
	if err != nil {
		return fmt.Errorf("appending to %s: %w", path, err)
	}

	return nil
}

type successMessage struct {
	Message           string   `json:"message"`
	AffectedWorkspace string   `json:"affectedWorkspace"`
	AffectedFiles     []string `json:"affectedFiles"`
	Warnings          []string `json:"warnings"`
}

// String prints a successMessage in the case of --output=text.
func (msg *successMessage) String() string {
	var result strings.Builder
	result.WriteString(msg.Message)
	result.WriteString(" Affected files:\n")
	for i, affectedFile := range msg.AffectedFiles {
		if i > 0 {
			result.WriteByte('\n')
		}
		result.WriteString(filepath.Join(msg.AffectedWorkspace, affectedFile))
	}
	if msg.Warnings != nil && len(msg.Warnings) > 0 {
		result.WriteString("\nWarnings:\n")
		result.WriteString(strings.Join(msg.Warnings, "\n"))
	}
	return result.String()
}

// runCreateCmd implements the skill create command. It is the entry-point for
// unit tests and does not rely on any global state (e.g. global flag
// variables).
func runCreateCmd(params *cmdParams, stdout io.Writer) error {
	// Parse given skill ID.
	skillPackage, skillName, err := parseSkillID(params.argSkillID)
	if err != nil {
		return err
	}

	// --language flag
	if _, hasLanguage := projectLayouts[params.flagLanguage]; !hasLanguage {
		return fmt.Errorf("unknown language %s, must be one of %s",
			params.flagLanguage, strings.Join(supportedLanguages()[:], ", "))
	}

	// --proto_package flag
	protoPackage := strings.Split(skillPackage, ".")
	if params.flagProtoPackage != "" {
		protoPackage = strings.Split(params.flagProtoPackage, ".")
	}

	// --workspace_root flag
	workspaceRoot := params.flagWorkspaceRoot
	if workspaceRoot == "" {
		if workspaceRoot, err = os.Getwd(); err != nil {
			return fmt.Errorf("failed to get current working directory: %w", err)
		}
	}

	// --bazel_package flag
	if path.IsAbs(params.flagBazelPackage) {
		return fmt.Errorf("bazel-package(%s) needs to be relative to "+
			"workspace_root (%s) but is absolute", params.flagBazelPackage, workspaceRoot)
	}
	// string array so that it can be flexibly string-joined later.
	// explicitly set empty slice if flag is empty because
	// len(strings.Split("", "/")) == 1
	bazelPackage := []string{}
	bazelPackageUpperSnakeCase := ""
	if params.flagBazelPackage != "" {
		bazelPackage = strings.Split(params.flagBazelPackage, string(os.PathSeparator))
		bazelPackageUpperSnakeCase = strings.ToUpper(strings.Replace(params.flagBazelPackage, "/", "_", -1))
	}

	fullDirectoryPath := filepath.Join(workspaceRoot, params.flagBazelPackage)

	// text/template does not have a string-join by default.
	customTemplateFunctions := template.FuncMap{
		"strJoin": func(values []string, sep string) string {
			return strings.Join(values, sep)
		},
	}

	templateSet, err := template.New("").
		Funcs(customTemplateFunctions).
		ParseFS(embeddedTemplates, "templates/*.template")
	if err != nil {
		return fmt.Errorf("parsing templates: %w", err)
	}

	templParams := templateParams{
		SkillNameSnakeCase:         strcase.SnakeCase(skillName),
		SkillNameUpperSnakeCase:    strings.ToUpper(strcase.SnakeCase(skillName)),
		SkillNameUpperCamelCase:    strcase.UpperCamelCase(skillName),
		SkillPackageName:           skillPackage,
		ProtoPackage:               protoPackage,
		BazelPackage:               bazelPackage,
		BazelPackageUpperSnakeCase: bazelPackageUpperSnakeCase,
	}

	// Assemble list of files that will be created.
	buildFile := filepath.Join(fullDirectoryPath, "BUILD")
	allCreatedFiles := []string{}
	for _, projectFile := range projectLayouts[params.flagLanguage].files {
		projectFilePath := filepath.Join(fullDirectoryPath, templParams.SkillNameSnakeCase+projectFile.extension)
		allCreatedFiles = append(allCreatedFiles, projectFilePath)
	}
	sort.Strings(allCreatedFiles)

	// Check early for collisions with existing files to enable dry-runs and to
	// make the creation of the skill files more atomic. I.e. we don't want to
	// create file one and then return an error because file two already exists.
	if err = templateutil.CheckFilesDoNotExist(allCreatedFiles); err != nil {
		return err
	}

	bazelInitSuccessMsg, err := createBazelWorkspaceIfNeeded(workspaceRoot, params, stdout)
	if err != nil {
		return fmt.Errorf("%w.  If you haven't done so, you can initialize a Bazel workspace with `inctl bazel init "+
			"--sdk_repository <repo url>`", err)
	}

	if !params.flagDryRun {
		// Recursively create requested skill dir if it does not exist yet. Note
		// that from checks above we already know that we are in a Bazel workspace
		// with a WORKSPACE file, so this call is limited to creating folders inside
		// of this Bazel workspace.
		if err = os.MkdirAll(fullDirectoryPath, 0750 /*rwxr-x---*/); err != nil {
			return fmt.Errorf("creating directory %s: %w", fullDirectoryPath, err)
		}

		var projectLayout = projectLayouts[params.flagLanguage]
		err = createOrUpdateBuildFile(workspaceRoot,
			bazelPackage, projectLayout.buildozerCommands, &templParams,
			projectLayout.buildTemplateFilename, templateSet)
		if err != nil {
			return fmt.Errorf("creating or updating BUILD file: %w", err)
		}
		for _, file := range projectLayout.files {
			fullFilePath := filepath.Join(fullDirectoryPath, templParams.SkillNameSnakeCase+file.extension)
			err = templateutil.CreateNewFileFromTemplate(fullFilePath, file.templateFilename, &templParams, templateSet, templateutil.CreateFileOptions{})
			if err != nil {
				return fmt.Errorf("creating %s: %w", fullFilePath, err)
			}
		}
	}

	skillCreateSuccessMsg := successMessage{
		AffectedWorkspace: workspaceRoot,
		Warnings:          []string{},
	}
	for _, affectedFile := range append([]string{buildFile}, allCreatedFiles...) {
		relative, err := filepath.Rel(workspaceRoot, affectedFile)
		if err != nil {
			return fmt.Errorf("could not find relative path "+
				"from %s to %s: %w", workspaceRoot, affectedFile, err)
		}
		skillCreateSuccessMsg.AffectedFiles = append(skillCreateSuccessMsg.AffectedFiles, relative)
	}
	if params.flagDryRun {
		skillCreateSuccessMsg.Message = fmt.Sprintf("Will create skill %q.", params.argSkillID)
	} else {
		skillCreateSuccessMsg.Message = fmt.Sprintf("Successfully created skill %q.", params.argSkillID)
	}

	// Merge success message of bazelInit and skill create - do sanity checks on the way
	if bazelInitSuccessMsg.AffectedWorkspace != "" && bazelInitSuccessMsg.AffectedWorkspace != skillCreateSuccessMsg.AffectedWorkspace {
		return fmt.Errorf("affected workspaces of bazelInit cmd (%s) and skill create cmd (%s) do not match",
			bazelInitSuccessMsg.AffectedWorkspace,
			skillCreateSuccessMsg.AffectedWorkspace)
	}

	combinedSuccessMessage := successMessage{
		Message:           fmt.Sprintf("%s %s", bazelInitSuccessMsg.Message, skillCreateSuccessMsg.Message),
		AffectedFiles:     append(bazelInitSuccessMsg.AffectedFiles, skillCreateSuccessMsg.AffectedFiles...),
		AffectedWorkspace: bazelInitSuccessMsg.AffectedWorkspace,
		Warnings:          skillCreateSuccessMsg.Warnings,
	}

	printr, err := printer.NewPrinterWithWriter(params.flagOutput, stdout)
	if err != nil {
		return fmt.Errorf("creating printer: %w", err)
	}
	printr.Print(&combinedSuccessMessage)

	return nil
}

// NewCreateCmd creates a new create command.
func NewCreateCmd() *cobra.Command {
	createCmd := &cobra.Command{
		Use:   "create skill_id",
		Short: "Create a new skill.",
		Long:  "Create the sources and build rules for a new skill.",
		Example: `Create a skill with name "my_move" and package "com.my_org" in the current working directory:
$ inctl skill create com.my_org.my_move --proto_package my_org

Create a skill in the subfolder "my_move" of your workspace folder "/src/skill_workspace":
$ inctl skill create com.my_org.my_move --workspace_root /src/skill_workspace --bazel_package my_move

If you leave out --proto_package, the skill's package name will be used as the skill's proto package. Thus the following two calls are equivalent:
$ inctl skill create com.my_org.my_move
$ inctl skill create com.my_org.my_move --proto_package com.my_org`,
		Args:       cobra.ExactArgs(1),
		ArgAliases: []string{"skill_id"},
		RunE: func(cmd *cobra.Command, argsArray []string) error {
			params := cmdParams{
				argSkillID:        argsArray[0],
				flagWorkspaceRoot: flagWorkspaceRoot,
				flagBazelPackage:  flagBazelPackage,
				flagProtoPackage:  flagProtoPackage,
				flagSDKRepository: flagSDKRepository,
				flagSDKVersion:    flagSDKVersion,
				flagLanguage:      flagLanguage,
				flagDryRun:        flagDryRun,
				flagOutput:        root.FlagOutput,
			}

			return runCreateCmd(&params, cmd.OutOrStdout())
		},
	}

	createCmd.Flags().StringVar(&flagWorkspaceRoot, "workspace_root", "", "(optional) Path to the "+
		"root of the workspace in which to create the skill files. Defaults to the current working directory."+
		"Can either be a relative path (to the current working directory) or an absolute filesystem "+
		"path. A new workspace will be automatically created given that --sdk_repository is also "+
		"provided.")
	createCmd.Flags().StringVar(&flagBazelPackage, "bazel_package", "", "(optional) Bazel package in "+
		"which to create the skill files (e.g. 'ball_skills/throw_ball'). "+
		"Defaults to '' (the workspace root). If no BUILD file or folder is present for the given "+
		"package, they will be created.")
	createCmd.Flags().StringVar(&flagProtoPackage, "proto_package", "", "(optional) Proto package "+
		"for the skills parameter proto. It is recommended to set this explicitly, otherwise defaults "+
		"to the skills package (=the package portion of the given skill ID).")
	createCmd.Flags().StringVar(&flagSDKRepository, "sdk_repository", "", "(optional) Git repository from which "+
		"to fetch the Intrinsic SDK, e.g., "+
		"\"https://intrinsic.googlesource.com/xfa-prod-happy-hippo/intrinsic_sdks.git\". Only required if "+
		"workspace_root is not yet a Bazel workspace.")
	createCmd.Flags().StringVar(&flagSDKVersion, "sdk_version", "", "(optional) Version of the "+
		"Intrinsic SDK to fetch. Only required if workspace_root is not yet a Bazel workspace.")
	createCmd.Flags().StringVar(&flagLanguage, "language", defaultLanguage, "(optional) Implementation language to"+
		" generate ("+strings.Join(supportedLanguages()[:], ", ")+", default "+defaultLanguage+").")
	createCmd.Flags().BoolVar(&flagDryRun, "dry_run", false, "(optional) If set, no files will be "+
		"created or modified.")

	return createCmd
}

func init() {
	skillCmd.SkillCmd.AddCommand(NewCreateCmd())
}
