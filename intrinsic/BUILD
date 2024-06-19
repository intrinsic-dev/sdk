# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

exports_files(
    srcs = [
        "BUILD",
    ],
    visibility = ["//intrinsic/production:__subpackages__"],
)

###############################################################################
# Common package groups for visibility
# See go/intrinsic-visibility-groups-tdd

# public_api_users contains the set of packages allowed to depend on
# Intrinsic's public APIs.
#
# Targets visible to public_api_users will receive an increasing level of
# strictness and scrutiny over time. You should expect a significant ongoing
# maintenance cost for these targets.
package_group(
    name = "public_api_users",
    packages = [
        "public",
    ],
)

# internal_api_users contains the set of packages allowed to depend on
# Intrinsic's internal APIs.
#
# This package_group *should not* contain packages that include solutions or
# assets, since they should be built against public APIs.
package_group(
    name = "internal_api_users",
    packages = [
        "-//intrinsic/apps/...",
        "-//intrinsic/resources/catalog/resourcedata/...",
        "-//intrinsic/skills/apps/...",
        "//intrinsic/...",
    ],
)

# public_asset_users contains the set of packages allowed to depend on assets built by Intrinsic.
package_group(
    name = "public_asset_users",
    packages = [
        "//intrinsic/apps/...",
    ],
)

# release_tooling contains the set of packages used to release targets to production.
package_group(
    name = "release_tooling",
    packages = [
        "//intrinsic/production/...",
    ],
)

###############################################################################

package_group(
    name = "intrinsic_internal",
    packages = ["//intrinsic/..."],
)

package_group(
    name = "intrinsic_public",
    packages = [
        "//intrinsic/...",
        "//robotics/...",
    ],
)

package_group(
    name = "usd_dependants",
    packages = [
        "//intrinsic/usd/...",
        "//intrinsic/world/...",
    ],
)
