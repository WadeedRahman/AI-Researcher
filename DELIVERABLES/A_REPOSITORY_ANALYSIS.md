# AI-Research Backend Repository Analysis

**Document Version:** 1.0  
**Date:** 2025-01-XX  
**Analyzed By:** Senior Developer Agent  

---

## Executive Summary

The AI-Research Backend is a FastAPI-based REST API that orchestrates autonomous scientific research agents. The system provides three operational modes for research automation, from idea generation to paper writing, with background job processing and real-time log streaming capabilities.

**Key Technologies:**
- **Backend Framework:** FastAPI 0.115.12
- **Language:** Python 3.11+
- **API Server:** Uvicorn
- **Containerization:** Docker
- **Agent Framework:** Custom multi-agent system (research_agent/inno)

---

## 1. Repository Structure

```
AI-Researcher/
├── server.py                    # Main FastAPI application
├── web_ai_researcher.py        # Gradio UI (legacy) + shared utilities
├── main_ai_researcher.py       # Entry point for agent execution
├── job_manager.py              # Background job processing
├── global_state.py             # Global application state
│
├── research_agent/             # Core agent implementation
│   ├── inno/                   # Agent framework
│   │   ├── agents/            # Agent definitions (Prepare, Survey, Plan, ML, Judge, Exp Analyser)
│   │   ├── tools/             # Tool implementations
│   │   ├── environment/       # Docker/browser environments
│   │   └── workflow/          # Workflow orchestration
│   ├── constant.py            # Configuration constants
│   └── run_infer_*.py         # Agent entry points
│
├── paper_agent/                # Paper generation agent
├── benchmark/                  # Benchmark datasets
├── docker/                     # Docker configuration
└── logs/                       # Application logs
```

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server (server.py)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ /health  │  │  /jobs   │  │  /logs   │  │   /env   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         JobManager (Background Processing)           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            main_ai_researcher.py (Orchestrator)             │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Detailed Idea    │  │ Reference-Based  │                │
│  │ Description      │  │ Ideation         │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────────────────────────────┐              │
│  │      Paper Generation Agent              │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         research_agent/inno/ (Agent Framework)              │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Prepare  │  │  Survey  │  │   Plan   │  │    ML    │   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                │
│  │  Judge   │  │   Exp    │                                │
│  │  Agent   │  │ Analyser │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         Docker Container Environment                         │
│         (tjbtech1/airesearcher:v1)                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

#### 2.2.1 FastAPI Server (`server.py`)
- **Port:** 8080 (default, configurable)
- **API Version:** 2.0.0
- **Features:**
  - RESTful API endpoints
  - Background job processing
  - Real-time log streaming (polling-based)
  - Environment variable management
  - CORS support (should be configured)

#### 2.2.2 Job Manager (`job_manager.py`)
- **Purpose:** Background job queue and processing
- **Features:**
  - Thread-safe job queue
  - Job status tracking (PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED)
  - Per-job log files
  - Progress tracking
  - Token usage tracking
- **Limitations:**
  - Single worker (respects global agent constraints)
  - Jobs stored in-memory (not persistent across restarts)

#### 2.2.3 Agent Execution (`main_ai_researcher.py`)
- **Modes:**
  1. **Detailed Idea Description:** User provides comprehensive research idea
  2. **Reference-Based Ideation:** User provides reference papers, system generates idea
  3. **Paper Generation Agent:** Generates academic paper from research results
- **Execution:** Runs within Docker containers for isolation

---

## 3. API Contract Analysis

### 3.1 Endpoints Overview

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/health` | Health check | No |
| POST | `/preflight` | Validate environment | No |
| GET | `/modes` | List available modes | No |
| POST | `/run` | Synchronous execution | No |
| POST | `/jobs` | Submit background job | No |
| GET | `/jobs` | List jobs (paginated) | No |
| GET | `/jobs/{job_id}` | Get job status | No |
| GET | `/jobs/{job_id}/progress` | Get job progress | No |
| GET | `/jobs/{job_id}/logs` | Get job logs (incremental) | No |
| GET | `/jobs/{job_id}/tokens` | Get token usage | No |
| GET | `/jobs/{job_id}/result` | Get job result | No |
| POST | `/jobs/{job_id}/cancel` | Cancel job | No |
| GET | `/logs` | Get global logs | No |
| GET | `/logs/download` | Download log file | No |
| GET | `/paper` | Download generated paper PDF | No |
| GET | `/env` | List environment variables | No |
| GET | `/env/validate` | Validate env vars for mode | No |
| PUT | `/env` | Update env variables (bulk) | No |
| POST | `/env` | Add/update env variable | No |
| DELETE | `/env/{key}` | Delete env variable | No |

### 3.2 Request/Response Patterns

#### Standard Response Format
```json
{
  "status": "success" | "error",
  "result": { /* response data */ },
  "detail": "optional error message"
}
```

#### Job Status Format
```json
{
  "id": "uuid",
  "status": "pending" | "running" | "succeeded" | "failed" | "cancelled",
  "created_at": "ISO8601 timestamp",
  "started_at": "ISO8601 timestamp" | null,
  "finished_at": "ISO8601 timestamp" | null,
  "result": { /* result data */ } | null,
  "error": "error message" | null,
  "progress": {
    "current_agent": "agent name" | null,
    "current_step": "step description" | null,
    "subtasks": [ /* subtask list */ ]
  },
  "token_usage": {
    "completion_tokens": 0,
    "prompt_tokens": 0,
    "total_tokens": 0
  }
}
```

---

## 4. Agent Execution Pipeline

### 4.1 Agent Workflow

```
1. Prepare Agent → Initialize workspace, load benchmark data
2. Survey Agent → Literature review, resource gathering
3. Plan Agent → Research plan generation
4. ML Agent → Algorithm design and implementation
5. Judge Agent → Quality assessment
6. Exp Analyser → Experimental analysis and validation
```

### 4.2 Mode-Specific Execution Paths

#### Mode 1: Detailed Idea Description
- Input: Comprehensive research idea description
- Process: Direct plan inference (`run_infer_plan`)
- Output: Research implementation and results

#### Mode 2: Reference-Based Ideation
- Input: Reference papers
- Process: Idea inference → Plan inference (`run_infer_idea`)
- Output: Generated idea + research implementation

#### Mode 3: Paper Generation Agent
- Input: Research results (category + instance_id)
- Process: Paper writing (`paper_agent/writing`)
- Output: Generated academic paper (PDF)

---

## 5. Data Models

### 5.1 Job Model
```python
JobInfo:
  - id: str (UUID)
  - status: JobStatus (enum)
  - created_at: str (ISO8601)
  - started_at: str | None
  - finished_at: str | None
  - payload: Dict[str, Any]
  - result: Dict[str, Any] | None
  - error: str | None
  - log_file: str | None
  - progress: Dict[str, Any]
  - token_usage: Dict[str, int]
```

### 5.2 Request Models
```python
RunRequest:
  - question: str (required)
  - reference: str (optional)
  - mode: str (required) # One of three modes

PreflightRequest:
  - category: str (optional)
  - instance_id: str (optional)
  - mode: str (required)

EnvItem:
  - key: str
  - value: str
```

---

## 6. Environment Variables

### 6.1 Required Variables by Mode

#### Detailed Idea Description / Reference-Based Ideation
- `CATEGORY` - Research category (e.g., "vq", "gnn", "recommendation")
- `INSTANCE_ID` - Benchmark instance identifier
- `TASK_LEVEL` - Task level (e.g., "task1")
- `CONTAINER_NAME` - Docker container name
- `WORKPLACE_NAME` - Workspace directory name
- `CACHE_PATH` - Cache directory path
- `PORT` - Agent port number
- `MAX_ITER_TIMES` - Maximum iteration count

#### Paper Generation Agent
- `CATEGORY` - Research category
- `INSTANCE_ID` - Instance identifier

#### LLM Configuration (All Modes)
- At least one of:
  - `OPENAI_API_KEY`
  - `QWEN_API_KEY`
  - `DEEPSEEK_API_KEY`

### 6.2 Optional Variables
- `OPENROUTER_API_KEY` - OpenRouter API key
- `GITHUB_AI_TOKEN` - GitHub access token
- `GOOGLE_API_KEY` - Google Search API key
- `SEARCH_ENGINE_ID` - Google Search Engine ID
- `CHUNKR_API_KEY` - Chunkr API key
- `FIRECRAWL_API_KEY` - Firecrawl API key
- `DOCKER_WORKPLACE_NAME` - Docker workspace name
- `BASE_IMAGES` - Docker base image (default: tjbtech1/airesearcher:v1)

---

## 7. Logging System

### 7.1 Log Structure
- **Global Logs:** `logs/log_YYYY-MM-DD_HH-MM-SS.log`
- **Per-Job Logs:** `logs/jobs/job_{job_id}.log`
- **Format:** Timestamped text logs with conversation parsing

### 7.2 Log Streaming
- **Mechanism:** Polling-based (client requests `/jobs/{job_id}/logs` with `last_index`)
- **Parsing:** Conversation-style parsing (User → Assistant → Tool Calls → Tool Execution)
- **Incremental Updates:** Uses `last_index` for delta updates

---

## 8. Error Handling

### 8.1 HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found (job/resource not found)
- `500` - Internal Server Error

### 8.2 Error Response Format
```json
{
  "status": "error",
  "detail": "error message"
}
```

---

## 9. Authentication & Security

### 9.1 Current State
- **No authentication** - API is publicly accessible
- **No authorization** - All endpoints are open
- **API Keys** - Stored in environment variables (`.env` file)

### 9.2 Security Considerations
- Environment variables stored in `.env` file (not in git)
- Docker container isolation for agent execution
- No rate limiting implemented
- CORS not explicitly configured (needs frontend configuration)

---

## 10. Performance Characteristics

### 10.1 Execution Times
- **Agent Execution:** Minutes to hours (varies by research complexity)
- **Log Polling:** Recommended interval: 1-3 seconds
- **Job Queue:** Single worker (sequential processing)

### 10.2 Limitations
- **In-Memory Jobs:** Not persisted across restarts
- **Single Worker:** Only one job runs at a time
- **Polling-Based Logs:** No WebSocket/SSE for real-time streaming
- **File-Based Storage:** Logs stored as files (no database)

---

## 11. Dependencies

### 11.1 Core Dependencies
- `fastapi==0.115.12` - Web framework
- `uvicorn` - ASGI server
- `pydantic==2.6.1` - Data validation
- `python-dotenv` - Environment variable management

### 11.2 Agent Dependencies
- Docker for containerized execution
- LLM APIs (OpenAI, Qwen, DeepSeek, OpenRouter)
- Various research tools (GitHub, ArXiv, web scraping)

---

## 12. Integration Points

### 12.1 External Services
1. **LLM Providers:** OpenAI, Qwen, DeepSeek, OpenRouter
2. **GitHub API:** Code search and repository access
3. **ArXiv API:** Paper search
4. **Google Search API:** Web search
5. **Chunkr API:** Document processing
6. **Firecrawl API:** Web crawling

### 12.2 File System Dependencies
- `benchmark/final/{category}/{instance_id}.json` - Benchmark data
- `logs/` - Log directory
- `casestudy_results/` - Research results
- `research_agent/workplace_paper/` - Agent workspaces
- `{category}/target_sections/{instance_id}/iclr2025_conference.pdf` - Generated papers

---

## 13. Known Issues & Limitations

### 13.1 Current Limitations
1. **No Authentication:** API is fully open
2. **No Rate Limiting:** Vulnerable to abuse
3. **In-Memory Jobs:** Lost on server restart
4. **Polling-Based Logs:** Less efficient than WebSocket/SSE
5. **Single Worker:** No parallel job execution
6. **CORS Not Configured:** May block browser requests

### 13.2 Technical Debt
1. Legacy Gradio UI code mixed with server utilities
2. Global state management (`global_state.py`)
3. File-based storage (no database)
4. No automated testing visible

---

## 14. Recommendations for Frontend Integration

### 14.1 CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 14.2 Frontend Considerations
1. **Polling Strategy:** Use exponential backoff for log polling
2. **Job Management:** Implement local state caching for jobs
3. **Error Handling:** Handle network errors gracefully
4. **Session Persistence:** Store job IDs in localStorage
5. **Real-time Updates:** Consider WebSocket implementation for future

---

## 15. API Rate Limits

**Current Status:** No rate limits implemented  
**Recommendation:** Implement rate limiting per client IP/user

---

## 16. Version Information

- **API Version:** 2.0.0
- **Backend Version:** Not explicitly versioned
- **Compatibility:** Python 3.11+

---

## Conclusion

The AI-Research Backend provides a robust foundation for autonomous research automation. The API is well-structured with clear separation of concerns, though it lacks authentication and some production-ready features. The frontend implementation should account for:

1. No authentication (handle API key management client-side)
2. Polling-based log updates (implement efficient polling)
3. Single-worker job processing (manage user expectations)
4. In-memory job storage (handle server restarts)

The system is ready for frontend integration with the noted considerations.

