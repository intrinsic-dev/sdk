// Copyright 2023 Intrinsic Innovation LLC

package auth

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"

	"github.com/spf13/cobra"
	"intrinsic/tools/inctl/util/orgutil"
)

var (
	flagOrg string
)

func init() {
	printDebugInfoCmd.Flags().StringVarP(&flagOrg, orgutil.KeyOrganization, "", "", "Name of the organization to debug.")
	printDebugInfoCmd.MarkFlagRequired(orgutil.KeyOrganization)
	authCmd.AddCommand(printDebugInfoCmd)
}

var domains = []string{
	"flowstate.intrinsic.ai",
	"accounts.intrinsic.ai",
}

var printDebugInfoCmdHelp = `
Prints debug information to diagnose issues with authentication.
`

var printDebugInfoCmd = &cobra.Command{
	Use:   "debuginfo",
	Short: "Prints debug information to diagnose issues with authentication.",
	Long:  printDebugInfoCmdHelp,
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := cmd.Context()
		debugAuthStore(flagOrg)
		for _, domain := range domains {
			debugDomain(ctx, domain)
		}
		return nil
	},
}

func debugAuthStore(org string) {
	fmt.Printf("Configuration for org %s: ", org)
	orgInfo, err := authStore.ReadOrgInfo(org)
	if err != nil {
		fmt.Printf("ERROR (%v)\n", err)
		return
	}
	fmt.Println("OK")
	fmt.Printf(" Organization: %s\n", orgInfo.Organization)
	fmt.Printf(" Project: %s\n", orgInfo.Project)
	fmt.Printf("Project configuration %s: ", orgInfo.Project)
	store, err := authStore.GetConfiguration(orgInfo.Project)
	if err != nil {
		fmt.Printf("ERROR (%v)\n", err)
		return
	}
	fmt.Println("OK")
	fmt.Print("Default credentials: ")
	cred, err := store.GetDefaultCredentials()
	if err != nil {
		fmt.Printf("ERROR (%v)\n", err)
		return
	}
	fmt.Println("OK")
	fmt.Printf("API Key Length: %d\n", len(cred.APIKey))
}

func debugDomain(ctx context.Context, domain string) {
	debugDNS(ctx, domain)
	err := debugTLS(ctx, domain, false)
	if err != nil { // try again without verification
		debugTLS(ctx, domain, true)
	}
}

func debugTLS(ctx context.Context, domain string, skipVerify bool) error {
	fmt.Printf("TLS (%q, skipVerify=%t): ", domain, skipVerify)
	conf := &tls.Config{
		InsecureSkipVerify: skipVerify, // NOLINT
	}
	conn, err := tls.Dial("tcp", domain+":443", conf)
	if err != nil {
		fmt.Printf("ERROR (%v)\n", err)
		return err
	}
	defer conn.Close()
	fmt.Println("OK")
	certs := conn.ConnectionState().PeerCertificates
	for idx, cert := range certs {
		fmt.Printf(" Certificate %d:\n", idx)
		fmt.Printf("  Subject: %v\n", cert.Subject)
		fmt.Printf("  Issuer Name: %v\n", cert.Issuer)
		fmt.Printf("  Expiry: %s \n", cert.NotAfter.Format("2006-January-02"))
		fmt.Printf("  Common Name: %s \n", cert.Issuer.CommonName)
	}
	return nil
}

func debugDNS(ctx context.Context, domain string) {
	// debug DNS
	fmt.Printf("DNS (%q): ", domain)
	r := net.Resolver{}
	addrs, err := r.LookupHost(ctx, domain)
	if err != nil {
		fmt.Printf("ERROR (%v)", err)
		return
	}
	fmt.Println("OK")
	fmt.Printf("DNS (%q): Addresses: %v\n", domain, addrs)
}
