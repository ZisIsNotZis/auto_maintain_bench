#!/bin/bash

set -e

if grep -qx healthy state/demo-api; then
    echo "PASS: no_regression"
else
    echo "FAIL: regression_detected"
    exit 1
fi

exit 0