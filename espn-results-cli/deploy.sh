#!/usr/bin/env bash
# deploy.sh — packages and updates both Lambda functions
set -e

FUNCTIONS=("clt-espn-results-production" "clt-espn-results-staging")
REGION="us-east-1"
DIR="$(cd "$(dirname "$0")" && pwd)"
ZIP="$DIR/deploy.zip"

echo "==> Packaging..."
cd "$DIR"
zip -q "$ZIP" lambda_handler.py espn_results.py
echo "    deploy.zip ready ($(du -sh "$ZIP" | cut -f1))"

for FN in "${FUNCTIONS[@]}"; do
    echo "==> Updating $FN..."
    aws lambda update-function-code \
        --function-name "$FN" \
        --zip-file "fileb://$ZIP" \
        --region "$REGION" \
        --no-verify-ssl \
        --query "FunctionName" \
        --output text 2>&1 | grep -v InsecureRequest || echo "    WARNING: failed to update $FN"
    echo "    Done."
done

rm "$ZIP"
echo "==> Deploy complete."
