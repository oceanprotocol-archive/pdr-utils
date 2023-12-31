# Release Process

## Version Number

In the pdr-utils repository, the version and tag name convention follows the format "vx.x.x":
- The version number consists of three parts separated by dots, The first part represents the major version, the second part represents the minor version, and the third part represents the patch version.
- When a new release is created, the version number should be incremented according to the significance of the changes made in the release.

## Create a New Release

To create a new release for pdr-utils, follow these steps:

1. Visit the [Github Releases](https://github.com/oceanprotocol/pdr-utils/releases) page.
2. Click on "Draft a new release."
3. Choose an appropriate version tag (e.g., v1.0.0) and provide a release title.
4. Add release notes and any relevant information about the new release.
5. Once everything is ready, click "Publish release."

The CI will automatically push the new release to PyPI, making it available for installation and use.