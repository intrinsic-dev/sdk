// Copyright 2023 Intrinsic Innovation LLC

// Package sourcecodeinfoview offers tools for working with SourceCodeInfo in proto descriptors.
package sourcecodeinfoview

import (
	"fmt"
	"slices"

	dpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoreflect"
)

// GetNestedFieldCommentMap returns a mapping of fully qualified messages and fields to the leading comments of those fields.
// This is useful for turning comments in proto files into tooltips in the UI.
func GetNestedFieldCommentMap(protoDescriptors *dpb.FileDescriptorSet, messageFullName string) (map[string]string, error) {
	if len(protoDescriptors.GetFile()) == 0 {
		return nil, fmt.Errorf("a FileDescriptorSet is required, but %v was given instead", protoDescriptors)
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
					if !slices.Contains(deps, typeName) {
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
		if slices.Contains(namesToKeep, currentFullName) {
			continue
		}
		namesToKeep = append(namesToKeep, currentFullName)
		for _, f := range messageFields[currentFullName] {
			namesToKeep = append(namesToKeep, f)
		}
		for _, dep := range messageDependencies[currentFullName] {
			if !slices.Contains(fullNameQueue, dep) {
				fullNameQueue = append(fullNameQueue, dep)
			}
		}
	}
	// Filter anything we don't want to keep.
	for name := range nestedLeadingComments {
		if !slices.Contains(namesToKeep, name) {
			delete(nestedLeadingComments, name)
		}
	}

	return nestedLeadingComments, nil
}

func toString(file string, path protoreflect.SourcePath) string {
	return fmt.Sprintf("%s %s", file, path.String())
}

func addEdge(from string, to string, graph map[string]map[string]struct{}) {
	if _, exists := graph[from]; !exists {
		graph[from] = map[string]struct{}{}
	}
	graph[from][to] = struct{}{}
}

func addMessageDependencies(index int, md protoreflect.MessageDescriptor, graph map[string]map[string]struct{}, paths map[string]struct{}) {
	filePath := md.ParentFile().Path()
	from := string(md.FullName())
	for i := 0; i < md.Fields().Len(); i++ {
		fd := md.Fields().Get(i)
		sourcePath := md.ParentFile().SourceLocations().ByDescriptor(fd).Path
		paths[toString(filePath, sourcePath)] = struct{}{}
		if fd.Kind() == protoreflect.MessageKind {
			to := string(fd.Message().FullName())
			addEdge(from, to, graph)
		}
	}

	for i := 0; i < md.Messages().Len(); i++ {
		nested := md.Messages().Get(i)
		sourcePath := md.ParentFile().SourceLocations().ByDescriptor(nested).Path
		paths[toString(filePath, sourcePath)] = struct{}{}
		addMessageDependencies(index, nested, graph, paths)
	}
}

func addServiceDependencies(index int, sd protoreflect.ServiceDescriptor, graph map[string]map[string]struct{}, paths map[string]struct{}) {
	filePath := sd.ParentFile().Path()
	from := string(sd.FullName())
	for i := 0; i < sd.Methods().Len(); i++ {
		md := sd.Methods().Get(i)
		sourcePath := sd.ParentFile().SourceLocations().ByDescriptor(md).Path
		paths[toString(filePath, sourcePath)] = struct{}{}

		// Add the method's input proto.
		im := md.Input()
		to := string(im.FullName())
		addEdge(from, to, graph)

		// Add the method's output proto.
		om := md.Output()
		to = string(om.FullName())
		addEdge(from, to, graph)
	}
}

func dependencyGraph(fds *dpb.FileDescriptorSet) (map[string]map[string]struct{}, map[string]struct{}, error) {
	// A map between full message names to set of direct dependencies.
	graph := map[string]map[string]struct{}{}
	// A set of descriptor location "paths" that we need to retain. These paths
	// currently hold message, nested messages, and message field descriptors. All
	// other sources will be pruned.
	pathsWithFile := map[string]struct{}{}

	files, err := protodesc.NewFiles(fds)
	if err != nil {
		return nil, nil, err
	}
	files.RangeFiles(func(f protoreflect.FileDescriptor) bool {
		for i := 0; i < f.Messages().Len(); i++ {
			md := f.Messages().Get(i)
			sourcePath := f.SourceLocations().ByDescriptor(md).Path
			pathsWithFile[toString(f.Path(), sourcePath)] = struct{}{}
			addMessageDependencies(i, md, graph, pathsWithFile)
		}
		for i := 0; i < f.Services().Len(); i++ {
			sd := f.Services().Get(i)
			sourcePath := f.SourceLocations().ByDescriptor(sd).Path
			pathsWithFile[toString(f.Path(), sourcePath)] = struct{}{}
			addServiceDependencies(i, sd, graph, pathsWithFile)
		}
		return true
	})
	return graph, pathsWithFile, nil
}

func allDependencies(fullNames []string, graph map[string]map[string]struct{}) map[string]struct{} {
	deps := map[string]struct{}{}
	stack := slices.Clone(fullNames)
	for len(stack) > 0 {
		popped := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if _, exists := deps[popped]; !exists {
			deps[popped] = struct{}{}
			neighbors, _ := graph[popped]
			for fn := range neighbors {
				stack = append(stack, fn)
			}
		}
	}
	return deps
}

func anyMessageInDepSet(file *dpb.FileDescriptorProto, depSet map[string]struct{}) bool {
	pkg := file.GetPackage()
	for _, mt := range file.GetMessageType() {
		fullName := pkg + "." + mt.GetName()
		if _, exists := depSet[fullName]; exists {
			return true
		}
	}
	return false
}

// PruneSourceCodeInfo removes comments and other source code information. It
// always retains comments that are needed by the passed in list of message type
// names and their transitive dependencies. Leading detached comments are
// always removed.
func PruneSourceCodeInfo(fullNames []string, fds *dpb.FileDescriptorSet) error {
	depGraph, pathsWithFile, err := dependencyGraph(fds)
	if err != nil {
		return err
	}
	depSet := allDependencies(fullNames, depGraph)

	for _, file := range fds.GetFile() {

		// We keep comments in any file that contains at least one message that
		// belong to the set of transitive dependencies.
		if !anyMessageInDepSet(file, depSet) {
			file.SourceCodeInfo = nil
			continue
		}

		// Remove all leading detached comments and spans as we do not need them.
		locations := file.GetSourceCodeInfo().GetLocation()
		for _, l := range locations {
			l.LeadingDetachedComments = nil
		}

		// Remove source locations that don't point to a proto message location.
		file.GetSourceCodeInfo().Location = slices.DeleteFunc(locations, func(l *dpb.SourceCodeInfo_Location) bool {
			_, exists := pathsWithFile[toString(file.GetName(), protoreflect.SourcePath(l.Path))]
			return !exists
		})
	}
	return nil
}
