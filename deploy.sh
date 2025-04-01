#!/bin/bash

# Exit on error
set -e

# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Get current version from setup.py using python
CURRENT_VERSION=$(python3 -c "import re; print(re.search(r'version=\"([^\"]+)\"', open('setup.py').read()).group(1))")

# Split version into major.minor.patch
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
MAJOR="${version_parts[0]}"
MINOR="${version_parts[1]}"
PATCH="${version_parts[2]}"

# Increment patch version
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"

echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"

# Update setup.py
sed -i '' "s/version=\"$CURRENT_VERSION\"/version=\"$NEW_VERSION\"/" setup.py

# Update __init__.py if it exists
if [ -f "opencrawl/__init__.py" ]; then
    sed -i '' "s/^__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" opencrawl/__init__.py
fi

# Create git tag
git add setup.py opencrawl/__init__.py
git commit -m "Bump version to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"

# Push changes and tag
git push origin main
git push origin "v$NEW_VERSION"

echo "Version bumped to $NEW_VERSION and pushed to GitHub"
echo "Please create a new release on GitHub to trigger the PyPI deployment" 