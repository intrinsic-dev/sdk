// Copyright 2023 Intrinsic Innovation LLC

// Package sourcecodeinfoview offers tools for working with SourceCodeInfo in proto descriptors.
package sourcecodeinfoview

import (
	"fmt"
	slice "slices"

	dpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
)

// GetNestedFieldCommentMap returns a mapping of fully qualified messages and fields to the leading comments of those fields.
// This is useful for turning comments in proto files into tooltips in the UI.
func GetNestedFieldCommentMap(protoDescriptors *dpb.FileDescriptorSet, messageFullName string) (map[string]string, error) {
	if len(protoDescriptors.GetFile()) == 0 {
		return nil, fmt.Errorf("a FileDescriptorSet is required, but %v was given instead", protoDescriptors)
	}

	// Validate that we have source code info to work with
	for _, file := range protoDescriptors.GetFile() {
		if file.GetSourceCodeInfo() == nil {
			return nil, fmt.Errorf("file %v has no source code info", file.GetName())
		}
	}

	// key: fully qualified name of message or field; value: leading comments
	nestedLeadingComments := make(map[string]string)

	// We need to filter out messages we don't depend on, so create an adjacency list.
	// key: message full name; value: list of message names it depends on
	messageDependencies := make(map[string][]string)
	// key: message full name; value: list of fields it has
	messageFields := make(map[string][]string)
	for _, file := range protoDescriptors.GetFile() {
		packageName := file.GetPackage()
		// Gather all paths to message names into a map to make it easier to look them up later.
		// key: SourceCodeInfo_Locarion.path represented as a string, value: full name of thing at that path
		pathToFullName := make(map[string]string)

		for mIdx, messageType := range file.GetMessageType() {
			deps := []string{}
			currentMessageFullName := fmt.Sprintf("%v.%v", packageName, messageType.GetName())
			// Path: (FileDescriptorProto.message_type = 4) (the mIdx message_type)
			path := fmt.Sprintf("%v", []int32{4, int32(mIdx)})
			pathToFullName[path] = currentMessageFullName
			for fIdx, field := range messageType.GetField() {
				fullName := fmt.Sprintf("%v.%v", currentMessageFullName, field.GetName())
				// Path: (FileDescriptorProto.message_type = 4) (the mIdx message_type) (DescriptorProto.field = 2) (the fIdx field)
				path := fmt.Sprintf("%v", []int32{4, int32(mIdx), 2, int32(fIdx)})
				pathToFullName[path] = fullName
				messageFields[currentMessageFullName] = append(messageFields[currentMessageFullName], fullName)

				// Figure out dependencies on other messages
				if field.GetType() == dpb.FieldDescriptorProto_TYPE_MESSAGE {
					typeName := field.GetTypeName()
					if len(typeName) < 1 {
						return nil, fmt.Errorf("field type name is empty")
					}
					if typeName[0] == '.' {
						typeName = typeName[1:]
					}
					if !slice.Contains(deps, typeName) {
						deps = append(deps, typeName)
					}
				}
			}
			messageDependencies[currentMessageFullName] = deps
		}

		for _, loc := range file.GetSourceCodeInfo().GetLocation() {
			if fullName, ok := pathToFullName[fmt.Sprintf("%v", loc.GetPath())]; ok {
				nestedLeadingComments[fullName] = loc.GetLeadingComments()
			}
		}
	}

	if _, ok := nestedLeadingComments[messageFullName]; !ok {
		return nil, fmt.Errorf("did not find message %v in given file descriptor set", messageFullName)
	}

	// Figure out which comments using breadth first traversal starting from the target message.
	// key: SourceCodeInfo_Location.path represented as a string, value: name of thing at that path
	namesToKeep := []string{}
	fullNameQueue := []string{messageFullName}
	for len(fullNameQueue) > 0 {
		var currentFullName string
		currentFullName, fullNameQueue = fullNameQueue[0], fullNameQueue[1:]
		if slice.Contains(namesToKeep, currentFullName) {
			continue
		}
		namesToKeep = append(namesToKeep, currentFullName)
		for _, f := range messageFields[currentFullName] {
			namesToKeep = append(namesToKeep, f)
		}
		for _, dep := range messageDependencies[currentFullName] {
			if !slice.Contains(fullNameQueue, dep) {
				fullNameQueue = append(fullNameQueue, dep)
			}
		}
	}
	// Filter anything we don't want to keep.
	for name := range nestedLeadingComments {
		if !slice.Contains(namesToKeep, name) {
			delete(nestedLeadingComments, name)
		}
	}

	return nestedLeadingComments, nil
}
