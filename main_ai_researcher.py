import numpy as np
import argparse
import os
import sys
import asyncio
import contextlib
import threading
import global_state
from dotenv import load_dotenv
import json




def init_ai_researcher():
    a = 1

@contextlib.contextmanager
def change_directory(path):
    """Thread-safe context manager for changing directories."""
    original_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original_dir)

def get_args_research(argv=None): 
    """
    Get research arguments. 
    - When called from API (argv=[]), parses empty list to use defaults (env vars will override).
    - When called from CLI (argv=None), parses sys.argv normally.
    - When argv is explicitly provided, parses that list.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance_path", type=str, default="benchmark/gnn.json")
    parser.add_argument('--container_name', type=str, default='paper_eval')
    parser.add_argument("--task_level", type=str, default="task1")
    parser.add_argument("--model", type=str, default="gpt-4o-2024-08-06")
    parser.add_argument("--workplace_name", type=str, default="workplace")
    parser.add_argument("--cache_path", type=str, default="cache")
    parser.add_argument("--port", type=int, default=12345)
    parser.add_argument("--max_iter_times", type=int, default=0)
    parser.add_argument("--category", type=str, default="recommendation")
    parser.add_argument("--enable-code", action="store_true", dest="enable_code", help="Enable code implementation (default: paper writing only)")
    # Check if we're being called from uvicorn/FastAPI (common indicators)
    if argv is not None:
        # Explicit argv provided (e.g., from API with empty list)
        args = parser.parse_args(argv)
    elif len(sys.argv) > 1 and any(arg in sys.argv for arg in ['server:app', 'uvicorn', '--host', '--port']):
        # Detected uvicorn/FastAPI invocation - parse empty list to avoid conflicts
        args = parser.parse_args([])
    else:
        # Normal CLI invocation - parse sys.argv
        args = parser.parse_args()
    return args

def get_args_paper(argv=None):
    """
    Get paper generation arguments.
    - When called from API (argv=[]), parses empty list to use defaults (env vars will override).
    - When called from CLI (argv=None), parses sys.argv normally.
    - When argv is explicitly provided, parses that list.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--research_field", type=str, default="vq")
    parser.add_argument("--instance_id", type=str, default="rotation_vq")
    # Check if we're being called from uvicorn/FastAPI (common indicators)
    if argv is not None:
        # Explicit argv provided (e.g., from API with empty list)
        args = parser.parse_args(argv)
    elif len(sys.argv) > 1 and any(arg in sys.argv for arg in ['server:app', 'uvicorn', '--host', '--port']):
        # Detected uvicorn/FastAPI invocation - parse empty list to avoid conflicts
        args = parser.parse_args([])
    else:
        # Normal CLI invocation - parse sys.argv
        args = parser.parse_args()
    return args

def main_ai_researcher(input, reference, mode):
    # if main_autoagent.mode is None:
    #     main_autoagent.mode = mode
        
    # if main_autoagent.mode != mode:
    #     model = COMPLETION_MODEL
    #     main_autoagent.mode = mode
    #     global_state.INIT_FLAG = False
    
    # Debug logging
    print(f"[DEBUG] main_ai_researcher called with mode={mode}, INIT_FLAG={global_state.INIT_FLAG}")
    
    load_dotenv()
    category = os.getenv("CATEGORY") or "recommendation"
    instance_id = os.getenv("INSTANCE_ID") or "default_instance"
    task_level = os.getenv("TASK_LEVEL") or "task1"
    container_name = os.getenv("CONTAINER_NAME") or "paper_eval"
    workplace_name = os.getenv("WORKPLACE_NAME") or "workplace"
    cache_path = os.getenv("CACHE_PATH") or "cache"
    port = int(os.getenv("PORT") or "12345")
    max_iter_times = int(os.getenv("MAX_ITER_TIMES") or "0")

    
    match mode:
        case 'Idea Spark' | 'Deep Survey' | 'Auto Experiment':
            # All three modes use the same routing logic:
            # - If no reference file: use idea generation agent (run_infer_idea)
            # - If reference file attached: use reference-based agent (run_infer_plan)
            # Note: Removed INIT_FLAG check - each API request should be independent
            # Use thread-safe directory change context manager
            result = None
            current_file_path = os.path.realpath(__file__)
            current_dir = os.path.dirname(current_file_path)
            sub_dir = os.path.join(current_dir, "research_agent")
            
            with change_directory(sub_dir):

                from research_agent.constant import COMPLETION_MODEL
                from research_agent import run_infer_idea, run_infer_plan

                args = get_args_research()
                args.instance_path = f"../benchmark/final/{category}/{instance_id}.json"
                args.task_level = task_level
                args.model = COMPLETION_MODEL
                args.container_name = container_name
                args.workplace_name = workplace_name
                args.cache_path = cache_path
                args.port = port
                args.max_iter_times = max_iter_times
                args.category = category

                # Route based on whether reference file is attached
                if reference and reference.strip():
                    # Reference file attached: use reference-based agent
                    try:
                        research_result = run_infer_plan.main(args, input, reference, mode)
                        print(f"[DEBUG] main_ai_researcher: run_infer_plan returned: {type(research_result)}")
                        # Format the result for display
                        if research_result and isinstance(research_result, dict):
                            result = f"""# Research Results (Mode: {mode})

## Final Result
{research_result.get('final_result', 'N/A')}

## Survey Results
{research_result.get('survey_result', 'N/A')}

## Implementation Plan
{research_result.get('plan', 'N/A')}
"""
                        else:
                            result = f"Research completed successfully using reference-based agent (mode: {mode}). Results have been generated and saved. Returned type: {type(research_result)}"
                    except Exception as e:
                        print(f"[ERROR] run_infer_plan.main failed: {e}")
                        import traceback
                        traceback.print_exc()
                        result = f"Error in research process: {str(e)}"
                else:
                    # No reference file: use idea generation agent
                    # Pass the input as custom_task (user's question), not as references
                    try:
                        # Clean the input to remove @ mentions if present
                        import re
                        clean_input = re.sub(r'@\w+\s*', '', input if input else "").strip()
                        print(f"[DEBUG] main_ai_researcher: Calling run_infer_idea.main with input='{clean_input[:50] if clean_input else 'empty'}...', mode='{mode}'")
                        research_result = run_infer_idea.main(args, references="", mode=mode, custom_task=clean_input)
                        print(f"[DEBUG] main_ai_researcher: run_infer_idea returned: {type(research_result)}, is_none={research_result is None}, value: {str(research_result)[:200] if research_result else 'None'}...")
                        
                        # Format the result for display
                        if research_result is None:
                            print("[ERROR] main_ai_researcher: research_result is None - this should not happen!")
                            result = f"Research process encountered an issue: the idea generation agent did not return any results. Please check the logs for more information. Mode: {mode}, Input: {clean_input[:100] if clean_input else 'empty'}"
                        elif isinstance(research_result, dict):
                            # Extract meaningful content from the dict
                            final_result = research_result.get('final_result', 'N/A')
                            selected_idea = research_result.get('selected_idea', 'N/A')
                            code_survey = research_result.get('code_survey', 'N/A')
                            plan = research_result.get('plan', 'N/A')
                            
                            # Build result string with better formatting and filtering
                            result_parts = [f"# Research Results (Mode: {mode})"]
                            
                            # Helper function to clean text (NO TRUNCATION - show full content)
                            def clean_text(text):
                                if not text or text == 'N/A':
                                    return None
                                # Remove any ML/code skip messages - not relevant for research-only mode
                                skip_patterns = [
                                    "skipped per configuration",
                                    "ML refinement skipped",
                                    "ML agent execution skipped",
                                    "ML implementation skipped",
                                    "ML experiments skipped"
                                ]
                                if any(pattern in text.lower() for pattern in skip_patterns):
                                    return None
                                # Return full text - no truncation
                                return text
                            
                            # Helper to remove duplicate headers in code survey
                            def clean_code_survey(text):
                                if not text:
                                    return None
                                # Remove duplicate "Code Survey Report" headers
                                if text.count("Code Survey Report") > 1:
                                    parts = text.split("Code Survey Report")
                                    # Keep only the last occurrence
                                    return "Code Survey Report" + parts[-1] if len(parts) > 1 else text
                                return text
                            
                            # Helper to format plan (handle dict/JSON)
                            def format_plan(plan_text):
                                if not plan_text or plan_text == 'N/A':
                                    return None
                                # Try to parse as JSON and format nicely
                                if isinstance(plan_text, str) and plan_text.strip().startswith('{'):
                                    try:
                                        plan_dict = json.loads(plan_text)
                                        formatted = []
                                        for key, value in plan_dict.items():
                                            key_display = key.replace('_', ' ').title()
                                            if isinstance(value, dict):
                                                formatted.append(f"\n### {key_display}\n")
                                                for sub_key, sub_value in value.items():
                                                    sub_key_display = sub_key.replace('_', ' ').title()
                                                    formatted.append(f"**{sub_key_display}**: {sub_value}\n")
                                            elif isinstance(value, list):
                                                formatted.append(f"\n### {key_display}\n")
                                                for item in value:
                                                    formatted.append(f"- {item}\n")
                                            else:
                                                formatted.append(f"**{key_display}**: {value}\n")
                                        return "".join(formatted)
                                    except:
                                        pass  # Keep as-is if not valid JSON
                                return plan_text
                            
                            if selected_idea and selected_idea != 'N/A':
                                cleaned = clean_text(selected_idea)
                                if cleaned:
                                    result_parts.append(f"\n## Selected Idea\n{cleaned}")
                            
                            if final_result and final_result != 'N/A':
                                cleaned = clean_text(final_result)
                                if cleaned:
                                    result_parts.append(f"\n## Final Result\n{cleaned}")
                            
                            if code_survey and code_survey != 'N/A':
                                cleaned_survey = clean_code_survey(code_survey)
                                cleaned = clean_text(cleaned_survey) if cleaned_survey else None
                                if cleaned:
                                    result_parts.append(f"\n## Code Survey\n{cleaned}")
                            
                            if plan and plan != 'N/A':
                                formatted_plan = format_plan(plan)
                                cleaned = clean_text(formatted_plan) if formatted_plan else None
                                if cleaned:
                                    result_parts.append(f"\n## Implementation Plan\n{cleaned}")
                            
                            result = "\n".join(result_parts) if len(result_parts) > 1 else f"Research completed successfully using idea generation agent (mode: {mode}). Results have been generated and saved."
                        else:
                            # If it's not a dict, convert to string
                            result = str(research_result) if research_result else f"Research completed successfully using idea generation agent (mode: {mode}). Results have been generated and saved."
                    except Exception as e:
                        print(f"[ERROR] run_infer_idea.main failed: {e}")
                        import traceback
                        traceback.print_exc()
                        result = f"Error in research process: {str(e)}"
            
            # Ensure we always return a result
            if result is None:
                result = f"Research process completed but no results were returned. Please check the logs for more information. Mode: {mode}"
            
            return result
        case 'Detailed Idea Description':
            # Note: INIT_FLAG check removed - JobManager handles concurrency
            # Each job runs independently through the job queue
            result = None
            current_file_path = os.path.realpath(__file__)
            current_dir = os.path.dirname(current_file_path)
            sub_dir = os.path.join(current_dir, "research_agent")
            
            with change_directory(sub_dir):

                from research_agent.constant import COMPLETION_MODEL
                from research_agent import run_infer_idea, run_infer_plan

                args = get_args_research()
                # category="vq"
                # instance_id="rotation_vq"
                args.instance_path = f"../benchmark/final/{category}/{instance_id}.json"
                args.task_level = task_level
                args.model = COMPLETION_MODEL
                args.container_name = container_name
                args.workplace_name = workplace_name
                args.cache_path = cache_path
                args.port = port
                args.max_iter_times = max_iter_times
                args.category = category

                research_result = run_infer_plan.main(args, input, reference)
                
                # Format the result for display
                if research_result and isinstance(research_result, dict):
                    result = f"""# Research Results (Mode: Detailed Idea Description)

## Final Result
{research_result.get('final_result', 'N/A')}

## Survey Results
{research_result.get('survey_result', 'N/A')}

## Implementation Plan
{research_result.get('plan', 'N/A')}
"""
                else:
                    result = f"Research completed successfully using Detailed Idea Description mode. Results have been generated and saved."
            
            if result is None:
                result = f"Research process completed but no results were returned. Please check the logs for more information."
            
            return result
        case 'Reference-Based Ideation':
            # Note: INIT_FLAG check removed - JobManager handles concurrency
            # Each job runs independently through the job queue
            result = None
            current_file_path = os.path.realpath(__file__)
            current_dir = os.path.dirname(current_file_path)
            sub_dir = os.path.join(current_dir, "research_agent")
            
            with change_directory(sub_dir):

                from research_agent.constant import COMPLETION_MODEL
                from research_agent import run_infer_idea, run_infer_plan
                from research_agent.constant import COMPLETION_MODEL
                args = get_args_research()
                # category="vq"
                # instance_id="one_layer_vq"
                # args.instance_path = f"../benchmark/final/{category}/{instance_id}.json"
                # args.container_name = "paper_eval"
                # args.task_level = "task1"
                # args.model = COMPLETION_MODEL
                # args.workplace_name = "workplace"
                # args.cache_path = "cache"
                # args.port = 12356
                # args.max_iter_times = 0


                args.instance_path = f"../benchmark/final/{category}/{instance_id}.json"
                args.container_name = container_name
                args.task_level = task_level
                args.model = COMPLETION_MODEL
                args.workplace_name = workplace_name
                args.cache_path = cache_path
                args.port = port
                args.max_iter_times = max_iter_times
                args.category = category

                research_result = run_infer_idea.main(args, reference)
                
                # Format the result for display
                if research_result and isinstance(research_result, dict):
                    final_result = research_result.get('final_result', 'N/A')
                    selected_idea = research_result.get('selected_idea', 'N/A')
                    code_survey = research_result.get('code_survey', 'N/A')
                    plan = research_result.get('plan', 'N/A')
                    
                    # Build result string
                    result_parts = [f"# Research Results (Mode: Reference-Based Ideation)"]
                    
                    if selected_idea and selected_idea != 'N/A':
                        result_parts.append(f"\n## Selected Idea\n{selected_idea}")
                    
                    if final_result and final_result != 'N/A':
                        result_parts.append(f"\n## Final Refined Result\n{final_result}")
                    
                    if code_survey and code_survey != 'N/A':
                        result_parts.append(f"\n## Code Survey\n{code_survey}")
                    
                    if plan and plan != 'N/A':
                        result_parts.append(f"\n## Implementation Plan\n{plan}")
                    
                    result = "\n".join(result_parts) if len(result_parts) > 1 else f"Research completed successfully using Reference-Based Ideation mode. Results have been generated and saved."
                else:
                    result = f"Research completed successfully using Reference-Based Ideation mode. Results have been generated and saved."
            
            if result is None:
                result = f"Research process completed but no results were returned. Please check the logs for more information."
            
            return result
        case 'Paper Generation Agent':
            # clear_screen()
            result = None
            # Note: INIT_FLAG check removed - JobManager handles concurrency
            # Each job runs independently through the job queue
            try:
                from paper_agent import writing
                args = get_args_paper()

                research_field=category
                # instance_id="rotated_vq"
                args.research_field = research_field
                args.instance_id = instance_id

                # Validate that the required directory structure exists
                proj_dir = f'./paper_agent/{research_field}/{instance_id}/'
                if not os.path.exists(proj_dir):
                    error_msg = (
                        f"Paper Generation Agent requires a completed research job.\n"
                        f"Expected directory not found: {proj_dir}\n\n"
                        f"Please run one of the following agents first:\n"
                        f"  - 'Idea Spark'\n"
                        f"  - 'Deep Survey'\n"
                        f"  - 'Auto Experiment'\n"
                        f"  - 'Detailed Idea Description'\n"
                        f"  - 'Reference-Based Ideation'\n\n"
                        f"These agents will create the necessary directory structure at:\n"
                        f"  {proj_dir}\n\n"
                        f"Current environment variables:\n"
                        f"  CATEGORY={category}\n"
                        f"  INSTANCE_ID={instance_id}"
                    )
                    raise FileNotFoundError(error_msg)
                
                # Check for cache directories
                try:
                    cache_dirs = [d for d in os.listdir(proj_dir) if d.startswith('cache_')]
                    if not cache_dirs:
                        error_msg = (
                            f"Paper Generation Agent requires completed research results.\n"
                            f"Directory exists but no cache directories found in: {proj_dir}\n\n"
                            f"Please ensure a research job has completed successfully.\n"
                            f"The research job should create cache directories containing agent outputs."
                        )
                        raise ValueError(error_msg)
                except PermissionError:
                    error_msg = (
                        f"Permission denied accessing directory: {proj_dir}\n"
                        f"Please check file permissions."
                    )
                    raise PermissionError(error_msg)

                asyncio.run(writing.writing(args.research_field, args.instance_id))
                result = f"Paper generation completed successfully for {research_field}/{instance_id}. Paper has been generated and saved."
            except Exception as e:
                # Re-raise exceptions so they're properly handled by JobManager
                raise
            
            # Ensure we always return a result
            if result is None:
                result = f"Paper generation process completed but no result was returned. Please check the logs for more information."
            
            return result
