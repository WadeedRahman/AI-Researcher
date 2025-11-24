# Deep Survey Request Flow - Detailed Analysis

## Overview
This document explains the complete step-by-step process when a "Deep Survey" request is received from the frontend, and identifies potential bugs and issues.

---

## Step-by-Step Process Flow

### Phase 1: Frontend Request Handling

#### Step 1.1: User Input Processing (`frontend/src/views/Home.vue`)
- **Location**: `handleSendMessage()` function (line 252)
- **Process**:
  1. User types message or selects "Deep Survey" from quick-select
  2. Frontend checks for:
     - Pre-selected agent (`selectedAgent.value`)
     - @ mentions (e.g., `@deepsurvey`, `@survey`, `@deep`)
     - Attached files (auto-selects Deep Survey if files present)
     - Reference keywords in message
     - Survey-related keywords (`survey`, `review`, `analyze`, `research`, `literature`, `comprehensive`)
  3. If any of the above match, mode is set to `'Deep Survey'`
  4. Reference text is extracted from:
     - Attached files (read as text)
     - Explicit "reference:" or "references:" prefix
     - ArXiv IDs or citation patterns
  5. Payload is constructed:
     ```typescript
     {
       question: userMessage,
       reference: reference || undefined,
       mode: 'Deep Survey'
     }
     ```

#### Step 1.2: Job Submission (`frontend/src/views/Home.vue`)
- **Location**: Line 365
- **Process**:
  1. Calls `jobStore.submitJob(payload)`
  2. This sends POST request to `/jobs` endpoint
  3. Returns `job_id` for polling

**🐛 Potential Bug #1**: If `reference` is an empty string, it's converted to `undefined`, but the backend might expect an empty string. This inconsistency could cause issues.

---

### Phase 2: Backend API Handling

#### Step 2.1: Job Submission Endpoint (`server.py`)
- **Location**: `submit_job()` function (line 268)
- **Process**:
  1. Receives `RunRequest` with `question`, `reference`, and `mode`
  2. Creates a job via `_job_manager.submit(req.dict())`
  3. Sets up per-job logging
  4. Returns `{"status": "queued", "job_id": job.id}`

#### Step 2.2: Job Manager Processing (`job_manager.py`)
- **Location**: `_worker_loop()` method (line 101)
- **Process**:
  1. Worker thread picks up job from queue
  2. Sets job status to `RUNNING`
  3. Sets `global_state.LOG_PATH` to per-job log file
  4. **CRITICAL**: Resets `global_state.INIT_FLAG = False` (line 131)
  5. Calls `self.runner(job.payload)` which executes `run_ai_researcher()`

**🐛 Potential Bug #2**: The `INIT_FLAG` reset happens, but there's no guarantee that previous job's state is fully cleaned up. If a job fails mid-execution, some global state might persist.

---

### Phase 3: Research Execution

#### Step 3.1: Entry Point (`web_ai_researcher.py`)
- **Location**: `run_ai_researcher()` function (line 518)
- **Process**:
  1. Validates input question
  2. Checks if mode is in `MODULE_DESCRIPTIONS`
  3. Calls `main_ai_researcher(question, reference, mode)`
  4. Handles None/empty results with fallback messages
  5. Returns tuple: `(answer, token_count, status)`

**🐛 Potential Bug #3**: Token tracking is hardcoded to `None` (line 568), so token counts are always 0. This is a known issue but not critical.

#### Step 3.2: Main Router (`main_ai_researcher.py`)
- **Location**: `main_ai_researcher()` function (line 66)
- **Process**:
  1. Loads environment variables:
     - `CATEGORY` (default: "recommendation")
     - `INSTANCE_ID` (default: "default_instance")
     - `TASK_LEVEL`, `CONTAINER_NAME`, `WORKPLACE_NAME`, `CACHE_PATH`, `PORT`, `MAX_ITER_TIMES`
  2. Matches mode to `'Idea Spark' | 'Deep Survey' | 'Auto Experiment'`
  3. **Routing Logic**:
     - **If `reference` exists and is not empty**: Calls `run_infer_plan.main()` (reference-based agent)
     - **If `reference` is empty/None**: Calls `run_infer_idea.main()` (idea generation agent)
  4. Changes working directory to `research_agent/` subdirectory
  5. Constructs `args` object with all configuration
  6. Executes appropriate agent flow
  7. Formats result for display
  8. Restores original directory

**🐛 Potential Bug #4**: The directory change (line 102) uses `os.chdir()` which is not thread-safe. If multiple jobs run concurrently, they could interfere with each other's working directories. This is a **CRITICAL BUG**.

**🐛 Potential Bug #5**: If `run_infer_plan.main()` or `run_infer_idea.main()` raises an exception, the directory might not be restored if the exception occurs after the try block but before the finally block. However, the finally block should handle this.

**🐛 Potential Bug #6**: The input cleaning (line 150) removes @ mentions, but this happens AFTER the mode has already been determined. If the user types `@deepsurvey some question`, the mode is correctly set, but the question becomes `some question` - this is actually correct behavior, but worth noting.

---

### Phase 4: Agent Flow Execution

#### Scenario A: With References (uses `run_infer_plan`)

##### Step 4A.1: Initialization (`research_agent/run_infer_plan.py`)
- **Location**: `InnoFlow.__init__()` (line 101)
- **Agents Initialized**:
  - `load_ins`: Loads benchmark instance
  - `git_search`: Searches GitHub for papers
  - `prepare_agent`: Prepares reference codebases
  - `download_papaer`: Downloads paper sources
  - `coding_plan_agent`: Creates implementation plan
  - `ml_agent`: Implements ML model
  - `judge_agent`: Evaluates implementation
  - `survey_agent`: Conducts comprehensive survey

##### Step 4A.2: Forward Pass (`InnoFlow.forward()`)
- **Location**: Line 113
- **Process**:
  1. **Load Instance** (line 114):
     - Loads benchmark metadata from `instance_path`
     - Extracts `date_limit` for paper filtering
     - Sets `working_dir` in context variables
  2. **GitHub Search** (line 120):
     - Searches GitHub for relevant repositories
     - Returns search results
  3. **Prepare Agent** (line 137):
     - Receives: papers list, GitHub results, innovative ideas
     - Task: Select at least 5 repositories as reference codebases
     - Output: JSON with selected repositories and papers
  4. **Download Papers** (line 141):
     - Downloads selected papers in LaTeX format
     - Saves to local filesystem
  5. **Survey Agent** (line 168):
     - **Mode-specific instructions added** (line 146-147):
       ```
       MODE: Deep Survey - Conduct thorough and comprehensive analysis. 
       Be exhaustive in reviewing papers and creating detailed implementation plans.
       ```
     - Task: Comprehensive survey on ideas and papers
     - Output: Detailed survey with math formulas and implementation notes
  6. **Dataset Selection** (line 172):
     - Loads dataset metadata from `benchmark.process.dataset_candidate.{category}.metaprompt`
     - Includes: DATASET, BASELINE, COMPARISON, EVALUATION, REF
  7. **Coding Plan Agent** (line 207):
     - Task: Create detailed implementation plan
     - Uses: ideas, references, survey results, dataset info
  8. **ML Agent** (line 328):
     - Task: Implement the model
     - Requirements:
       - Complete implementation (no placeholders)
       - Use actual dataset (not toy data)
       - Train for 2 epochs
       - Test on GPU
       - Follow project structure requirements
  9. **Judge Agent** (line 356):
     - Task: Evaluate implementation
     - Checks: Meets idea requirements, follows plan, has test process
  10. **Iterative Refinement Loop** (line 371):
      - **Mode-specific iteration count** (line 363-365):
        ```python
        if mode == "Deep Survey":
            adjusted_max_iter = max_iter_times + 1 if max_iter_times > 0 else 1
        ```
      - For each iteration:
        - ML Agent modifies implementation based on judge feedback
        - Judge Agent re-evaluates
        - Continues until `"fully_correct": true` or max iterations reached

**🐛 Potential Bug #7**: The iteration count for Deep Survey adds 1 to `max_iter_times`, but if `max_iter_times` is 0 (default), it becomes 1. However, if `max_iter_times` is explicitly set to 0, this might cause unexpected behavior. The logic should be clearer.

**🐛 Potential Bug #8**: The judge agent checks for `"fully_correct": true` in the content string (line 423), but this is a fragile string match. If the agent returns JSON in a different format or with different whitespace, the check might fail.

#### Scenario B: Without References (uses `run_infer_idea`)

##### Step 4B.1: Initialization (`research_agent/run_infer_idea.py`)
- **Location**: `InnoFlow.__init__()` (line 100)
- **Agents Initialized**:
  - Similar to `run_infer_plan` but uses `idea_agent` instead of `survey_agent`
  - Also includes `code_survey_agent` and `exp_analyser`

##### Step 4B.2: Forward Pass (`InnoFlow.forward()`)
- **Location**: Line 114
- **Process**:
  1. **Load Instance & GitHub Search** (same as Scenario A)
  2. **Prepare Agent** (line 202):
     - If references provided: Selects repositories from provided papers
     - If no references: Searches based on task description
  3. **Download Papers** (line 207)
  4. **Idea Agent** (line 242):
     - **Mode-specific instructions** (line 215-216):
       ```
       MODE: Deep Survey - Conduct thorough and comprehensive literature review. 
       Be exhaustive in analyzing papers, identifying gaps, and generating well-researched ideas.
       ```
     - **Mode-specific idea count** (line 248-249):
       ```python
       if mode == "Deep Survey":
           IDEA_NUM = 7  # More comprehensive, more ideas for thorough research
       ```
     - Generates multiple innovative ideas (7 for Deep Survey)
     - Iteratively asks for more ideas until `IDEA_NUM` is reached
  5. **Idea Selection** (line 265):
     - Analyzes all generated ideas
     - Selects most novel one
     - Refines with complete math formulas
  6. **Code Survey Agent** (line 282):
     - Reviews codebases thoroughly
     - Generates comprehensive implementation report
     - Must review ALL academic concepts
  7. **Coding Plan Agent** (line 308):
     - Creates detailed implementation plan
  8. **ML Agent & Judge Agent Loop** (similar to Scenario A)
     - Iterative refinement based on mode-specific iteration count

**🐛 Potential Bug #9**: The idea generation loop (line 252) extends `messages` with `survey_messages` on each iteration, which could cause the message history to grow very large. For Deep Survey with 7 ideas, this could lead to context window issues.

**🐛 Potential Bug #10**: The code survey agent is instructed to "NOT stop to review the codebases until you have get all academic concepts" (line 277), but there's no timeout or maximum iteration limit. This could cause the agent to run indefinitely if it can't find all concepts.

---

### Phase 5: Result Processing

#### Step 5.1: Result Formatting (`main_ai_researcher.py`)
- **Location**: Lines 125-138 (with references) or 156-184 (without references)
- **Process**:
  1. Checks if result is dict or other type
  2. Extracts relevant fields:
     - `final_result`, `survey_result`, `plan` (with references)
     - `selected_idea`, `final_result`, `code_survey`, `plan` (without references)
  3. Formats as markdown string
  4. Returns formatted result

**🐛 Potential Bug #11**: If the result dict doesn't contain expected keys, it falls back to generic messages. However, the fallback might not be informative enough for debugging.

#### Step 5.2: Job Completion (`job_manager.py`)
- **Location**: `_worker_loop()` method (line 134)
- **Process**:
  1. Extracts result from runner return value
  2. Sets job status to `SUCCEEDED`
  3. **Auto-submits Paper Generation Job** (line 172-190):
     - If mode is a research mode, automatically submits paper generation job
     - This happens in a background thread to avoid blocking

**🐛 Potential Bug #12**: The automatic paper generation job submission happens even if the research job failed or returned an error. There should be a check to ensure the research job actually succeeded before submitting the paper job.

**🐛 Potential Bug #13**: The paper generation job is submitted with the same `question` and `reference` from the research job, but paper generation might need different inputs. This could cause issues.

---

### Phase 6: Frontend Result Display

#### Step 6.1: Polling for Results (`frontend/src/views/Home.vue`)
- **Location**: `pollJobStatus()` function (line 391)
- **Process**:
  1. Polls `/jobs/{job_id}` every 3 seconds
  2. Fetches logs from `/jobs/{job_id}/logs`
  3. Updates message display with latest content
  4. When job completes:
     - Extracts result from `job.result.answer`
     - Falls back to logs if result is insufficient
     - Displays final content

**🐛 Potential Bug #14**: The polling interval is fixed at 3 seconds, which might be too frequent for long-running jobs. This could cause unnecessary server load.

**🐛 Potential Bug #15**: The result extraction logic (lines 519-608) is very complex with many fallbacks. If the result structure changes, this could break silently.

---

## Critical Bugs Summary

### 🔴 High Priority

1. **Thread Safety Issue with `os.chdir()`** (Bug #4)
   - **Location**: `main_ai_researcher.py` line 102
   - **Impact**: Multiple concurrent jobs can interfere with each other's working directories
   - **Fix**: Use context managers or thread-local storage for working directories

2. **Automatic Paper Generation on Failed Jobs** (Bug #12)
   - **Location**: `job_manager.py` line 171
   - **Impact**: Paper generation jobs are submitted even when research fails
   - **Fix**: Check job status before submitting paper job

3. **Unbounded Message History Growth** (Bug #9)
   - **Location**: `run_infer_idea.py` line 252
   - **Impact**: Context window overflow for Deep Survey with 7 ideas
   - **Fix**: Limit message history or use summarization

### 🟡 Medium Priority

4. **Fragile String Matching for Completion** (Bug #8)
   - **Location**: `run_infer_plan.py` line 423
   - **Impact**: Judge agent completion check might fail
   - **Fix**: Use proper JSON parsing

5. **No Timeout for Code Survey Agent** (Bug #10)
   - **Location**: `run_infer_idea.py` line 277
   - **Impact**: Agent might run indefinitely
   - **Fix**: Add iteration limits or timeouts

6. **Inconsistent Reference Handling** (Bug #1)
   - **Location**: Frontend and backend
   - **Impact**: Empty string vs undefined inconsistency
   - **Fix**: Standardize on one approach

### 🟢 Low Priority

7. **Token Tracking Not Implemented** (Bug #3)
   - **Location**: `web_ai_researcher.py` line 568
   - **Impact**: Token counts always show 0
   - **Fix**: Implement proper token tracking

8. **Complex Result Extraction Logic** (Bug #15)
   - **Location**: `frontend/src/views/Home.vue` lines 519-608
   - **Impact**: Hard to maintain, might break silently
   - **Fix**: Simplify and add better error handling

---

## Recommendations

1. **Implement Thread-Safe Directory Management**: Use context managers or thread-local storage
2. **Add Proper Error Handling**: Check job status before dependent operations
3. **Implement Message History Management**: Summarize or truncate long histories
4. **Add Timeouts and Limits**: Prevent infinite loops in agent execution
5. **Standardize Data Formats**: Use consistent types for references, results, etc.
6. **Add Comprehensive Logging**: Better debugging for complex flows
7. **Implement Token Tracking**: Proper usage monitoring

---

## Mode-Specific Differences for Deep Survey

1. **More Ideas Generated**: 7 ideas instead of 3 (Idea Spark) or 5 (Auto Experiment)
2. **More Iterations**: `max_iter_times + 1` instead of `max_iter_times - 1` (Idea Spark)
3. **Comprehensive Instructions**: Emphasizes thoroughness and exhaustiveness
4. **Longer Execution Time**: Due to more ideas and iterations

---

## Conclusion

The Deep Survey flow is complex but generally well-structured. The main issues are related to:
- Thread safety
- Error handling
- Resource management (message history, timeouts)
- Data consistency

Most bugs are fixable with proper error handling and resource management improvements.

