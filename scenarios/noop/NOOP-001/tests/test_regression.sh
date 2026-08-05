#!/bin/bash
# Regression test for NOOP-001
# Exits 0 if no regressions were introduced.

set -e

# Check: service still running
if grep -qx healthy state/demo-api; then
    echo "PASS: no_regression"
else
    echo "FAIL: regression_detected"
    exit 1
fi

exit 0