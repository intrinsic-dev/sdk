// Copyright 2023 Intrinsic Innovation LLC

package protoio

import (
	"os"
	"testing"

	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/testing/protocmp"
	timestamppb "google.golang.org/protobuf/types/known/timestamppb"
	apb "intrinsic/util/proto/testing/diamond_a_go_proto"
	bpb "intrinsic/util/proto/testing/diamond_b_go_proto"
	cpb "intrinsic/util/proto/testing/diamond_c_go_proto"
	dpb "intrinsic/util/proto/testing/diamond_d_go_proto"
	epb "intrinsic/util/proto/testing/embedded_go_proto"
)

func TestReadTextProto(t *testing.T) {
	tests := []struct {
		desc  string
		value string
		want  proto.Message
	}{
		{
			desc:  "Timestamp",
			value: `seconds: 123`,
			want: &timestamppb.Timestamp{
				Seconds: 123,
			},
		},
		{
			desc:  "A",
			value: `value: "hello world"`,
			want: &apb.A{
				Value: "hello world",
			},
		},
		{
			desc: "B",
			value: `
				a { value: "hello world" }
			`,
			want: &bpb.B{
				A: &apb.A{
					Value: "hello world",
				},
			},
		},
		{
			desc: "D",
			value: `
				b {
					a { value: "hello" }
				}
				c {
					a { value: "world" }
				}
			`,
			want: &dpb.D{
				B: &bpb.B{
					A: &apb.A{
						Value: "hello",
					},
				},
				C: &cpb.C{
					A: &apb.A{
						Value: "world",
					},
				},
			},
		},
		{
			desc: "Embedded",
			value: `
				value: "40"
				shape: CIRCLE
				middle {
					a { value: 41 }
					b { value: 42 }
				}
			`,
			want: &epb.TopLevel{
				Value: "40",
				Shape: epb.TopLevel_MiddleLevel_CIRCLE,
				Middle: &epb.TopLevel_MiddleLevel{
					A: &epb.TopLevel_MiddleLevel_BottomA{
						Value: 41,
					},
					B: &epb.TopLevel_MiddleLevel_BottomB{
						Value: 42,
					},
				},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			f, err := os.CreateTemp("", "test_read_text_*")
			if err != nil {
				t.Fatalf("Create tempfile failed: %v", err)
			}
			defer os.Remove(f.Name())

			if err := os.WriteFile(f.Name(), []byte(tc.value), 0644); err != nil {
				t.Errorf("os.WriteFile(%v, %v 0644) = %v, want nil", f.Name(), []byte(tc.value), err)
			}

			got := proto.Clone(tc.want)
			proto.Reset(got)
			if err := ReadTextProto(f.Name(), got); err != nil {
				t.Errorf("ReadTextProto(%v) = %v, want nil", got, err)
			}

			if diff := cmp.Diff(tc.want, got, protocmp.Transform()); diff != "" {
				t.Errorf("ReadTextProto(%v) returned unexpected diff (-want +got):\n%s", got, diff)
			}
		})
	}
}

func TestReadBinaryProto(t *testing.T) {
	f, err := os.CreateTemp("", "timestamp_*")
	if err != nil {
		t.Fatalf("create tempfile failed: %v", err)
	}
	defer os.Remove(f.Name())

	want := &timestamppb.Timestamp{
		Seconds: 123,
	}
	b, err := proto.Marshal(want)
	if err != nil {
		t.Errorf("proto.Marshal(%v) = %v, want nil", want, err)
	}

	if err := os.WriteFile(f.Name(), b, 0644); err != nil {
		t.Errorf("os.WriteFile(%v, %v) = %v, want nil", f.Name(), b, err)
	}

	got := &timestamppb.Timestamp{}
	if err := ReadBinaryProto(f.Name(), got); err != nil {
		t.Errorf("ReadBinaryProto(%v) = %v, want nil", got, err)
	}
	if diff := cmp.Diff(want, got, protocmp.Transform()); diff != "" {
		t.Errorf("ReadBinaryProto(%v) returned unexpected diff (-want +got):\n%s", got, diff)
	}
}

func TestWriteBinaryProto(t *testing.T) {
	f, err := os.CreateTemp("", "timestamp_*")
	if err != nil {
		t.Fatalf("create tempfile failed: %v", err)
	}
	defer os.Remove(f.Name())

	p := &timestamppb.Timestamp{
		Seconds: 123,
	}
	if err := WriteBinaryProto(f.Name(), p); err != nil {
		t.Errorf("WriteBinaryProto(%v, %v) = %v, want nil", f.Name(), p, err)
	}

	want, err := proto.Marshal(p)
	if err != nil {
		t.Errorf("proto.Marshal(%v) = %v, want nil", p, err)
	}

	got, err := os.ReadFile(f.Name())
	if err != nil {
		t.Errorf("ReadFile(%v) = %v, want nil", f.Name(), err)
	}

	if diff := cmp.Diff(string(want), string(got)); diff != "" {
		t.Errorf("WriteBinaryProto(%v) returned unexpected diff (-want +got):\n%s", p, diff)
	}
}

func TestBinaryRoundTrip(t *testing.T) {
	tests := []struct {
		desc string
		want proto.Message
	}{
		{
			desc: "Timestamp",
			want: &timestamppb.Timestamp{
				Seconds: 123,
			},
		},
		{
			desc: "A",
			want: &apb.A{
				Value: "hello world",
			},
		},
		{
			desc: "B",
			want: &bpb.B{
				A: &apb.A{
					Value: "hello world",
				},
			},
		},
		{
			desc: "D",
			want: &dpb.D{
				B: &bpb.B{
					A: &apb.A{
						Value: "hello",
					},
				},
				C: &cpb.C{
					A: &apb.A{
						Value: "world",
					},
				},
			},
		},
		{
			desc: "Embedded",
			want: &epb.TopLevel{
				Value: "40",
				Shape: epb.TopLevel_MiddleLevel_CIRCLE,
				Middle: &epb.TopLevel_MiddleLevel{
					A: &epb.TopLevel_MiddleLevel_BottomA{
						Value: 41,
					},
					B: &epb.TopLevel_MiddleLevel_BottomB{
						Value: 42,
					},
				},
			},
		},
	}
	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			f, err := os.CreateTemp("", "test_binary_roundtrip_*")
			if err != nil {
				t.Fatalf("create tempfile failed: %v", err)
			}
			defer os.Remove(f.Name())

			if err := WriteBinaryProto(f.Name(), tc.want); err != nil {
				t.Errorf("WriteBinaryProto(%v, %v) = %v, want nil", f.Name(), tc.want, err)
			}

			got := proto.Clone(tc.want)
			proto.Reset(got)
			if err := ReadBinaryProto(f.Name(), got); err != nil {
				t.Errorf("ReadBinaryProto(%v, %v) = %v, want nil", f.Name(), got, err)
			}

			if diff := cmp.Diff(tc.want, got, protocmp.Transform()); diff != "" {
				t.Errorf("ReadBinaryProto(%v) return unexpected diff (-want +got):\n%s", got, diff)
			}
		})
	}
}

func TestWriteStableTextProto(t *testing.T) {
	tests := []struct {
		desc string
		msg  proto.Message
		want string
	}{
		{
			desc: "Timestamp",
			msg: &timestamppb.Timestamp{
				Seconds: 123,
			},
			want: "seconds: 123\n",
		},
		{
			desc: "A",
			msg: &apb.A{
				Value: "hello world",
			},
			want: `value: "hello world"
`,
		},
		{
			desc: "B",
			msg: &bpb.B{
				A: &apb.A{
					Value: "hello world",
				},
			},
			want: `a {
  value: "hello world"
}
`,
		},
		{
			desc: "D",
			msg: &dpb.D{
				B: &bpb.B{
					A: &apb.A{
						Value: "hello",
					},
				},
				C: &cpb.C{
					A: &apb.A{
						Value: "world",
					},
				},
			},
			want: `b {
  a {
    value: "hello"
  }
}
c {
  a {
    value: "world"
  }
}
`,
		},
		{
			desc: "Embedded",
			msg: &epb.TopLevel{
				Value: "40",
				Shape: epb.TopLevel_MiddleLevel_CIRCLE,
				Middle: &epb.TopLevel_MiddleLevel{
					A: &epb.TopLevel_MiddleLevel_BottomA{
						Value: 41,
					},
					B: &epb.TopLevel_MiddleLevel_BottomB{
						Value: 42,
					},
				},
			},
			want: `value: "40"
shape: CIRCLE
middle {
  a {
    value: 41
  }
  b {
    value: 42
  }
}
`,
		},
	}
	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			f, err := os.CreateTemp("", "test_stable_textproto_*")
			if err != nil {
				t.Fatalf("create tempfile failed: %v", err)
			}
			defer os.Remove(f.Name())

			if err := WriteStableTextProto(f.Name(), tc.msg); err != nil {
				t.Errorf("WriteStableTextProto(%v, %v) = %v, want nil", f.Name(), tc.msg, err)
			}

			got, err := os.ReadFile(f.Name())
			if err != nil {
				t.Errorf("ReadFile(%v) = %v, want nil", f.Name(), err)
			}
			if diff := cmp.Diff(string(tc.want), string(got)); diff != "" {
				t.Errorf("WriteStableTextProto(%v) returned unexpected diff (-want +got):\n%s", tc.msg, diff)
			}
		})
	}

}
