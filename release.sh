#!/bin/bash

# Exit on error
set -e

# Get current version from setup.py using python
CURRENT_VERSION=$(python3 -c "import re; print(re.search(r'version=\"([^\"]+)\"', open('setup.py').read()).group(1))")

# Push the tag to trigger workflow
echo "Pushing tag v${CURRENT_VERSION} to trigger PyPI deployment..."
git push origin "v${CURRENT_VERSION}"

echo "Tag pushed! PyPI deployment workflow should start automatically." 