#!/bin/bash
# Start MicroFlask API service
set -e
cd "$(dirname "$0")"
python3 app.py
