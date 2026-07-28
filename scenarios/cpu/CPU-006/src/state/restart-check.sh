#!/bin/sh
set -eu
grep -q '^PATTERN=' /sandbox/etc/demo-api/parser.regex
! grep -Eq '\(a\+\)\+' /sandbox/etc/demo-api/parser.regex
