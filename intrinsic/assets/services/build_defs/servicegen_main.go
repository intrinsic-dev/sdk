// Copyright 2023 Intrinsic Innovation LLC

// package main implements creation of the service type bundle.
package main

import (
	"flag"
	log "github.com/golang/glog"
	"intrinsic/assets/services/build_defs/servicegen"
	intrinsic "intrinsic/production/intrinsic"
)

var (
	flagDefaultConfig      = flag.String("default_config", "", "Optional path to default config proto.")
	flagFileDescriptorSets = flag.String("file_descriptor_sets", "", "Comma separated paths to binary file descriptor set protos to be used to resolve the configuration and behavior tree messages.")
	flagImageTars          = flag.String("image_tars", "", "Comma separated full paths to tar archives for images.")
	flagManifest           = flag.String("manifest", "", "Path to a ServiceManifest pbtxt file.")
	flagOutputBundle       = flag.String("output_bundle", "", "Bundle tar path.")
)

func main() {
	intrinsic.Init()

	data := servicegen.ServiceData{
		DefaultConfig:      *flagDefaultConfig,
		FileDescriptorSets: *flagFileDescriptorSets,
		ImageTars:          *flagImageTars,
		Manifest:           *flagManifest,
		OutputBundle:       *flagOutputBundle,
	}
	if err := servicegen.CreateService(&data); err != nil {
		log.Exitf("Couldn't create service type: %v", err)
	}
}
