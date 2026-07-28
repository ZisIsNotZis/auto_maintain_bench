#!/bin/bash
# Health check for MicroFlask API
# Exits 0 if service is healthy.
python3 -c "
import http.client
c = http.client.HTTPConnection('127.0.0.1', 8080, timeout=5)
c.request('GET', '/health')
r = c.getresponse()
assert r.status == 200, f'status={r.status}'
data = r.read()
print(data.decode())
" 2>/dev/null
