# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

###############################################################################
# Common package groups for visibility
# public_api_users contains the set of packages allowed to depend on
# Intrinsic's public APIs.
package_group(
    name = "public_api_users",
    packages = [
        "public",
    ],
)

# internal_api_users contains the set of packages allowed to depend on
# Intrinsic's internal APIs.
package_group(
    name = "internal_api_users",
    packages = [
        "//intrinsic/...",
    ],
)

# public_asset_users contains the set of packages allowed to depend on assets built by Intrinsic.
package_group(
    name = "public_asset_users",
    packages = [
        "public",
    ],
)

###############################################################################
