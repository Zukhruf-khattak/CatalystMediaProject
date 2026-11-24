# Frontend Operations & Deployment Runbook

## 1. Overview & Operational Responsibilities

The Catalist Meeting Intelligence Frontend is a standalone React 18 Single Page Application (SPA) served by Vite in development and compiled into optimized static HTML/JS/CSS assets for production deployment behind Nginx.

This runbook documents local development startup, production builds, environment variables, Nginx container configuration, SSE streaming troubleshooting, and smoke tests.

---

## 2. Environment Variables

Frontend environment variables are prefixed with `VITE_` and configured in `frontend/.env` or passed during Docker container builds:

| Variable | Default Value | Production Value | Purpose |
|---|---|---|---|
| `VITE_API_BASE_URL` | `""` (relative root / proxy) | `http://localhost:8000` or `https://catalist.internal` | Base URL prefix for FastAPI REST and SSE endpoints. |
| `NODE_ENV` | `development` | `production` | Enables React production optimizations and minification. |

When running with Nginx reverse proxy (standard Docker Compose setup), `VITE_API_BASE_URL` can be left empty (`""`) so requests route through `/api/v1/*` on the same origin, avoiding CORS issues entirely.

---

## 3. Local Development Workflows

### 3.1. Prerequisites
- Node.js $\ge 18.x$
- npm $\ge 9.x$

### 3.2. Install Dependencies
```bash
cd frontend
npm install
```

### 3.3. Run Development Server
```bash
npm --prefix frontend run dev
```
- Local URL: `http://localhost:5173`
- Hot Module Replacement (HMR) is enabled.
- Proxies `/api/v1` calls to backend running on port 8000.

### 3.4. Execute Test Suite
```bash
npm --prefix frontend test -- --run
```
Runs all 10 Vitest test suites (17 assertions) in isolated headless environments.

### 3.5. Compile Production Build
```bash
npm --prefix frontend run build
```
Executes `tsc --noEmit` (strict TypeScript validation) followed by `vite build` into `frontend/dist/`.

---

## 4. Production Deployment & Nginx Configuration

In containerized deployments, static assets in `dist/` are served by Nginx with reverse proxy rules for backend API and Server-Sent Events (SSE).

### 4.1. Sample Nginx Configuration (`docker/nginx.conf`)
```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Static Assets Caching
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, no-transform";
    }

    # SPA Routing Fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API Proxy
    location /api/v1/ {
        proxy_pass http://backend:8000/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Server-Sent Events (SSE) Streaming Proxy
    location /api/v1/agent/query/stream {
        proxy_pass http://backend:8000/api/v1/agent/query/stream;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 300s;
    }
}
```

> [!IMPORTANT]
> The `proxy_buffering off;` and `chunked_transfer_encoding off;` directives are required for `/api/v1/agent/query/stream` to prevent intermediate proxies from buffering SSE stage events before delivery to the browser.

---

## 5. Troubleshooting & Diagnostics

### Problem: SSE Stages Do Not Stream in Real Time (Batched at Completion)
- **Root Cause:** Upstream proxy (e.g. Nginx, Cloudflare, Traefik) has response buffering enabled.
- **Remedy:** Ensure `X-Accel-Buffering: no` header is set or `proxy_buffering off;` is active in Nginx.

### Problem: 404 Not Found on Page Refresh (`/research`, `/citations`, `/briefing`)
- **Root Cause:** Nginx attempting to serve static path rather than delegating routing to `index.html`.
- **Remedy:** Verify `try_files $uri $uri/ /index.html;` is present in Nginx location block.

### Problem: CORS Errors on API Calls
- **Root Cause:** Frontend host (e.g. `http://localhost:5173`) not listed in backend `CORS_ORIGINS`.
- **Remedy:** Add origin to `CORS_ORIGINS` in `.env` or use relative root proxy routing.
