// Copyright 2023 Intrinsic Innovation LLC

package servicegen

import (
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"

	idpb "intrinsic/assets/proto/id_go_proto"
	vpb "intrinsic/assets/proto/vendor_go_proto"
	smpb "intrinsic/assets/services/proto/service_manifest_go_proto"
)

func TestValidateManifest(t *testing.T) {
	var tests = []struct {
		desc      string
		given     *smpb.ServiceManifest
		wantError string
	}{
		{
			desc:      "no name or package",
			given:     &smpb.ServiceManifest{},
			wantError: "invalid name or package",
		},
		{
			desc: "invalid name",
			given: &smpb.ServiceManifest{
				Metadata: &smpb.ServiceMetadata{
					Id: &idpb.Id{
						Name: "_invalid_name",
					},
				},
			},
			wantError: "invalid name or package",
		},
		{
			desc: "no display name",
			given: &smpb.ServiceManifest{
				Metadata: &smpb.ServiceMetadata{
					Id: &idpb.Id{
						Name:    "test_name",
						Package: "test.package",
					},
				},
			},
			wantError: "vendor.display_name must be specified",
		},
		{
			desc: "no sim spec specified",
			given: &smpb.ServiceManifest{
				Metadata: &smpb.ServiceMetadata{
					Id: &idpb.Id{
						Name:    "test_name",
						Package: "test.package",
					},
					Vendor: &vpb.Vendor{
						DisplayName: "test display name",
					},
				},
				ServiceDef: &smpb.ServiceDef{},
			},
			wantError: "a sim_spec must be specified if a service_def is provided",
		},
		{
			desc: "valid manifest without service def",
			given: &smpb.ServiceManifest{
				Metadata: &smpb.ServiceMetadata{
					Id: &idpb.Id{
						Name:    "test_name",
						Package: "test.package",
					},
					Vendor: &vpb.Vendor{
						DisplayName: "test display name",
					},
				},
			},
			wantError: "",
		},
		{
			desc: "valid manifest with service def",
			given: &smpb.ServiceManifest{
				Metadata: &smpb.ServiceMetadata{
					Id: &idpb.Id{
						Name:    "test_name",
						Package: "test.package",
					},
					Vendor: &vpb.Vendor{
						DisplayName: "test display name",
					},
				},
				ServiceDef: &smpb.ServiceDef{
					SimSpec: &smpb.ServicePodSpec{},
				},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			if err := validateManifest(tc.given); err != nil && !strings.Contains(err.Error(), tc.wantError) {
				diff := cmp.Diff(tc.wantError, err, cmpopts.EquateErrors())
				t.Fatalf("validateManifest(%v) returned unexpected error, diff (-want +got):\n%s", tc.given, diff)
			}
		})
	}
}

func TestValidateImageTars(t *testing.T) {
	metadata := &smpb.ServiceMetadata{
		Id: &idpb.Id{
			Name:    "test_name",
			Package: "test.package",
		},
		Vendor: &vpb.Vendor{
			DisplayName: "test display name",
		},
	}
	var tests = []struct {
		desc                   string
		givenManifest          *smpb.ServiceManifest
		givenImagesInBuildRule []string
		wantError              string
	}{
		{
			desc: "image tar not provided in BUILD rule",
			givenManifest: &smpb.ServiceManifest{
				Metadata: metadata,
				ServiceDef: &smpb.ServiceDef{
					SimSpec: &smpb.ServicePodSpec{
						Image: &smpb.ServiceImage{
							ArchiveFilename: "test_image.tar",
						},
					},
				},
			},
			wantError: "images listed in the manifest are not provided in the BUILD rule",
		},
		{
			desc: "image tars not provided in manifest",
			givenManifest: &smpb.ServiceManifest{
				Metadata: metadata,
			},
			givenImagesInBuildRule: []string{"/path/to/test_image.tar"},
			wantError:              "images listed in the BUILD rule are not provided in the manifest",
		},
		{
			desc: "image tars not provided in BUILD rule",
			givenManifest: &smpb.ServiceManifest{
				Metadata: metadata,
				ServiceDef: &smpb.ServiceDef{
					SimSpec: &smpb.ServicePodSpec{
						Image: &smpb.ServiceImage{
							ArchiveFilename: "test_image.tar",
						},
					},
					RealSpec: &smpb.ServicePodSpec{
						Image: &smpb.ServiceImage{
							ArchiveFilename: "test_image.tar",
						},
					},
				},
			},
			wantError: "images listed in the manifest are not provided in the BUILD rule",
		},
		{
			desc: "image tars not provided in BUILD rule",
			givenManifest: &smpb.ServiceManifest{
				Metadata: metadata,
				ServiceDef: &smpb.ServiceDef{
					SimSpec: &smpb.ServicePodSpec{
						Image: &smpb.ServiceImage{
							ArchiveFilename: "test_image.tar",
						},
					},
					RealSpec: &smpb.ServicePodSpec{
						Image: &smpb.ServiceImage{
							ArchiveFilename: "another_image.tar",
						},
					},
				},
			},
			givenImagesInBuildRule: []string{"/path/to/test_image.tar"},
			wantError:              "images listed in the manifest are not provided in the BUILD rule",
		},
		{
			desc: "valid set of image tars",
			givenManifest: &smpb.ServiceManifest{
				Metadata: metadata,
				ServiceDef: &smpb.ServiceDef{
					SimSpec: &smpb.ServicePodSpec{
						Image: &smpb.ServiceImage{
							ArchiveFilename: "test_image.tar",
						},
					},
				},
			},
			givenImagesInBuildRule: []string{"/path/to/test_image.tar"},
			wantError:              "",
		},
		{
			desc: "valid no image tars",
			givenManifest: &smpb.ServiceManifest{
				Metadata: metadata,
			},
			wantError: "",
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			if err := validateImageTars(tc.givenManifest, tc.givenImagesInBuildRule); err != nil && !strings.Contains(err.Error(), tc.wantError) {
				diff := cmp.Diff(tc.wantError, err, cmpopts.EquateErrors())
				t.Fatalf("validateImageTars(%v, %v) returned unexpected error, diff (-want +got):\n%s", tc.givenManifest, tc.givenImagesInBuildRule, diff)
			}
		})
	}
}
