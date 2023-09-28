// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package shared provides data types that client tooling uses as well for static typed api boundaries.
package shared

import "encoding/json"

// ConfigureData is the data type used during the configuration push by inctl.
type ConfigureData struct {
	Config   []byte `json:"config"`
	Hostname string `json:"hostname"`
	Role     string `json:"role"`
	Cluster  string `json:"cluster"`
	Private  bool   `json:"private"`
	// CreatedByTest is only used for automated testing, and contains the ID of the test that is
	// registering this device. It is used to label the resources (in particular the Robot CR) so we
	// can clean it up.
	CreatedByTest string `json:"created_by_test"`
}

// TokenPlaceholder is used to modify the config by string replacement.
const TokenPlaceholder = "INTRINSIC_BOOTSTRAP_TOKEN_PLACEHOLDER"

// DeviceInfo is the data type used to upload the key from a device to the install registry and is
// reported to the devicemanager on claim
type DeviceInfo struct {
	Key       string `json:"key"`
	HasGPU    bool   `json:"has_gpu"`
	CanDoReal bool   `json:"can_do_real"`
}

// Nameservers sets DNS servers and search domains.
type Nameservers struct {
	// Search is a list of DNS search domains.
	Search []string `json:"search" jsonschema:"example=lab.intrinsic.ai"`

	// Addresses is a list of DNS servers.
	Addresses []string `json:"addresses" jsonschema:"format=ipv4"`
}

// Interface represents a network interface configuration.
type Interface struct {
	// DHCP4 enables or disables DHCP on the interface.
	DHCP4 bool `json:"dhcp4"`

	// Gateway4 specifies the default gateway, if DHCP4 is disabled.
	Gateway4 string `json:"gateway4" jsonschema:"format=ipv4"`

	// NOT IMPLEMENTED: DHCP6 enables or disables DHCP on the interface.
	DHCP6 *bool `json:"dhcp6"`

	// NOT IMPLEMENTED: Gateway6 specifies the default gateway, if DHCP6 is disabled.
	Gateway6 string `json:"gateway6" jsonschema:"format=ipv6"`

	// MTU is the maximum transfer unit of the device, in bytes. If omitted,
	// the system will choose a default.
	MTU int64 `json:"mtu" jsonschema:"example=9000"`

	// Nameservers sets DNS servers and search domains.
	Nameservers Nameservers `json:"nameservers"`

	// Addresses specifies the IP addresses. It is required if DHCP4 is
	// disabled. If DHCP4 is enabled it can be optionally used for additional
	// addresses.
	Addresses []string `json:"addresses" validate:"required_without=DHCP4,omitempty,min=1" jsonschema:"format=ipv4"`

	// Realtime identifies this interface to be used for realtime communication
	// with the robot.
	Realtime bool `json:"realtime"`
}

// String implements fmt.Stringer for logging purposes.
func (i Interface) String() string {
	r, err := json.Marshal(i)
	if err != nil {
		panic(err)
	}
	return string(r)
}

// Status represents the current OS status. It is similar to config.Config but
// contains the current status instead of the wanted status.
type Status struct {
	NodeName   string                     `json:"nodeName"`
	Hostname   string                     `json:"hostname"`
	Network    map[string]StatusInterface `json:"network"`
	BuildID    string                     `json:"buildId"`
	ImageType  string                     `json:"imageType"`
	Board      string                     `json:"board"`
	ActiveCopy string                     `json:"activeCopy"`
	OEMVars    map[string]string          `json:"oemVars"`
}

// StatusInterface represents a network interface.
type StatusInterface struct {
	Up         bool     `json:"up"`
	MacAddress string   `json:"hwaddr"`
	MTU        int      `json:"mtu"`
	IPAddress  []string `json:"addresses"`
	Speed      int      `json:"speed,omitempty"`
}
