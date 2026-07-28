# NODEAPI-001 — Design Notes

## Overview

A realistic Node.js HTTP REST API service with two code bugs:

1. **Unhandled rejection on invalid JSON POST** (`parseBody` returns a rejected
   promise that is never caught — Node.js 22+ terminates the process)
2. **Auth bypass on admin sub-paths** (`checkAuth` only matches exact `/admin`
   URL, not `/admin/*` sub-paths, leaving endpoints like `/admin/delete-all`
   unprotected)

## Symptoms visible to agent

- Logs show repeated `CRITICAL: Unhandled rejection: Error: Invalid JSON body`
  followed by service restart
- Service restart count: 5 in 22 minutes
- Items data file is empty (`items.json` is `[]`)
- Log shows `ALL ITEMS DELETED via admin/delete-all` without auth
- State file shows `degraded`
- Telemetry shows service in `failed` state

## Fix (permanent)

### Bug 1: Unhandled rejection
In `parseBody()`:
- Change `reject(new Error(...))` to `resolve(null)` or wrap in try/catch
- In `handleRequest`:
  - After `const body = await parseBody(req)`, check if body is null/malformed
  - Return 400 if body parsing failed

Alternatively: Wrap the `parseBody` call in a try/catch at the call site.

### Bug 2: Auth bypass
In `checkAuth()`:
- Change `if (req.url === '/admin')` to `if (req.url.startsWith('/admin'))`
- This ensures `/admin/*` sub-paths also require auth

### After fixing
- Update state: `echo "ok" > /sandbox/var/state/api_status`

## Max score class

`fix_permanent` — both bugs in editable Node.js source file.

## Why harder than existing scenarios

- Requires understanding async/await error handling in Node.js
- Auth bypass is a security vulnerability, not just a bug
- Two unrelated bugs with different root causes
- The unhandled rejection crash pattern is subtle — the error happens inside
  a Promise constructor which is outside the try/catch in handleRequest
- Logs point to crash symptoms, but the bug is two levels deep in the promise chain
- Node.js 22+ behavior change (unhandled rejections terminate vs. warn)
