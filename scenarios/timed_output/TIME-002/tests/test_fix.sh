#!/bin/bash
# Fix verification test for TIME-002
# Exits 0 if fix is applied correctly.

set -e

# Check: writer_enabled
if grep -qx "WRITE_OUTPUT=true" etc/batch-writer/job.env; then
    echo "PASS: writer_enabled"
else
    echo "FAIL: writer_enabled"
    exit 1
fi

# Check: output_file_created
if grep -qx "1,ok" var/output/2026-07-22.csv; then
    echo "PASS: output_file_created"
else
    echo "FAIL: output_file_created"
    exit 1
fi

exit 0
