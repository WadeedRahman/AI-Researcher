# AI-Research Backend API Contract (OpenAPI 3.0)

**API Version:** 2.0.0  
**Base URL:** `http://localhost:8080` (configurable)  
**Protocol:** HTTP/1.1  
**Format:** JSON  

---

## OpenAPI Specification

```yaml
openapi: 3.0.3
info:
  title: AI-Researcher API
  description: Enhanced API with progress tracking, per-job logs, and validation
  version: 2.0.0
  contact:
    name: AI-Researcher Team
    url: https://github.com/HKUDS/AI-Researcher

servers:
  - url: http://localhost:8080
    description: Local development server
  - url: https://api.airesearcher.example.com
    description: Production server (example)

tags:
  - name: Health
    description: Health check endpoints
  - name: Modes
    description: Agent mode management
  - name: Jobs
    description: Background job processing
  - name: Logs
    description: Log streaming and download
  - name: Environment
    description: Environment variable management
  - name: Papers
    description: Generated paper access

paths:
  /health:
    get:
      tags: [Health]
      summary: Health check
      description: Returns API health status and version
      operationId: getHealth
      responses:
        '200':
          description: API is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'

  /preflight:
    post:
      tags: [Modes]
      summary: Validate environment and prerequisites
      description: Validates environment variables, Docker availability, and file permissions before job submission
      operationId: preflightCheck
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PreflightRequest'
      responses:
        '200':
          description: Preflight check completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PreflightResponse'
        '400':
          description: Invalid request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /modes:
    get:
      tags: [Modes]
      summary: List available agent modes
      description: Returns all available research agent modes with descriptions and required environment variables
      operationId: getModes
      responses:
        '200':
          description: List of available modes
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ModesResponse'

  /run:
    post:
      tags: [Jobs]
      summary: Run agent synchronously
      description: Executes the research agent synchronously and returns the result. Blocks until completion.
      operationId: runAgent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RunRequest'
      responses:
        '200':
          description: Execution completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RunResponse'
        '500':
          description: Execution failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs:
    post:
      tags: [Jobs]
      summary: Submit background job
      description: Submits a research agent job for background processing. Returns immediately with job_id.
      operationId: submitJob
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RunRequest'
      responses:
        '200':
          description: Job submitted successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobSubmissionResponse'
    get:
      tags: [Jobs]
      summary: List jobs
      description: Lists jobs with optional filtering and pagination
      operationId: listJobs
      parameters:
        - name: limit
          in: query
          description: Maximum number of jobs to return
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 10
        - name: offset
          in: query
          description: Pagination offset
          required: false
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: status
          in: query
          description: Filter by job status
          required: false
          schema:
            $ref: '#/components/schemas/JobStatus'
      responses:
        '200':
          description: List of jobs
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobsListResponse'
        '400':
          description: Invalid status filter
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs/{job_id}:
    get:
      tags: [Jobs]
      summary: Get job status
      description: Returns detailed information about a specific job
      operationId: getJob
      parameters:
        - name: job_id
          in: path
          required: true
          description: Job identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Job information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobResponse'
        '404':
          description: Job not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs/{job_id}/progress:
    get:
      tags: [Jobs]
      summary: Get job progress
      description: Returns structured progress information for a job
      operationId: getJobProgress
      parameters:
        - name: job_id
          in: path
          required: true
          description: Job identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Job progress information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProgressResponse'
        '404':
          description: Job not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs/{job_id}/logs:
    get:
      tags: [Jobs]
      summary: Get job logs (incremental)
      description: Returns incremental logs for a specific job. Use last_index from previous call for delta updates.
      operationId: getJobLogs
      parameters:
        - name: job_id
          in: path
          required: true
          description: Job identifier
          schema:
            type: string
            format: uuid
        - name: last_index
          in: query
          description: Last log index from previous request (for incremental updates)
          required: false
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: max_lines
          in: query
          description: Maximum number of log lines to return
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 5000
            default: 500
      responses:
        '200':
          description: Job logs
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LogsResponse'
        '404':
          description: Job not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs/{job_id}/logs/download:
    get:
      tags: [Jobs]
      summary: Download job logs
      description: Downloads the complete log file for a job
      operationId: downloadJobLogs
      parameters:
        - name: job_id
          in: path
          required: true
          description: Job identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Log file
          content:
            text/plain:
              schema:
                type: string
                format: binary
        '404':
          description: Job or log file not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs/{job_id}/tokens:
    get:
      tags: [Jobs]
      summary: Get job token usage
      description: Returns token usage statistics for a job
      operationId: getJobTokens
      parameters:
        - name: job_id
          in: path
          required: true
          description: Job identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Token usage information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenUsageResponse'
        '404':
          description: Job not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs/{job_id}/result:
    get:
      tags: [Jobs]
      summary: Get job result
      description: Returns the final result of a completed job
      operationId: getJobResult
      parameters:
        - name: job_id
          in: path
          required: true
          description: Job identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Job result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobResultResponse'
        '404':
          description: Job not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /jobs/{job_id}/cancel:
    post:
      tags: [Jobs]
      summary: Cancel job
      description: Cancels a running or pending job
      operationId: cancelJob
      parameters:
        - name: job_id
          in: path
          required: true
          description: Job identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Job cancellation initiated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CancelJobResponse'
        '404':
          description: Job not found or cannot be cancelled
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /logs:
    get:
      tags: [Logs]
      summary: Get global logs (incremental)
      description: Returns incremental global logs. Use last_index from previous call for delta updates.
      operationId: getLogs
      parameters:
        - name: last_index
          in: query
          description: Last log index from previous request
          required: false
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: max_lines
          in: query
          description: Maximum number of log lines to return
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 5000
            default: 500
      responses:
        '200':
          description: Global logs
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LogsResponse'

  /logs/download:
    get:
      tags: [Logs]
      summary: Download global logs
      description: Downloads the most recent global log file
      operationId: downloadLogs
      responses:
        '200':
          description: Log file
          content:
            text/plain:
              schema:
                type: string
                format: binary
        '404':
          description: Log file not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /paper:
    get:
      tags: [Papers]
      summary: Download generated paper
      description: Downloads the generated PDF paper if available
      operationId: getPaper
      responses:
        '200':
          description: Paper PDF
          content:
            application/pdf:
              schema:
                type: string
                format: binary
        '404':
          description: Paper not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /env:
    get:
      tags: [Environment]
      summary: List environment variables
      description: Lists all environment variables with their sources and API guide links
      operationId: getEnvVars
      responses:
        '200':
          description: Environment variables
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvVarsResponse'
    put:
      tags: [Environment]
      summary: Update environment variables (bulk)
      description: Updates multiple environment variables at once
      operationId: updateEnvVars
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/EnvItem'
      responses:
        '200':
          description: Environment variables updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvUpdateResponse'
        '500':
          description: Update failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
    post:
      tags: [Environment]
      summary: Add/update environment variable
      description: Adds or updates a single environment variable
      operationId: addEnvVar
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/EnvItem'
      responses:
        '200':
          description: Environment variable added/updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvUpdateResponse'
        '500':
          description: Operation failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /env/validate:
    get:
      tags: [Environment]
      summary: Validate environment variables for mode
      description: Validates that all required environment variables are set for a specific mode
      operationId: validateEnvVars
      parameters:
        - name: mode
          in: query
          required: true
          description: Mode to validate
          schema:
            type: string
            enum: [Detailed Idea Description, Reference-Based Ideation, Paper Generation Agent]
      responses:
        '200':
          description: Validation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvValidationResponse'
        '400':
          description: Invalid mode
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /env/{key}:
    delete:
      tags: [Environment]
      summary: Delete environment variable
      description: Deletes an environment variable
      operationId: deleteEnvVar
      parameters:
        - name: key
          in: path
          required: true
          description: Environment variable key
          schema:
            type: string
      responses:
        '200':
          description: Environment variable deleted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnvUpdateResponse'
        '500':
          description: Deletion failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

components:
  schemas:
    HealthResponse:
      type: object
      properties:
        status:
          type: string
          example: ok
        timestamp:
          type: string
          format: date-time
          example: 2025-01-01T12:00:00Z
        version:
          type: string
          example: 2.0.0

    PreflightRequest:
      type: object
      required: [mode]
      properties:
        mode:
          type: string
          enum: [Detailed Idea Description, Reference-Based Ideation, Paper Generation Agent]
          description: Mode to validate
        category:
          type: string
          nullable: true
          description: Research category (optional)
        instance_id:
          type: string
          nullable: true
          description: Instance identifier (optional)

    PreflightResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success, error]
        valid:
          type: boolean
        errors:
          type: array
          items:
            type: string
        warnings:
          type: array
          items:
            type: string
        category:
          type: string
          nullable: true
        instance_id:
          type: string
          nullable: true

    RunRequest:
      type: object
      required: [question, mode]
      properties:
        question:
          type: string
          description: User prompt or category depending on mode
        reference:
          type: string
          default: ""
          description: Optional references text
        mode:
          type: string
          enum: [Detailed Idea Description, Reference-Based Ideation, Paper Generation Agent]
          description: Research mode

    RunResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success, error]
        result:
          type: object
          properties:
            answer:
              type: string
            token_count:
              type: string
            status:
              type: string

    JobStatus:
      type: string
      enum: [pending, running, succeeded, failed, cancelled]

    JobInfo:
      type: object
      properties:
        id:
          type: string
          format: uuid
        status:
          $ref: '#/components/schemas/JobStatus'
        created_at:
          type: string
          format: date-time
        started_at:
          type: string
          format: date-time
          nullable: true
        finished_at:
          type: string
          format: date-time
          nullable: true
        payload:
          type: object
        result:
          type: object
          nullable: true
        error:
          type: string
          nullable: true
        log_file:
          type: string
          nullable: true
        progress:
          $ref: '#/components/schemas/JobProgress'
        token_usage:
          $ref: '#/components/schemas/TokenUsage'

    JobProgress:
      type: object
      properties:
        current_agent:
          type: string
          nullable: true
        current_step:
          type: string
          nullable: true
        subtasks:
          type: array
          items:
            $ref: '#/components/schemas/Subtask'
        estimated_time_remaining:
          type: string
          nullable: true

    Subtask:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        status:
          type: string
          enum: [pending, in_progress, completed, failed]

    TokenUsage:
      type: object
      properties:
        completion_tokens:
          type: integer
        prompt_tokens:
          type: integer
        total_tokens:
          type: integer

    JobSubmissionResponse:
      type: object
      properties:
        status:
          type: string
          enum: [queued]
        job_id:
          type: string
          format: uuid

    JobsListResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          type: object
          properties:
            jobs:
              type: array
              items:
                $ref: '#/components/schemas/JobInfo'
            total:
              type: integer
            limit:
              type: integer
            offset:
              type: integer

    JobResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          $ref: '#/components/schemas/JobInfo'

    ProgressResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          $ref: '#/components/schemas/JobProgress'

    LogsResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          type: object
          properties:
            conversations:
              type: array
              items:
                type: array
                items:
                  type: string
                  nullable: true
            last_index:
              type: integer
            job_status:
              type: string
              nullable: true
              description: Only present in job logs endpoint

    TokenUsageResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          $ref: '#/components/schemas/TokenUsage'

    JobResultResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success, pending]
        result:
          type: object
          nullable: true
          properties:
            status:
              $ref: '#/components/schemas/JobStatus'
            result:
              type: object
              nullable: true
            error:
              type: string
              nullable: true
            token_usage:
              $ref: '#/components/schemas/TokenUsage'
        detail:
          type: string
          nullable: true

    CancelJobResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          type: object
          properties:
            status:
              $ref: '#/components/schemas/JobStatus'

    ModesResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              description:
                type: string
              required_env_vars:
                type: array
                items:
                  type: string

    EnvItem:
      type: object
      required: [key, value]
      properties:
        key:
          type: string
        value:
          type: string

    EnvVarInfo:
      type: object
      properties:
        value:
          type: string
        source:
          type: string
          enum: [System, .env file, Frontend configuration]
        api_guide:
          type: string
          format: uri
          nullable: true

    EnvVarsResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          type: object
          additionalProperties:
            $ref: '#/components/schemas/EnvVarInfo'

    EnvUpdateResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success, error]
        detail:
          type: string

    EnvValidationResponse:
      type: object
      properties:
        status:
          type: string
          enum: [success]
        result:
          type: object
          properties:
            valid:
              type: boolean
            missing:
              type: array
              items:
                type: string
            incorrect:
              type: array
              items:
                type: string
            mode:
              type: string

    ErrorResponse:
      type: object
      properties:
        status:
          type: string
          enum: [error]
        detail:
          type: string

```

---

## Business Rules

### 1. Job Processing
- Only one job can run at a time (single worker)
- Jobs are stored in-memory and lost on server restart
- Job status transitions: `pending` → `running` → `succeeded`/`failed`/`cancelled`
- Cancellation is best-effort; may not stop immediately if running

### 2. Environment Variables
- Priority: Frontend configuration > .env file > System environment
- Required variables vary by mode (see Environment Variables section)
- At least one LLM API key must be configured

### 3. Log Streaming
- Logs are parsed into conversation-style format
- Incremental updates use `last_index` parameter
- Maximum 5000 lines per request
- Recommended polling interval: 1-3 seconds

### 4. Mode Requirements

#### Detailed Idea Description / Reference-Based Ideation
- Requires: CATEGORY, INSTANCE_ID, TASK_LEVEL, CONTAINER_NAME, WORKPLACE_NAME, CACHE_PATH, PORT, MAX_ITER_TIMES
- Benchmark file must exist: `research_agent/benchmark/final/{category}/{instance_id}.json`

#### Paper Generation Agent
- Requires: CATEGORY, INSTANCE_ID
- Paper path: `{category}/target_sections/{instance_id}/iclr2025_conference.pdf`

---

## Error Handling Patterns

### Standard Error Response
```json
{
  "status": "error",
  "detail": "Error message"
}
```

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found (job/resource not found)
- `500`: Internal Server Error

### Common Error Scenarios

1. **Invalid Mode**
   - Status: 400
   - Detail: "Invalid mode: {mode}. Valid modes: [...]"

2. **Missing Environment Variable**
   - Status: 200 (in preflight/validate)
   - Response: `{ "valid": false, "missing": [...] }`

3. **Job Not Found**
   - Status: 404
   - Detail: "job not found"

4. **Execution Failure**
   - Status: 500
   - Detail: Exception message

---

## Rate Limits

**Current Status:** No rate limits implemented  
**Recommendation:** Implement rate limiting per client IP/user

---

## Security Considerations

### Current State
- No authentication required
- No authorization checks
- API keys stored in environment variables (`.env` file)

### Recommendations
1. Implement authentication (JWT tokens or API keys)
2. Add rate limiting
3. Configure CORS appropriately
4. Use HTTPS in production
5. Validate and sanitize all inputs

---

## Streaming/Real-time Considerations

### Current Implementation
- **Polling-based:** Client polls for updates
- **No WebSocket/SSE:** Real-time streaming not implemented
- **Incremental Logs:** Use `last_index` for delta updates

### Recommendations
1. Implement Server-Sent Events (SSE) for real-time log streaming
2. Consider WebSocket for bidirectional communication
3. Implement exponential backoff for polling clients

---

## Version History

- **2.0.0** (Current): Enhanced API with progress tracking, per-job logs, and validation
- Previous versions: Not documented

---

## Example Requests

### Submit Background Job
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Research idea description",
    "reference": "Optional references",
    "mode": "Detailed Idea Description"
  }'
```

### Get Job Logs (Incremental)
```bash
curl "http://localhost:8080/jobs/{job_id}/logs?last_index=0&max_lines=500"
```

### Poll Job Status
```bash
curl "http://localhost:8080/jobs/{job_id}"
```

---

## Frontend Integration Notes

1. **Polling Strategy:** Use exponential backoff (start at 1s, max 5s)
2. **Error Handling:** Handle network errors gracefully, retry with exponential backoff
3. **Session Persistence:** Store job IDs in localStorage for recovery after page refresh
4. **CORS:** Ensure backend CORS middleware is configured for frontend origin
5. **Environment Variables:** Frontend can manage env vars via `/env` endpoints

---

**End of API Contract**

