const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8080;
const DATA_DIR = process.env.DATA_DIR || '/sandbox/var/data';
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'dev-token-1234';

// ---------------------------------------------------------------------------
// BUG 1: Missing error handler on request body parsing.
// When JSON body parsing fails, the error is thrown asynchronously and
// becomes an unhandled rejection — Node.js logs "UnhandledPromiseRejection"
// and the process exits with code 1. This crashes the entire service.
// Fix: wrap body parsing in try/catch and respond with 400.
// ---------------------------------------------------------------------------

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      if (!body) return resolve({});
      try {
        resolve(JSON.parse(body));
      } catch (e) {
        // BUG: reject() is never caught — crashes the process
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

// ---------------------------------------------------------------------------
// BUG 2: Auth check only on exact "/admin" path.
// Request to "/admin/delete-all" or "/admin/../config" bypasses auth
// because the check is for path === "/admin" not path.startsWith("/admin").
// Fix: use path.startsWith("/admin") instead.
// ---------------------------------------------------------------------------

function checkAuth(req) {
  // BUG: only matches exact "/admin" path
  // Sub-paths like /admin/users, /admin/delete bypass this check
  if (req.url === '/admin') {
    const token = req.headers['authorization'];
    if (!token || token !== `Bearer ${AUTH_TOKEN}`) {
      return false;
    }
  }
  return true;
}

// ---------------------------------------------------------------------------
// Logging — persists to state file for monitoring
// ---------------------------------------------------------------------------

function logEvent(level, msg) {
  const line = `${new Date().toISOString()} [${level}] ${msg}\n`;
  fs.appendFileSync('/sandbox/var/log/api.log', line);
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

const OK_BODY = JSON.stringify({ status: 'ok' });
const ERR_BODY = JSON.stringify({ error: 'not found' });

async function handleRequest(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  // Auth check (BUG 2: only exact /admin, not /admin/*)
  if (!checkAuth(req)) {
    res.writeHead(401);
    res.end(JSON.stringify({ error: 'unauthorized' }));
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);

  try {
    // --- Health ---
    if (url.pathname === '/health') {
      res.writeHead(200);
      res.end(OK_BODY);
      logEvent('INFO', 'health check ok');
      return;
    }

    // --- Items (CRUD) ---
    if (url.pathname.startsWith('/items')) {
      if (req.method === 'GET') {
        // Pagination
        const page = parseInt(url.searchParams.get('page') || '1', 10);
        const limit = parseInt(url.searchParams.get('limit') || '10', 10);
        const items = await readItems();
        // BUG: page * limit skips first (page-1) items for pages > 1
        // e.g. page=2 with limit=10 returns items 20-29 instead of 10-19
        const start = page * limit;
        const paged = items.slice(start, start + limit);
        res.writeHead(200);
        res.end(JSON.stringify({ page, limit, total: items.length, items: paged }));
        logEvent('INFO', `GET /items page=${page} limit=${limit}`);
        return;
      }

      if (req.method === 'POST') {
        const body = await parseBody(req);
        if (!body.name) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'name required' }));
          return;
        }
        const item = await createItem(body);
        res.writeHead(201);
        res.end(JSON.stringify(item));
        logEvent('INFO', `POST /items id=${item.id}`);
        return;
      }
    }

    // --- Admin ---
    if (url.pathname === '/admin') {
      res.writeHead(200);
      res.end(JSON.stringify({ role: 'admin', endpoints: ['/admin/delete', '/admin/users'] }));
      return;
    }

    // BUG: /admin/delete has NO auth check (BUG 2)
    if (url.pathname === '/admin/delete-all') {
      await deleteAllItems();
      res.writeHead(200);
      res.end(JSON.stringify({ status: 'deleted' }));
      logEvent('WARN', 'ALL ITEMS DELETED via admin/delete-all');
      return;
    }

    // --- Status/Config ---
    if (url.pathname === '/status') {
      const stats = getStats();
      res.writeHead(200);
      res.end(JSON.stringify(stats));
      return;
    }

    // 404
    res.writeHead(404);
    res.end(ERR_BODY);
  } catch (err) {
    // BUG 1: crash from parseBody rejection reaches here but parseBody
    // rejection is in a separate promise chain that ISN'T in this try/catch
    logEvent('ERROR', `Unhandled error: ${err.message}`);
    res.writeHead(500);
    res.end(JSON.stringify({ error: 'internal error' }));
  }
}

// ---------------------------------------------------------------------------
// Data layer (file-backed "database")
// ---------------------------------------------------------------------------

let itemsCache = null;

function getItemsPath() {
  return path.join(DATA_DIR, 'items.json');
}

async function readItems() {
  if (itemsCache) return itemsCache;
  const filePath = getItemsPath();
  try {
    const data = await fs.promises.readFile(filePath, 'utf-8');
    itemsCache = JSON.parse(data);
  } catch {
    itemsCache = [];
  }
  return itemsCache;
}

async function createItem(body) {
  const items = await readItems();
  const id = items.length + 1;
  const item = { id, name: body.name, price: body.price || 0, created_at: new Date().toISOString() };
  items.push(item);
  itemsCache = items;
  await fs.promises.writeFile(getItemsPath(), JSON.stringify(items, null, 2));
  return item;
}

async function deleteAllItems() {
  itemsCache = [];
  await fs.promises.writeFile(getItemsPath(), '[]');
}

function getStats() {
  const mem = process.memoryUsage();
  return {
    uptime: process.uptime(),
    memory: { rss: mem.rss, heapUsed: mem.heapUsed, heapTotal: mem.heapTotal },
    pid: process.pid,
  };
}

// ---------------------------------------------------------------------------
// Server startup
// ---------------------------------------------------------------------------

const server = http.createServer(handleRequest);

server.listen(PORT, () => {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.mkdirSync(path.dirname('/sandbox/var/log/api.log'), { recursive: true });
  logEvent('INFO', `NodeAPI server started on port ${PORT}`);
  console.log(`NodeAPI listening on :${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logEvent('INFO', 'shutting down');
  server.close(() => process.exit(0));
});

// BUG 1 amplification: Node.js default behavior on unhandled rejections
// is to log a warning. But in Node 22+, unhandled rejections terminate
// the process with exit code 1. Any invalid JSON POST crashes the whole
// service.
process.on('unhandledRejection', (reason) => {
  logEvent('CRITICAL', `Unhandled rejection: ${reason}`);
  // Process will exit with code 1 — no recovery
});
