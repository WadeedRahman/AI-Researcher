# Integration Instructions - AI-Researcher Frontend & Backend

**Document Version:** 1.0  
**Date:** 2025-01-XX  

---

## Overview

This document provides step-by-step instructions for integrating the Vue.js frontend application with the AI-Researcher backend API.

---

## Prerequisites

### Backend Requirements
- Python 3.11+
- FastAPI server running (default: `http://localhost:8080`)
- Environment variables configured (see Backend README)
- CORS middleware configured (see CORS Configuration below)

### Frontend Requirements
- Node.js 18+ or 20+
- pnpm (recommended) or npm/yarn
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

---

## Step 1: Backend CORS Configuration

The backend **must** be configured to allow requests from the frontend origin.

### Update `server.py`

Add CORS middleware to your FastAPI application:

```python
from fastapi.middleware.cors import CORSMiddleware

# Add after app = FastAPI(...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        # Add production frontend URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Restart Backend Server

After adding CORS middleware, restart your FastAPI server:

```bash
# If using uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 8080 --reload

# Or if using Docker
docker-compose restart
```

---

## Step 2: Frontend Setup

### 2.1 Install Dependencies

```bash
cd frontend
pnpm install
```

If you don't have pnpm:

```bash
npm install -g pnpm
# or
npm install
```

### 2.2 Configure Environment Variables

Create `.env` file in the `frontend/` directory:

```bash
cp .env.example .env
```

Edit `.env` and set your backend API URL:

```env
VITE_API_BASE_URL=http://localhost:8080
VITE_APP_TITLE=AI Researcher
VITE_LOG_POLL_INTERVAL=2000
VITE_MAX_LOG_LINES=500
```

**Important:** 
- For production, set `VITE_API_BASE_URL` to your production backend URL
- Environment variables prefixed with `VITE_` are embedded at build time
- Changes to `.env` require restarting the dev server

### 2.3 Start Development Server

```bash
pnpm dev
```

The frontend should now be available at `http://localhost:5173`

---

## Step 3: Verify Integration

### 3.1 Health Check

1. Open `http://localhost:5173` in your browser
2. Open browser DevTools (F12) → Network tab
3. Navigate to the home page
4. Check for successful requests to `/health` endpoint
5. Verify response status is `200 OK`

### 3.2 Test Job Submission

1. Fill in the research form on the home page:
   - Enter a research question
   - Select a mode
   - Click "Start Research"
2. Verify:
   - Job is submitted successfully
   - Redirected to job detail page
   - Job status updates in real-time
   - Logs stream correctly

---

## Step 4: Production Deployment

### 4.1 Build Frontend

```bash
cd frontend
pnpm build
```

This creates a `dist/` directory with production-ready static files.

### 4.2 Configure Production Environment

Before building, update `.env` with production values:

```env
VITE_API_BASE_URL=https://api.yourapp.com
VITE_APP_TITLE=AI Researcher
```

Rebuild after updating environment variables:

```bash
pnpm build
```

### 4.3 Deploy Options

#### Option A: Static Hosting (Recommended)

Deploy the `dist/` directory to:
- **Vercel:** `vercel --prod`
- **Netlify:** Drag and drop `dist/` folder or connect Git repo
- **GitHub Pages:** Push `dist/` to `gh-pages` branch
- **Nginx/Apache:** Copy `dist/` contents to web root

#### Option B: Docker

Create `Dockerfile` in `frontend/`:

```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build -t ai-researcher-frontend .
docker run -p 80:80 ai-researcher-frontend
```

#### Option C: Serve with Backend

Serve static files from FastAPI:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
```

### 4.4 Update CORS for Production

Update backend CORS to allow production frontend URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",
        "https://www.your-frontend-domain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Step 5: API Endpoint Configuration

### 5.1 Base URL Configuration

The frontend uses the base URL from `VITE_API_BASE_URL`. Ensure this matches your backend server address.

**Development:**
```env
VITE_API_BASE_URL=http://localhost:8080
```

**Production:**
```env
VITE_API_BASE_URL=https://api.yourapp.com
```

### 5.2 Proxy Configuration (Optional)

For development, you can configure Vite proxy in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

Then use `/api` prefix in frontend requests (requires API client update).

---

## Step 6: Environment Variable Management

### 6.1 Backend Environment Variables

The frontend provides a UI for managing backend environment variables via the `/env` endpoints.

**Access:**
1. Navigate to `/environment` in the frontend
2. View/edit environment variables
3. Changes are saved to backend `.env` file

### 6.2 Required Environment Variables

Before using the system, configure these in the backend:

#### All Modes
- At least one LLM API key:
  - `OPENAI_API_KEY`
  - `QWEN_API_KEY`
  - `DEEPSEEK_API_KEY`

#### Detailed Idea Description / Reference-Based Ideation
- `CATEGORY` - Research category
- `INSTANCE_ID` - Instance identifier
- `TASK_LEVEL` - Task level
- `CONTAINER_NAME` - Docker container name
- `WORKPLACE_NAME` - Workspace name
- `CACHE_PATH` - Cache directory path
- `PORT` - Agent port
- `MAX_ITER_TIMES` - Max iterations

#### Paper Generation Agent
- `CATEGORY` - Research category
- `INSTANCE_ID` - Instance identifier

---

## Step 7: Session Persistence

The frontend automatically persists:
- Active job IDs
- View preferences
- Theme settings

**Storage:** `localStorage` (browser-based)

**Recovery:** After page refresh, active jobs are restored and polling resumes automatically.

---

## Step 8: Troubleshooting

### Issue: CORS Errors

**Symptom:** Browser console shows CORS errors

**Solution:**
1. Verify CORS middleware is configured in backend
2. Check allowed origins match frontend URL
3. Ensure credentials are enabled if using cookies
4. Check backend server is running

### Issue: API Connection Failed

**Symptom:** Network errors or connection refused

**Solution:**
1. Verify `VITE_API_BASE_URL` matches backend URL
2. Check backend server is running and accessible
3. Check firewall/network settings
4. Verify port is not blocked

### Issue: Jobs Not Updating

**Symptom:** Job status doesn't update in real-time

**Solution:**
1. Check polling interval in environment variables
2. Verify job endpoint is accessible
3. Check browser console for errors
4. Verify session persistence is working

### Issue: Logs Not Streaming

**Symptom:** Logs don't appear in real-time

**Solution:**
1. Verify log endpoint is accessible
2. Check `last_index` is being updated correctly
3. Increase `max_lines` if logs are truncated
4. Check backend log file exists

### Issue: Environment Variables Not Saving

**Symptom:** Changes to env vars don't persist

**Solution:**
1. Verify backend has write permissions to `.env` file
2. Check backend `/env` endpoints are working
3. Verify API client error handling

---

## Step 9: Testing Integration

### 9.1 Manual Testing Checklist

- [ ] Backend server starts successfully
- [ ] Frontend dev server starts successfully
- [ ] Health check endpoint responds
- [ ] Home page loads without errors
- [ ] Job submission works
- [ ] Job status updates in real-time
- [ ] Logs stream correctly
- [ ] Environment variables can be managed
- [ ] Session persists after page refresh
- [ ] Error messages display correctly

### 9.2 Automated Testing

Run frontend tests:

```bash
cd frontend
pnpm test
```

Run with coverage:

```bash
pnpm test:coverage
```

---

## Step 10: Performance Optimization

### 10.1 Polling Optimization

Adjust polling intervals based on usage:

```env
# Faster updates (more server load)
VITE_LOG_POLL_INTERVAL=1000

# Slower updates (less server load)
VITE_LOG_POLL_INTERVAL=5000
```

### 10.2 Log Streaming

Limit log size to prevent memory issues:

```env
# Smaller chunks (more requests)
VITE_MAX_LOG_LINES=250

# Larger chunks (fewer requests)
VITE_MAX_LOG_LINES=1000
```

---

## Step 11: Security Considerations

### 11.1 API Keys

- **Never** expose API keys in frontend code
- API keys are managed via backend environment variables
- Frontend only displays masked values

### 11.2 HTTPS in Production

- Use HTTPS for both frontend and backend in production
- Update `VITE_API_BASE_URL` to use `https://`
- Configure SSL certificates

### 11.3 CORS Security

- Restrict CORS origins to specific domains in production
- Don't use `allow_origins=["*"]` in production
- Use credentials only when necessary

---

## Step 12: Monitoring & Logging

### 12.1 Frontend Error Tracking

Consider integrating error tracking:
- Sentry
- LogRocket
- Bugsnag

Example (Sentry):

```typescript
// main.ts
import * as Sentry from "@sentry/vue"

Sentry.init({
  app,
  dsn: "YOUR_SENTRY_DSN",
})
```

### 12.2 API Monitoring

Monitor backend API:
- Response times
- Error rates
- Request volumes

Tools:
- Prometheus + Grafana
- Datadog
- New Relic

---

## Additional Resources

- **Backend API Docs:** See `B_API_CONTRACT.md`
- **Frontend Architecture:** See `C_FRONTEND_ARCHITECTURE.md`
- **Repository Analysis:** See `A_REPOSITORY_ANALYSIS.md`
- **Risks & Optimizations:** See `F_RISKS_OPTIMIZATIONS.md`

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review API contract documentation
3. Check backend logs
4. Check browser console for errors

---

**End of Integration Instructions**

