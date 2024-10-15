// Copyright 2023 Intrinsic Innovation LLC

// Package environments provides utilities and helpers for working with the various environments.
package environments

import "fmt"

const (
	// Prod is the production environment.
	Prod = "prod"
	// Staging is the staging environment.
	Staging = "staging"
	// Dev is the development environment.
	Dev = "dev"

	// AccountsProjectDev is the project for the accounts service in dev.
	AccountsProjectDev = "intrinsic-accounts-dev"
	// AccountsProjectStaging is the project for the accounts service in staging.
	AccountsProjectStaging = "intrinsic-accounts-staging"
	// AccountsProjectProd is the project for the accounts service in prod.
	AccountsProjectProd = "intrinsic-accounts-prod"

	// AccountsDomainDev is the domain for the accounts service in dev.
	AccountsDomainDev = "accounts-dev.intrinsic.ai"
	// AccountsDomainStaging is the domain for the accounts service in staging.
	AccountsDomainStaging = "accounts-qa.intrinsic.ai"
	// AccountsDomainProd is the domain for the accounts service in prod.
	AccountsDomainProd = "accounts.intrinsic.ai"

	// PortalProjectDev is the project for the portal service in dev.
	PortalProjectDev = "intrinsic-portal-dev"
	// PortalProjectStaging is the project for the portal service in staging.
	PortalProjectStaging = "intrinsic-portal-staging"
	// PortalProjectProd is the project for the portal service in prod.
	PortalProjectProd = "intrinsic-portal-prod"

	// PortalDomainDev is the domain for the portal service in dev.
	PortalDomainDev = "flowstate-dev.intrinsic.ai"
	// PortalDomainStaging is the domain for the portal service in staging.
	PortalDomainStaging = "flowstate-qa.intrinsic.ai"
	// PortalDomainProd is the domain for the portal service in prod.
	PortalDomainProd = "flowstate.intrinsic.ai"

	// AssetsProjectDev is the project for the asset service in dev.
	AssetsProjectDev = "intrinsic-assets-dev"
	// AssetsProjectStaging is the project for the asset service in staging.
	AssetsProjectStaging = "intrinsic-assets-staging"
	// AssetsProjectProd is the project for the asset service in prod.
	AssetsProjectProd = "intrinsic-assets-prod"

	// AssetsDomainDev is the domain for the asset service in dev.
	AssetsDomainDev = "assets-dev.intrinsic.ai"
	// AssetsDomainStaging is the domain for the asset service in staging.
	AssetsDomainStaging = "assets-qa.intrinsic.ai"
	// AssetsDomainProd is the domain for the asset service in prod.
	AssetsDomainProd = "assets.intrinsic.ai"
)

// All is the list of all environments.
var All = []string{Prod, Staging, Dev}

// FromDomain returns the environment for the given domain of portal, accounts or assets projects.
func FromDomain(domain string) (string, error) {
	switch domain {
	case PortalDomainProd, AccountsDomainProd, AssetsDomainProd:
		return Prod, nil
	case PortalDomainStaging, AccountsDomainStaging, AssetsDomainStaging:
		return Staging, nil
	case PortalDomainDev, AccountsDomainDev, AssetsDomainDev:
		return Dev, nil
	default:
		return "", fmt.Errorf("unknown domain %q", domain)
	}
}

// FromProject returns the environment for the given portal, accounts or assets project.
func FromProject(project string) (string, error) {
	switch project {
	case PortalProjectProd, AccountsProjectProd, AssetsProjectProd:
		return Prod, nil
	case PortalProjectStaging, AccountsProjectStaging, AssetsProjectStaging:
		return Staging, nil
	case PortalProjectDev, AccountsProjectDev, AssetsProjectDev:
		return Dev, nil
	default:
		return "", fmt.Errorf("unknown project %q", project)
	}
}

// FromComputeProject returns the environment for the given compute project.
func FromComputeProject(project string) string {
	switch project {
	default:
		return Prod
	}
}

// PortalDomain returns the portal domain for the given environment.
func PortalDomain(env string) string {
	switch env {
	case Prod:
		return PortalDomainProd
	case Staging:
		return PortalDomainStaging
	case Dev:
		return PortalDomainDev
	default:
		return ""
	}
}

// PortalProject returns the portal project for the given environment.
func PortalProject(env string) string {
	switch env {
	case Prod:
		return PortalProjectProd
	case Staging:
		return PortalProjectStaging
	case Dev:
		return PortalProjectDev
	default:
		return ""
	}
}

// AccountsDomain returns the accounts domain for the given environment.
func AccountsDomain(env string) string {
	switch env {
	case Prod:
		return AccountsDomainProd
	case Staging:
		return AccountsDomainStaging
	case Dev:
		return AccountsDomainDev
	default:
		return ""
	}
}

// AccountsProject returns the accounts project for the given environment.
func AccountsProject(env string) string {
	switch env {
	case Prod:
		return AccountsProjectProd
	case Staging:
		return AccountsProjectStaging
	case Dev:
		return AccountsProjectDev
	default:
		return ""
	}
}

// AssetsDomain returns the assets domain for the given environment.
func AssetsDomain(env string) string {
	switch env {
	case Prod:
		return AssetsDomainProd
	case Staging:
		return AssetsDomainStaging
	case Dev:
		return AssetsDomainDev
	default:
		return ""
	}
}

// AssetsProject returns the assets project for the given environment.
func AssetsProject(env string) string {
	switch env {
	case Prod:
		return AssetsProjectProd
	case Staging:
		return AssetsProjectStaging
	case Dev:
		return AssetsProjectDev
	default:
		return ""
	}
}
