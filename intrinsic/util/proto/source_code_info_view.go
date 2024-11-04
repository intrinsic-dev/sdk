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

type pathInfo struct {
	// The message (or service) that this path is associated with.
	messageName string
	// The full name. This will equal messageName for top-level message or service
	// comments. Message fields or service methods will equal the message name
	// with an added suffix.
	fullName       string
	leadingComment string
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

func addPath(md protoreflect.Descriptor, d protoreflect.Descriptor, paths map[string]pathInfo) {
	filePath := md.ParentFile().Path()
	sourcePath := md.ParentFile().SourceLocations().ByDescriptor(d).Path
	paths[toString(filePath, sourcePath)] = pathInfo{
		messageName:    string(md.FullName()),
		fullName:       string(d.FullName()),
		leadingComment: md.ParentFile().SourceLocations().ByDescriptor(d).LeadingComments,
	}
}

func addMessageDependencies(index int, md protoreflect.MessageDescriptor, graph map[string]map[string]struct{}, paths map[string]pathInfo) {
	// This is the comment of a proto message definition.
	addPath(md, md, paths)

	from := string(md.FullName())
	addEdge(from, from, graph)
	for i := 0; i < md.Fields().Len(); i++ {
		fd := md.Fields().Get(i)
		// This is the comment associated with a field in the proto message.
		addPath(md, fd, paths)
		if fd.Kind() == protoreflect.MessageKind {
			to := string(fd.Message().FullName())
			addEdge(from, to, graph)
		}
	}

	// Process nested proto messages.
	for i := 0; i < md.Messages().Len(); i++ {
		nested := md.Messages().Get(i)
		addMessageDependencies(index, nested, graph, paths)
	}
}

func addServiceDependencies(index int, sd protoreflect.ServiceDescriptor, graph map[string]map[string]struct{}, paths map[string]pathInfo) {
	// This is the comment of a gRPC service definition.
	addPath(sd, sd, paths)

	from := string(sd.FullName())
	addEdge(from, from, graph)
	for i := 0; i < sd.Methods().Len(); i++ {
		md := sd.Methods().Get(i)
		// // This is the comment associated with a method of a service.
		addPath(sd, md, paths)

		// Add the method's input proto as a dependency.
		im := md.Input()
		to := string(im.FullName())
		addEdge(from, to, graph)
		// Add the method's output proto as a dependency.
		om := md.Output()
		to = string(om.FullName())
		addEdge(from, to, graph)
	}
}

func dependencyGraph(fds *dpb.FileDescriptorSet) (map[string]map[string]struct{}, map[string]pathInfo, error) {
	// A map between full message names to set of direct dependencies.
	graph := map[string]map[string]struct{}{}
	// A set of descriptor location "paths" that we need to retain. These paths
	// currently hold message, nested messages, and message field descriptors. All
	// other sources will be pruned.
	pathsWithFile := map[string]pathInfo{}

	files, err := protodesc.NewFiles(fds)
	if err != nil {
		return nil, nil, err
	}
	files.RangeFiles(func(f protoreflect.FileDescriptor) bool {
		for i := 0; i < f.Messages().Len(); i++ {
			md := f.Messages().Get(i)
			addMessageDependencies(i, md, graph, pathsWithFile)
		}
		for i := 0; i < f.Services().Len(); i++ {
			sd := f.Services().Get(i)
			addServiceDependencies(i, sd, graph, pathsWithFile)
		}
		return true
	})
	return graph, pathsWithFile, nil
}

func allDependencies(fullNames []string, graph map[string]map[string]struct{}) map[string]struct{} {
	deps := map[string]struct{}{}
	stack := []string{}
	for _, fullName := range fullNames {
		if _, exists := graph[fullName]; exists {
			stack = append(stack, fullName)
		}
	}
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

// NestedFieldCommentMap returns a mapping of fully qualified messages and
// fields to the leading comments of those fields. This is useful for turning
// comments in proto files into tooltips in the UI.
func NestedFieldCommentMap(protoDescriptors *dpb.FileDescriptorSet, messageFullName string) (map[string]string, error) {
	if len(protoDescriptors.GetFile()) == 0 {
		return nil, fmt.Errorf("a FileDescriptorSet is required, but %v was given instead", protoDescriptors)
	}

	depGraph, pathsWithFile, err := dependencyGraph(protoDescriptors)
	if err != nil {
		return nil, err
	}
	depSet := allDependencies([]string{messageFullName}, depGraph)
	if _, exists := depSet[messageFullName]; !exists {
		return nil, fmt.Errorf("did not find message %v in given file descriptor set", messageFullName)
	}

	comments := map[string]string{}
	for _, file := range protoDescriptors.GetFile() {
		locations := file.GetSourceCodeInfo().GetLocation()
		for _, l := range locations {
			pi, exists := pathsWithFile[toString(file.GetName(), protoreflect.SourcePath(l.Path))]
			if !exists {
				continue
			}
			if _, exists := depSet[pi.messageName]; exists {
				comments[pi.fullName] = pi.leadingComment
			}
		}
	}
	return comments, nil
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
