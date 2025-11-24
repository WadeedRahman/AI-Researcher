import datetime
import threading
import uuid
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from queue import Queue
from typing import Any, Dict, Optional, Callable


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    id: str
    status: JobStatus
    created_at: str
    payload: Dict[str, Any]
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cancel_requested: bool = False
    last_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    log_file: Optional[str] = None  # Per-job log file path
    progress: Dict[str, Any] = field(default_factory=dict)  # Structured progress tracking
    token_usage: Dict[str, int] = field(default_factory=dict)  # Token usage tracking


class JobManager:
    def __init__(self, runner: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.runner = runner
        self.jobs: Dict[str, JobInfo] = {}
        self._queue: "Queue[str]" = Queue()
        self._lock = threading.RLock()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _create_job_log_file(self, job_id: str) -> str:
        """Create a per-job log file"""
        logs_dir = os.path.join(os.path.dirname(__file__), "logs", "jobs")
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, f"job_{job_id}.log")
        return log_file

    def submit(self, payload: Dict[str, Any]) -> JobInfo:
        with self._lock:
            job_id = str(uuid.uuid4())
            now = datetime.datetime.utcnow().isoformat() + "Z"
            log_file = self._create_job_log_file(job_id)
            job = JobInfo(
                id=job_id,
                status=JobStatus.PENDING,
                created_at=now,
                payload=payload,
                log_file=log_file,
                progress={
                    "current_agent": None,
                    "current_step": None,
                    "subtasks": [],
                    "estimated_time_remaining": None
                },
                token_usage={
                    "completion_tokens": 0,
                    "prompt_tokens": 0,
                    "total_tokens": 0
                }
            )
            self.jobs[job_id] = job
            self._queue.put(job_id)
            return job

    def get(self, job_id: str) -> Optional[JobInfo]:
        with self._lock:
            return self.jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False
            if job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
                return False
            job.cancel_requested = True
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.finished_at = datetime.datetime.utcnow().isoformat() + "Z"
            return True

    def list_jobs(self) -> Dict[str, JobInfo]:
        with self._lock:
            return dict(self.jobs)

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            with self._lock:
                job = self.jobs.get(job_id)
                if not job:
                    continue
                if job.cancel_requested and job.status == JobStatus.CANCELLED:
                    continue
                if job.status != JobStatus.PENDING:
                    continue
                job.status = JobStatus.RUNNING
                job.started_at = datetime.datetime.utcnow().isoformat() + "Z"

            try:
                if job.cancel_requested:
                    with self._lock:
                        job.status = JobStatus.CANCELLED
                        job.error = "Job cancelled before start"
                    continue
                
                # Set log path in global state before running the job
                if job.log_file:
                    import global_state
                    import os
                    # Ensure absolute path
                    if not os.path.isabs(job.log_file):
                        job.log_file = os.path.abspath(job.log_file)
                    global_state.LOG_PATH = job.log_file
                    # CRITICAL: Reset INIT_FLAG to False for each job to prevent blocking
                    global_state.INIT_FLAG = False
                    print(f"[DEBUG] Job {job_id}: Set LOG_PATH to {global_state.LOG_PATH}, INIT_FLAG={global_state.INIT_FLAG}")
                
                result = self.runner(job.payload)
                with self._lock:
                    if job.cancel_requested:
                        job.status = JobStatus.CANCELLED
                        job.error = "Job cancelled during execution"
                    else:
                        # Extract the result - it should be {"result": {"answer": ..., "token_count": ..., "status": ...}}
                        print(f"[DEBUG] Job {job_id}: Runner returned result type: {type(result)}, value: {str(result)[:500] if result else 'None'}")
                        job_result = result.get("result", {}) if isinstance(result, dict) else {}
                        print(f"[DEBUG] Job {job_id}: Extracted job_result type: {type(job_result)}, keys: {list(job_result.keys()) if isinstance(job_result, dict) else 'N/A'}")
                        
                        if isinstance(job_result, dict):
                            job.result = job_result
                            answer = job_result.get("answer", "")
                            print(f"[DEBUG] Job {job_id}: Answer type: {type(answer)}, length: {len(str(answer))}, preview: {str(answer)[:200]}")
                            
                            # Check if answer contains error messages and log warning
                            if answer and isinstance(answer, str):
                                if "already in progress" in answer.lower() or "Research job is already" in answer:
                                    print(f"[WARNING] Job {job_id}: Result contains 'already in progress' message! This should not happen.")
                                    print(f"[WARNING] Job {job_id}: Full answer: {answer}")
                        else:
                            # Fallback if structure is different
                            job.result = {"answer": str(job_result) if job_result else "No result returned", "token_count": "0", "status": "✅ Completed"}
                            print(f"[WARNING] Job {job_id}: Result structure unexpected, using fallback")
                        print(f"[DEBUG] Job {job_id}: Final job.result type: {type(job.result)}, answer length: {len(str(job.result.get('answer', ''))) if isinstance(job.result, dict) else 0}")
                        job.status = JobStatus.SUCCEEDED
                        
                        # Automatically trigger Paper Generation Agent after research jobs complete
                        # Only submit if job actually succeeded (not failed or cancelled)
                        if job.status == JobStatus.SUCCEEDED:
                            mode = job.payload.get("mode", "")
                            research_modes = [
                                "Detailed Idea Description", 
                                "Reference-Based Ideation",
                                "Idea Spark",
                                "Deep Survey",
                                "Auto Experiment"
                            ]
                            if mode in research_modes:
                            # Submit paper generation job automatically (in a separate thread to avoid blocking)
                            import threading
                            def submit_paper_job():
                                try:
                                    paper_payload = {
                                        "question": job.payload.get("question", ""),
                                        "reference": job.payload.get("reference", ""),
                                        "mode": "Paper Generation Agent"
                                    }
                                    paper_job = self.submit(paper_payload)
                                    # Link the paper job to the research job in metadata
                                    with self._lock:
                                        paper_job.metadata["parent_job_id"] = job.id
                                        job.metadata["paper_job_id"] = paper_job.id
                                except Exception as e:
                                    print(f"Error submitting paper generation job: {e}")
                            
                            # Submit in background thread to avoid blocking
                            threading.Thread(target=submit_paper_job, daemon=True).start()
            except Exception as e:
                with self._lock:
                    if job.status != JobStatus.CANCELLED:
                        job.error = str(e)
                        job.status = JobStatus.FAILED
            finally:
                with self._lock:
                    job.finished_at = datetime.datetime.utcnow().isoformat() + "Z"
            self._queue.task_done()


def build_default_runner(run_callable: Callable[[str, str, str], Any]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def _runner(payload: Dict[str, Any]) -> Dict[str, Any]:
        question = payload.get("question", "")
        reference = payload.get("reference", "") or ""
        mode = payload.get("mode", "")
        answer, token_count, status = run_callable(question, reference, mode)
        return {
            "result": {
                "answer": answer,
                "token_count": token_count,
                "status": status,
            }
        }

    return _runner


def job_to_dict(job: JobInfo) -> Dict[str, Any]:
    data = asdict(job)
    data["status"] = job.status.value
    return data



