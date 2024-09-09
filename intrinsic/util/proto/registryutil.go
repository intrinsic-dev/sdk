// Copyright 2023 Intrinsic Innovation LLC

// Package registryutil defines common functions for working with protoregistry
// types.
package registryutil

import (
	"fmt"

	descriptorpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	dynamicpb "google.golang.org/protobuf/types/dynamicpb"
	"intrinsic/util/proto/protoio"
)

// LoadFileDescriptorSets loads a list of binary proto files from disk and returns a
// populated FileDescriptorSet proto.  An empty set of paths returns a nil set.
func LoadFileDescriptorSets(paths []string) (*descriptorpb.FileDescriptorSet, error) {
	if len(paths) == 0 {
		return nil, nil
	}
	set := &descriptorpb.FileDescriptorSet{}
	for _, path := range paths {
		if err := protoio.ReadBinaryProto(path, set, protoio.WithMerge(true)); err != nil {
			return nil, fmt.Errorf("failed to read file descriptor set %q: %v", path, err)
		}
	}
	return set, nil
}

// NewFilesFromFileDescriptorSets creates a protoregistry Files object from a
// set of binary proto files on disk.  The set of files is required to be
// complete, as unresolved paths will result in an error.  If the set is nil,
// nil files will be returned.
func NewFilesFromFileDescriptorSets(paths []string) (*protoregistry.Files, error) {
	set, err := LoadFileDescriptorSets(paths)
	if err != nil {
		return nil, err
	}
	if set == nil {
		return nil, nil
	}

	files, err := protodesc.NewFiles(set)
	if err != nil {
		return nil, fmt.Errorf("failed to create a new proto descriptor: %v", err)
	}

	return files, nil
}

// NewTypesFromFileDescriptorSetOptions contains options for
// NewTypesFromFileDescriptorSetWithOptions.
type NewTypesFromFileDescriptorSetOptions struct {
	// BaseTypes is a registry in which to look for existing types before falling back to generating a
	// new type using dynamicpb.
	//
	// NOTE: Types are only matched by full name, rather than a full comparison of descriptors.
	BaseTypes *protoregistry.Types
}

// NewTypesFromFileDescriptorSet creates a new protoregistry Types from a complete file descriptor
// set.  Unresolved paths will result in an error.  A nil set returns a nil types.
//
// NOTE: Returned types will be generated using dynamicpb, regardless of whether the concrete type
// is known (e.g., in the global registry).
func NewTypesFromFileDescriptorSet(set *descriptorpb.FileDescriptorSet) (*protoregistry.Types, error) {
	return NewTypesFromFileDescriptorSetWithOptions(set, nil)
}

// NewTypesFromFileDescriptorSetWithOptions creates a new protoregistry Types from a complete file
// descriptor set.  Unresolved paths will result in an error.  A nil set returns a nil types.
//
// NOTE: Returned types will be drawn from opts.BaseTypes if present and generated using dynamicpb
// otherwise.
func NewTypesFromFileDescriptorSetWithOptions(set *descriptorpb.FileDescriptorSet, opts *NewTypesFromFileDescriptorSetOptions) (*protoregistry.Types, error) {
	if opts == nil {
		opts = &NewTypesFromFileDescriptorSetOptions{}
	}

	if set == nil {
		return new(protoregistry.Types), nil
	}

	files, err := protodesc.NewFiles(set)
	if err != nil {
		return nil, fmt.Errorf("failed to create a new proto descriptor: %v", err)
	}

	types := new(protoregistry.Types)
	if err := PopulateTypesFromFilesWithOptions(types, files, &PopulateTypesFromFilesOptions{
		BaseTypes: opts.BaseTypes,
	}); err != nil {
		return nil, fmt.Errorf("failed to populate the registry: %v", err)
	}

	return types, nil
}

// PopulateTypesFromFilesOptions contains options for PopulateTypesFromFilesWithOptions.
type PopulateTypesFromFilesOptions struct {
	// BaseTypes is a registry in which to look for existing types before falling back to generating a
	// new type using dynamicpb.
	//
	// NOTE: Types are only matched by full name, rather than a full comparison of descriptors.
	BaseTypes *protoregistry.Types
}

// PopulateTypesFromFiles adds in all Messages, Enums, and Extensions held within a Files object
// into the provided Type. `t“ may be modified prior to returning an error.  Types from `f“ that
// already exist in `t` will be ignored.
//
// NOTE: Returned types will be generated using dynamicpb, regardless of whether the concrete type
// is known (e.g., in the global registry).
func PopulateTypesFromFiles(t *protoregistry.Types, f *protoregistry.Files) error {
	return PopulateTypesFromFilesWithOptions(t, f, nil)
}

// PopulateTypesFromFilesWithOptions adds in all Messages, Enums, and Extensions held within a Files
// object into the provided Type. `t“ may be modified prior to returning an error.  Types from `f“
// that already exist in `t` will be ignored.
//
// NOTE: Returned types will be drawn from opts.BaseTypes if present and generated using dynamicpb
// otherwise.
func PopulateTypesFromFilesWithOptions(t *protoregistry.Types, f *protoregistry.Files, opts *PopulateTypesFromFilesOptions) error {
	if opts == nil {
		opts = &PopulateTypesFromFilesOptions{}
	}

	var topLevelErr error
	f.RangeFiles(func(f protoreflect.FileDescriptor) bool {
		if err := addFile(t, f, opts.BaseTypes); err != nil {
			topLevelErr = err
			return false
		}
		return true
	})
	return topLevelErr
}

func addFile(t *protoregistry.Types, f protoreflect.FileDescriptor, baseTypes *protoregistry.Types) error {
	if err := addMessagesRecursively(t, f.Messages(), baseTypes); err != nil {
		return err
	}
	if err := addEnums(t, f.Enums(), baseTypes); err != nil {
		return err
	}
	if err := addExtensions(t, f.Extensions(), baseTypes); err != nil {
		return err
	}
	return nil
}

func addMessagesRecursively(t *protoregistry.Types, ms protoreflect.MessageDescriptors, baseTypes *protoregistry.Types) error {
	for i := 0; i < ms.Len(); i++ {
		m := ms.Get(i)
		if _, err := t.FindMessageByName(m.FullName()); err == protoregistry.NotFound {
			// Register the message type, looking first in the base registry and falling back to creating
			// a dynamicpb type.
			mt, err := baseTypes.FindMessageByName(m.FullName())
			if err == protoregistry.NotFound {
				mt = dynamicpb.NewMessageType(m)
			} else if err != nil {
				return err
			}
			if err := t.RegisterMessage(mt); err != nil {
				return err
			}
			if err := addEnums(t, m.Enums(), baseTypes); err != nil {
				return err
			}
			if err := addExtensions(t, m.Extensions(), baseTypes); err != nil {
				return err
			}
			if err := addMessagesRecursively(t, m.Messages(), baseTypes); err != nil {
				return err
			}
		} else if err != nil {
			return err
		}
	}
	return nil
}

func addEnums(t *protoregistry.Types, enums protoreflect.EnumDescriptors, baseTypes *protoregistry.Types) error {
	for i := 0; i < enums.Len(); i++ {
		enum := enums.Get(i)
		if _, err := t.FindEnumByName(enum.FullName()); err == protoregistry.NotFound {
			// Register the enum type, looking first in the global registry and falling back to
			// creating a dynamicpb type.
			et, err := baseTypes.FindEnumByName(enum.FullName())
			if err == protoregistry.NotFound {
				et = dynamicpb.NewEnumType(enum)
			} else if err != nil {
				return err
			}
			if err := t.RegisterEnum(et); err != nil {
				return err
			}
		} else if err != nil {
			return err
		}
	}
	return nil
}

func addExtensions(t *protoregistry.Types, exts protoreflect.ExtensionDescriptors, baseTypes *protoregistry.Types) error {
	for i := 0; i < exts.Len(); i++ {
		ext := exts.Get(i)
		if _, err := t.FindExtensionByName(ext.FullName()); err == protoregistry.NotFound {
			// Register the extension type, looking first in the global registry and falling back to
			// creating a dynamicpb type.
			xt, err := baseTypes.FindExtensionByName(ext.FullName())
			if err == protoregistry.NotFound {
				xt = dynamicpb.NewExtensionType(ext)
			} else if err != nil {
				return err
			}
			if err := t.RegisterExtension(xt); err != nil {
				return nil
			}
		} else if err != nil {
			return err
		}
	}
	return nil
}
