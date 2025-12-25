#!/bin/bash

# -----------------------------
# Upload test results to JFrog
# -----------------------------

set -e
set -u
set -o pipefail

# -----------------------------
# Arguments
# -----------------------------
if [ $# -lt 4 ]; then
  echo "Usage: $0 <NAME> <JFROG_URL> <JFROG_REPO> <JFROG_TOKEN>"
  exit 1
fi

NAME="$1"
JFROG_URL="$2"
JFROG_REPO="$3"
JFROG_ACCESS_TOKEN="$4"

echo "Upload test result for: \"$NAME\""
echo "Using URL: $JFROG_URL"
echo "Repo: $JFROG_REPO"

# -----------------------------
# Run Python uploader
# -----------------------------
python3 -m jfrog_uploader \
    --artifact_result="./project/test-results/$NAME" \
    --json_result="./project/test-results/results.json" \
    --dest="test/testreport/ws/WS_1.21.0" \
    --base-url="$JFROG_URL" \
    --repo="$JFROG_REPO" \
    --access-token="$JFROG_ACCESS_TOKEN"

echo "✅ Upload completed."
