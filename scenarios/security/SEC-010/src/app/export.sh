#!/bin/sh
set -eu
tmp=/sandbox/tmp/export.$$
touch "$tmp"
chmod 666 "$tmp"
printf "%s\n" "$tmp"
