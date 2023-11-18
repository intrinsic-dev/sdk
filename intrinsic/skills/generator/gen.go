// Copyright 2023 Intrinsic Innovation LLC

// Package gen provides code generation utilities for generating skills
package gen

import (
	"bufio"
	"embed"
	"fmt"
	"os"
	"strings"
	"text/template"

	"google.golang.org/protobuf/proto"
	manifestpb "intrinsic/skills/proto/skill_manifest_go_proto"
)

type templateCCParameters struct {
	CCHeaderPaths          []string
	ParameterDescriptorPtr string
	ReturnDescriptorPtr    string
	CreateSkillMethod      string
}

type templatePyParameters struct {
	PythonModules        []string
	ParameterDescriptor  string
	ReturnTypeDescriptor string
	CreateSkillMethod    string
}

//go:embed skill_service_main_tmpl.cc
//go:embed skill_service_main.py.tmpl
var embeddedTemplate embed.FS

func writeCCTemplateOutput(parameters templateCCParameters, out string) error {
	template, err := template.New("skill_service_main_tmpl.cc").
		Funcs(template.FuncMap{"join": strings.Join}).
		ParseFS(embeddedTemplate, "skill_service_main_tmpl.cc")
	if err != nil {
		return fmt.Errorf("cannot parse template: %v", err)
	}

	f, err := os.Create(out)
	if err != nil {
		return fmt.Errorf("cannot create file %q: %v", out, err)
	}
	defer f.Close()

	w := bufio.NewWriter(f)
	if err := template.Execute(w, parameters); err != nil {
		return fmt.Errorf("cannot populate: %v", err)
	}
	return w.Flush()
}

func writePyTemplateOutput(parameters templatePyParameters, out string) error {
	template, err := template.New("skill_service_main.py.tmpl").
		ParseFS(embeddedTemplate, "skill_service_main.py.tmpl")
	if err != nil {
		return fmt.Errorf("cannot parse template: %v", err)
	}

	f, err := os.Create(out)
	if err != nil {
		return fmt.Errorf("cannot create file %q: %v", out, err)
	}
	defer f.Close()

	w := bufio.NewWriter(f)
	if err := template.Execute(w, parameters); err != nil {
		return fmt.Errorf("cannot populate: %v", err)
	}
	return w.Flush()
}

func readSkillManifest(path string) (*manifestpb.Manifest, error) {
	manifestBinary, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("cannot read file: %v", err)
	}
	manifest := &manifestpb.Manifest{}
	if err := proto.Unmarshal(manifestBinary, manifest); err != nil {
		return nil, fmt.Errorf("cannot unmarshal binary to proto: %v", err)
	}
	return manifest, nil
}

func ccDescriptorPointerFrom(protoMessageFullName string) string {
	if protoMessageFullName == "" {
		return "nullptr"
	}
	return "::" + strings.ReplaceAll(protoMessageFullName, ".", "::") + "::descriptor()"
}

func lastString(parts []string) string {
	if len(parts) == 0 {
		return ""
	}

	if len(parts) == 1 {
		return parts[0]
	}

	return parts[len(parts)-1]
}

func pyDescriptorFrom(protoModule, protoMessageFullName string) string {
	if protoMessageFullName == "" {
		return "None"
	}
	return protoModule + "." + lastString(strings.Split(protoMessageFullName, ".")) + ".DESCRIPTOR"
}

// WriteSkillServiceCC writes a skill service main to the file at out.
//
// The manifestPath must refer to a file that contains an intrinsic_proto.skills.Manifest
// proto binary. ccHeaderPaths are the path(s) to the proto header file(s) for the skill's
// protobuf schema(s). out is the file path to write the generated service main to.
//
// The template is specified at skill_service_main_tmpl.cc
func WriteSkillServiceCC(manifestPath string, ccHeaderPaths []string, out string) error {
	manifest, err := readSkillManifest(manifestPath)
	if err != nil {
		return fmt.Errorf("cannot read manifest: %v", err)
	}

	return writeCCTemplateOutput(
		templateCCParameters{
			CCHeaderPaths:          ccHeaderPaths,
			ParameterDescriptorPtr: ccDescriptorPointerFrom(manifest.GetParameter().GetMessageFullName()),
			ReturnDescriptorPtr:    ccDescriptorPointerFrom(manifest.GetReturnType().GetMessageFullName()),
			CreateSkillMethod:      manifest.GetOptions().GetCcConfig().GetCreateSkill(),
		},
		out,
	)
}

// WriteSkillServicePy writes a skill service main to the file at out.
//
// The manifestPath must refer to a file that contains an intrinsic_proto.skills.Manifest
// proto binary. pyModules are the module(s) to to import for the skill, these must at least include
// the module where the skill create method is declared and the proto schema modules for the skill.
// out is the file path to write the generated service main to.
//
// The template is specified at skill_service_main_tmpl.py
func WriteSkillServicePy(manifestPath string, out string) error {
	manifest, err := readSkillManifest(manifestPath)
	if err != nil {
		return fmt.Errorf("cannot read manifest: %v", err)
	}

	return writePyTemplateOutput(
		templatePyParameters{
			PythonModules: []string{
				manifest.GetOptions().GetPythonConfig().GetSkillModule(),
				manifest.GetOptions().GetPythonConfig().GetProtoModule(),
			},
			ParameterDescriptor: pyDescriptorFrom(
				manifest.GetOptions().GetPythonConfig().GetProtoModule(),
				manifest.GetParameter().GetMessageFullName()),
			ReturnTypeDescriptor: pyDescriptorFrom(
				manifest.GetOptions().GetPythonConfig().GetProtoModule(),
				manifest.GetReturnType().GetMessageFullName()),
			CreateSkillMethod: manifest.GetOptions().GetPythonConfig().GetCreateSkill(),
		},
		out,
	)
}
