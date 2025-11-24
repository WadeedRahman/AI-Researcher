import os
import threading
import datetime
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
import global_state

# Reuse existing orchestration and logging utilities
from web_ai_researcher import (
    setup_logging,
    log_reader_thread,
    get_latest_logs,
    init_env_file,
    load_env_vars,
    save_env_vars,
    add_env_var,
    delete_env_var,
    run_ai_researcher,
    return_paper_file,
    LOG_QUEUE,
    MODULE_DESCRIPTIONS,
    is_api_related,
    get_api_guide,
    STOP_REQUESTED,
)
from job_manager import JobManager, JobStatus, build_default_runner, job_to_dict

# Initialize environment
load_dotenv(find_dotenv(), override=True)

app = FastAPI(title="AI-Researcher API", version="2.0.0", description="Enhanced API with progress tracking, per-job logs, and validation")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server (default)
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://novix.videmak.net"
        # Add production frontend URL here when deploying
        # "https://your-frontend-domain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Local state for log indexing per client/session (simple, stateless default)
_DEFAULT_MAX_LINES = 500

# Per-job log queues
_job_log_queues: Dict[str, Any] = {}
_job_log_threads: Dict[str, threading.Thread] = {}


class RunRequest(BaseModel):
    question: str = Field(..., description="User prompt or category depending on mode")
    reference: Optional[str] = Field("", description="Optional references text")
    mode: str = Field(
        ...,
        description="One of: 'Idea Spark', 'Deep Survey', 'Auto Experiment', 'Detailed Idea Description', 'Reference-Based Ideation', 'Paper Generation Agent'",
    )


class PreflightRequest(BaseModel):
    category: Optional[str] = None
    instance_id: Optional[str] = None
    mode: str = Field(..., description="Mode to validate")


class EnvItem(BaseModel):
    key: str
    value: str


# Job manager (single worker to respect global agent constraints)
_job_manager = JobManager(build_default_runner(run_ai_researcher))


def _setup_job_logging(job_id: str, log_file: str):
    """Set up per-job log reading thread"""
    if job_id in _job_log_threads:
        return
    
    job_queue = type(LOG_QUEUE)()
    _job_log_queues[job_id] = job_queue
    
    def job_log_reader():
        try:
            if not os.path.exists(log_file):
                return
            with open(log_file, "r", encoding="utf-8") as f:
                f.seek(0, 2)  # Move to end
                while True:
                    line = f.readline()
                    if line:
                        job_queue.put(line)
                    else:
                        import time
                        time.sleep(0.1)
        except Exception as e:
            print(f"Error in job log reader for {job_id}: {e}")
    
    thread = threading.Thread(target=job_log_reader, daemon=True, name=f"log_reader_{job_id}")
    thread.start()
    _job_log_threads[job_id] = thread


@app.on_event("startup")
def startup() -> None:
    # Set up logging and background log reader (mirrors UI behavior)
    log_file = setup_logging()
    thread = threading.Thread(target=log_reader_thread, args=(log_file,), daemon=True)
    thread.start()
    # Ensure .env exists
    init_env_file()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0",
    }


@app.post("/preflight")
def preflight(req: PreflightRequest) -> Dict[str, Any]:
    """
    Validate environment and prerequisites before job submission.
    Returns validation results with actionable errors.
    """
    errors = []
    warnings = []
    
    # Load current env vars
    env_vars = load_env_vars()
    env_dict = {k: v[0] if isinstance(v, tuple) else v for k, v in env_vars.items()}
    
    # Determine category and instance_id
    category = req.category or env_dict.get("CATEGORY")
    instance_id = req.instance_id or env_dict.get("INSTANCE_ID")
    
    # Validate mode
    if req.mode not in MODULE_DESCRIPTIONS:
        errors.append(f"Invalid mode: {req.mode}. Valid modes: {list(MODULE_DESCRIPTIONS.keys())}")
    
    # Validate required env vars based on mode
    required_vars = {
        "Detailed Idea Description": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
        "Reference-Based Ideation": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
        "Paper Generation Agent": ["CATEGORY", "INSTANCE_ID"]
    }
    
    mode_required = required_vars.get(req.mode, [])
    for var in mode_required:
        if not env_dict.get(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check for at least one LLM API key
    llm_keys = ["OPENAI_API_KEY", "QWEN_API_KEY", "DEEPSEEK_API_KEY"]
    if not any(env_dict.get(key) for key in llm_keys):
        errors.append("Missing LLM API key. Set at least one of: OPENAI_API_KEY, QWEN_API_KEY, DEEPSEEK_API_KEY")
    
    # Validate benchmark file exists
    if category and instance_id:
        benchmark_path = f"research_agent/benchmark/final/{category}/{instance_id}.json"
        if not os.path.exists(benchmark_path):
            errors.append(f"Benchmark file not found: {benchmark_path}")
    
    # Check Docker
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            warnings.append("Docker daemon may not be running")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        warnings.append("Docker not available or not responding")
    
    # Check Docker image
    base_image = env_dict.get("BASE_IMAGES", "tjbtech1/paperapp:latest")
    try:
        result = subprocess.run(
            ["docker", "images", "-q", base_image],
            capture_output=True,
            text=True,
            timeout=5
        )
        if not result.stdout.strip():
            warnings.append(f"Docker image '{base_image}' not found locally. Will attempt to pull on first use.")
    except Exception:
        pass
    
    # Check file permissions
    dirs_to_check = ["logs", "casestudy_results", "research_agent/workplace_paper"]
    for dir_path in dirs_to_check:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if os.path.exists(full_path):
            if not os.access(full_path, os.W_OK):
                errors.append(f"No write permission for directory: {dir_path}")
        else:
            try:
                os.makedirs(full_path, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {str(e)}")
    
    return {
        "status": "success" if not errors else "error",
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "category": category,
        "instance_id": instance_id,
    }


@app.get("/modes")
def get_modes() -> Dict[str, Any]:
    """List available agent modes with descriptions and examples"""
    modes = []
    for mode_name, description in MODULE_DESCRIPTIONS.items():
        # Skip Paper Generation Agent - it runs automatically
        if mode_name == "Paper Generation Agent":
            continue
        modes.append({
            "name": mode_name,
            "description": description,
            "required_env_vars": {
                "Idea Spark": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
                "Deep Survey": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
                "Auto Experiment": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
                "Detailed Idea Description": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
                "Reference-Based Ideation": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
                "Paper Generation Agent": ["CATEGORY", "INSTANCE_ID"]
            }.get(mode_name, [])
        })
    return {"status": "success", "result": modes}


@app.post("/run")
def run(req: RunRequest) -> Dict[str, Any]:
    try:
        # Delegates to the same function used by the Gradio UI
        answer, token_count, status = run_ai_researcher(
            req.question, req.reference or "", req.mode
        )
        return {
            "status": "success",
            "result": {
                "answer": answer,
                "token_count": token_count,
                "status": status,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs")
def submit_job(req: RunRequest) -> Dict[str, Any]:
    """
    Submit a background job to run an agent. Returns a job_id to poll.
    """
    job = _job_manager.submit(req.dict())
    
    # Set up per-job logging
    if job.log_file:
        _setup_job_logging(job.id, job.log_file)
        # Set log path in global state for this job
        global_state.LOG_PATH = job.log_file
    
    return {"status": "queued", "job_id": job.id}


@app.get("/jobs")
def list_jobs(
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """List jobs with optional filtering"""
    all_jobs = _job_manager.list_jobs()
    
    # Filter by status if provided
    if status:
        try:
            status_enum = JobStatus(status)
            all_jobs = {k: v for k, v in all_jobs.items() if v.status == status_enum}
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    # Sort by created_at (newest first)
    sorted_jobs = sorted(
        all_jobs.items(),
        key=lambda x: x[1].created_at,
        reverse=True
    )
    
    # Apply pagination
    paginated = sorted_jobs[offset:offset + limit]
    
    return {
        "status": "success",
        "result": {
            "jobs": [job_to_dict(job) for _, job in paginated],
            "total": len(all_jobs),
            "limit": limit,
            "offset": offset
        }
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    job = _job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    # Automatically update progress if job is running and has a log file
    if job.status == JobStatus.RUNNING and job.log_file and os.path.exists(job.log_file):
        try:
            # Parse logs to detect agent transitions (same logic as /progress endpoint)
            agents = ["Prepare Agent", "Survey Agent", "Plan Agent", "ML Agent", "Judge Agent", "Exp Analyser"]
            detected_agents = []
            
            with open(job.log_file, "r", encoding="utf-8") as f:
                content = f.read()
                for agent in agents:
                    if agent in content and agent not in detected_agents:
                        detected_agents.append(agent)
            
            # Update progress if we detected new agents
            if detected_agents:
                job.progress["current_agent"] = detected_agents[-1] if detected_agents else None
                job.progress["subtasks"] = [
                    {"id": str(i+1), "name": agent, "status": "completed"}
                    for i, agent in enumerate(detected_agents)
                ] + [
                    {"id": str(len(detected_agents)+1), "name": agent, "status": "pending"}
                    for agent in agents[len(detected_agents):]
                ]
        except Exception:
            # If progress update fails, continue with existing progress
            pass
    
    return {"status": "success", "result": job_to_dict(job)}


@app.get("/jobs/{job_id}/progress")
def get_job_progress(job_id: str) -> Dict[str, Any]:
    """Get structured progress information for a job"""
    job = _job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    # Parse logs to detect agent transitions
    agents = ["Prepare Agent", "Survey Agent", "Plan Agent", "ML Agent", "Judge Agent", "Exp Analyser"]
    detected_agents = []
    
    if job.log_file and os.path.exists(job.log_file):
        try:
            with open(job.log_file, "r", encoding="utf-8") as f:
                content = f.read()
                for agent in agents:
                    if agent in content and agent not in detected_agents:
                        detected_agents.append(agent)
        except Exception:
            pass
    
    # Update progress if we detected new agents
    if detected_agents:
        job.progress["current_agent"] = detected_agents[-1] if detected_agents else None
        job.progress["subtasks"] = [
            {"id": str(i+1), "name": agent, "status": "completed"}
            for i, agent in enumerate(detected_agents)
        ] + [
            {"id": str(len(detected_agents)+1), "name": agent, "status": "pending"}
            for agent in agents[len(detected_agents):]
        ]
    
    return {
        "status": "success",
        "result": job.progress
    }


@app.get("/jobs/{job_id}/logs")
def get_job_logs(
    job_id: str,
    last_index: int = Query(0, ge=0),
    max_lines: int = Query(_DEFAULT_MAX_LINES, gt=0, le=5000)
) -> Dict[str, Any]:
    """
    Get incremental logs for a specific job. Uses per-job log file if available.
    """
    job = _job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    # Use per-job log queue if available, otherwise fall back to global
    log_queue = _job_log_queues.get(job_id, LOG_QUEUE)
    
    state: List[Any] = []
    conversations, updated_index = get_latest_logs(max_lines, state, log_queue, last_index)
    job.last_index = updated_index
    
    return {
        "status": "success",
        "result": {
            "conversations": conversations,
            "last_index": updated_index,
            "job_status": job.status.value,
        },
    }


@app.get("/jobs/{job_id}/logs/download")
def download_job_logs(job_id: str) -> FileResponse:
    """Download the log file for a specific job"""
    job = _job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    if not job.log_file or not os.path.exists(job.log_file):
        raise HTTPException(status_code=404, detail="log file not found for this job")
    
    return FileResponse(
        path=job.log_file,
        filename=f"job_{job_id}_logs.log",
        media_type="text/plain"
    )


@app.get("/jobs/{job_id}/tokens")
def get_job_tokens(job_id: str) -> Dict[str, Any]:
    """Get token usage for a job"""
    job = _job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    return {
        "status": "success",
        "result": job.token_usage
    }


@app.get("/jobs/{job_id}/result")
def get_job_result(job_id: str) -> Dict[str, Any]:
    job = _job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status not in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED]:
        return {"status": "pending", "detail": "job not finished"}
    return {
        "status": "success",
        "result": {
            "status": job.status.value,
            "result": job.result,
            "error": job.error,
            "token_usage": job.token_usage,
        },
    }


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> Dict[str, Any]:
    """Cancel a job and set STOP_REQUESTED event"""
    success = _job_manager.cancel(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="job not found or cannot cancel")
    
    # Set global stop event
    STOP_REQUESTED.set()
    
    job = _job_manager.get(job_id)
    return {"status": "success", "result": {"status": job.status.value}}


@app.get("/logs")
def logs(
    last_index: int = Query(0, ge=0),
    max_lines: int = Query(_DEFAULT_MAX_LINES, gt=0, le=5000)
) -> Dict[str, Any]:
    """
    Returns parsed conversation logs. Provide last_index from previous call for incremental updates.
    """
    state: List[Any] = []
    conversations, updated_index = get_latest_logs(max_lines, state, LOG_QUEUE, last_index)
    return {
        "status": "success",
        "result": {
            "conversations": conversations,
            "last_index": updated_index,
        },
    }


@app.get("/logs/download")
def download_logs() -> FileResponse:
    """Download the main research log file"""
    # Get the most recent log file from logs directory
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        raise HTTPException(status_code=404, detail="logs directory not found")
    
    # Get most recent log file
    log_files = sorted(
        [f for f in os.listdir(logs_dir) if f.endswith(".log") and not f.startswith("job_")],
        key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)),
        reverse=True
    )
    
    if not log_files:
        raise HTTPException(status_code=404, detail="no log files found")
    
    log_path = os.path.join(logs_dir, log_files[0])
    return FileResponse(
        path=log_path,
        filename=log_files[0],
        media_type="text/plain"
    )


@app.get("/paper", response_model=None)
def paper():
    """
    Returns the generated paper PDF if present.
    Path is derived from CATEGORY and INSTANCE_ID environment vars.
    """
    try:
        paper_path = return_paper_file()
        if paper_path and os.path.exists(paper_path):
            return FileResponse(
                path=paper_path,
                filename=os.path.basename(paper_path),
                media_type="application/pdf"
            )
        return JSONResponse(
            status_code=404,
            content={"status": "not_found", "detail": f"Paper not found at {paper_path}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/paper/logs/download")
def download_paper_logs() -> FileResponse:
    """Download paper generation logs"""
    logs_dir = os.path.join(os.path.dirname(__file__), "paper_agent", "paper_logs")
    if not os.path.exists(logs_dir):
        raise HTTPException(status_code=404, detail="paper logs directory not found")
    
    # Get most recent log file
    log_files = sorted(
        [f for f in os.listdir(logs_dir) if f.endswith(".log")],
        key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)),
        reverse=True
    )
    
    if not log_files:
        raise HTTPException(status_code=404, detail="no paper log files found")
    
    log_path = os.path.join(logs_dir, log_files[0])
    return FileResponse(
        path=log_path,
        filename=log_files[0],
        media_type="text/plain"
    )


@app.get("/env")
def get_env() -> Dict[str, Any]:
    """
    Lists environment variables merged from system, .env, and frontend overrides.
    Includes API guide links for relevant variables.
    """
    env_vars = load_env_vars()
    result = {}
    
    for k, v in env_vars.items():
        value = v[0] if isinstance(v, tuple) else v
        source = v[1] if isinstance(v, tuple) else "unknown"
        
        item = {
            "value": value,
            "source": source
        }
        
        # Add API guide link if available
        if is_api_related(k):
            guide = get_api_guide(k)
            if guide:
                item["api_guide"] = guide
        
        result[k] = item
    
    return {"status": "success", "result": result}


@app.get("/env/validate")
def validate_env(mode: str = Query(..., description="Mode to validate")) -> Dict[str, Any]:
    """Validate environment variables for a specific mode"""
    env_vars = load_env_vars()
    env_dict = {k: v[0] if isinstance(v, tuple) else v for k, v in env_vars.items()}
    
    required_vars = {
        "Detailed Idea Description": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
        "Reference-Based Ideation": ["CATEGORY", "INSTANCE_ID", "TASK_LEVEL", "CONTAINER_NAME", "WORKPLACE_NAME", "CACHE_PATH", "PORT", "MAX_ITER_TIMES"],
        "Paper Generation Agent": ["CATEGORY", "INSTANCE_ID"]
    }
    
    if mode not in required_vars:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    
    missing = []
    incorrect = []
    
    for var in required_vars[mode]:
        if not env_dict.get(var):
            missing.append(var)
        elif var == "PORT" and not env_dict[var].isdigit():
            incorrect.append(f"{var} must be a number")
        elif var == "MAX_ITER_TIMES" and not env_dict[var].isdigit():
            incorrect.append(f"{var} must be a number")
    
    # Check for LLM API key
    llm_keys = ["OPENAI_API_KEY", "QWEN_API_KEY", "DEEPSEEK_API_KEY"]
    if not any(env_dict.get(key) for key in llm_keys):
        missing.append("LLM_API_KEY (at least one of: OPENAI_API_KEY, QWEN_API_KEY, DEEPSEEK_API_KEY)")
    
    return {
        "status": "success",
        "result": {
            "valid": len(missing) == 0 and len(incorrect) == 0,
            "missing": missing,
            "incorrect": incorrect,
            "mode": mode
        }
    }


@app.put("/env")
def put_env(items: List[EnvItem]) -> Dict[str, Any]:
    """
    Replaces/updates provided environment variables in .env and process env.
    """
    try:
        # Convert into the format save_env_vars expects: dict of key -> value
        to_save = {it.key: it.value for it in items if it.key}
        ok, msg = save_env_vars(to_save)
        if not ok:
            return {"status": "error", "detail": msg}
        return {"status": "success", "detail": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/env")
def add_env(items: List[EnvItem]) -> Dict[str, Any]:
    """
    Adds/updates variables one by one (immediate write).
    """
    try:
        for it in items:
            add_env_var(it.key, it.value, from_frontend=True)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/env/{key}")
def del_env(key: str) -> Dict[str, Any]:
    try:
        ok, msg = delete_env_var(key)
        if not ok:
            return {"status": "error", "detail": msg}
        return {"status": "success", "detail": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Exclude runtime-generated files from reload detection to prevent server restarts during job execution
    reload_excludes = [
        "**/cookies_data.py",
        "**/logs/**",
        "**/cache/**",
        "**/workplace/**",
        "**/casestudy_results/**",
        "**/paper_agent/**/cache_*/**",
        "**/*.log",
    ]
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=8080, 
        reload=False,  # Set to True for development, but exclude problematic files
        reload_excludes=reload_excludes if os.getenv("ENABLE_RELOAD", "false").lower() == "true" else []
    )
