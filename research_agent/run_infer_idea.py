import json
from research_agent.inno.workflow.flowcache import FlowModule, ToolModule, AgentModule
from research_agent.inno.tools.inno_tools.paper_search import get_arxiv_paper_meta
from research_agent.inno.tools.inno_tools.code_search import search_github_repos, search_github_code
from research_agent.inno.agents.inno_agent.plan_agent import get_coding_plan_agent
from research_agent.inno.agents.inno_agent.prepare_agent import get_prepare_agent
from research_agent.inno.agents.inno_agent.ml_agent import get_ml_agent
from research_agent.inno.agents.inno_agent.judge_agent import get_judge_agent
from research_agent.inno.agents.inno_agent.survey_agent import get_survey_agent
from research_agent.inno.agents.inno_agent.exp_analyser import get_exp_analyser_agent
from research_agent.inno.agents.inno_agent.idea_agent import get_idea_agent, get_code_survey_agent
from research_agent.inno.tools.arxiv_source import download_arxiv_source_by_title
from research_agent.inno import MetaChain
from tqdm import tqdm
from pydantic import BaseModel, Field
from research_agent.constant import DOCKER_WORKPLACE_NAME, COMPLETION_MODEL, CHEEP_MODEL
from research_agent.inno.util import single_select_menu
from research_agent.inno.environment.docker_env import DockerEnv, DockerConfig
from research_agent.inno.environment.browser_env import BrowserEnv
from research_agent.inno.environment.markdown_browser import RequestsMarkdownBrowser
import asyncio
import argparse
import os
from typing import List, Dict, Any, Union
from research_agent.inno.logger import MetaChainLogger
import importlib
from research_agent.inno.environment.utils import setup_dataset
# instance_path = "benchmark/gnn.json"
# task_level = "task1"
def warp_source_papers(source_papers):
    return "\n".join([f"Title: {source_paper['reference']}; You can use this paper in the following way: {source_paper['usage']}" for source_paper in source_papers])
def extract_json_from_output(output_text: str) -> dict:
    # 计数器方法来找到完整的JSON
    def find_json_boundaries(text):
        stack = []
        start = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if not stack:  # 第一个开括号
                    start = i
                stack.append(char)
            elif char == '}':
                stack.pop()
                if not stack and start != -1:  # 找到匹配的最外层括号
                    return text[start:i+1]
        
        return None

    # 找到JSON文本
    json_str = find_json_boundaries(output_text)
    
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return {}
    return {}
def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance_path", type=str, default="benchmark/gnn.json")
    parser.add_argument('--container_name', type=str, default='paper_eval')
    parser.add_argument("--task_level", type=str, default="task1")
    parser.add_argument("--model", type=str, default="gpt-4o-2024-08-06")
    parser.add_argument("--workplace_name", type=str, default="workplace")
    parser.add_argument("--cache_path", type=str, default="cache")
    parser.add_argument("--port", type=int, default=12345)
    parser.add_argument("--max_iter_times", type=int, default=0)
    parser.add_argument("--skip_ml", action="store_true", help="Skip ML agent execution to save tokens")
    parser.add_argument("--enable-code", action="store_true", help="Enable code implementation (default: paper writing only)")
    parser.add_argument("--category", type=str, default="recommendation")
    args = parser.parse_args()
    return args

class EvalMetadata(BaseModel):
    source_papers: List[dict] = Field(description="the list of source papers")
    task_instructions: str = Field(description="the task instructions")
    date: str = Field(description="the date", pattern="^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD format
    date_limit: str = Field(description="the date limit", pattern="^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD format
def load_instance(instance_path, task_level) -> Dict:
    with open(instance_path, "r", encoding="utf-8") as f:
        eval_instance = json.load(f)
    source_papers = eval_instance["source_papers"]  
    task_instructions = eval_instance[task_level]   
    arxiv_url = eval_instance["url"]
    meta = get_arxiv_paper_meta(arxiv_url)
    if meta is None:
        date = "2024-01-01"
    else:
        date = meta["published"].strftime("%Y-%m-%d")

    return EvalMetadata(source_papers=source_papers, task_instructions=task_instructions, date=date, date_limit=date).model_dump()

def github_search(metadata: Dict) -> str:
    github_result = ""
    for source_paper in tqdm(metadata["source_papers"]):
        github_result += search_github_repos(metadata, source_paper["reference"], 10)
        github_result += "*"*30 + "\n"
    return github_result

class InnoFlow(FlowModule):
    def __init__(self, cache_path: str, log_path: Union[str, None, MetaChainLogger] = None, model: str = "gpt-4o-2024-08-06", code_env: DockerEnv = None, web_env: BrowserEnv = None, file_env: RequestsMarkdownBrowser = None):
        super().__init__(cache_path, log_path, model)
        self.load_ins = ToolModule(load_instance, cache_path)
        self.git_search = ToolModule(github_search, cache_path)
        self.prepare_agent = AgentModule(get_prepare_agent(model=CHEEP_MODEL, code_env=code_env), self.client, cache_path)
        self.download_papaer = ToolModule(download_arxiv_source_by_title, cache_path)
        self.coding_plan_agent = AgentModule(get_coding_plan_agent(model=CHEEP_MODEL, code_env=code_env), self.client, cache_path)
        self.ml_agent = AgentModule(get_ml_agent(model=COMPLETION_MODEL, code_env=code_env), self.client, cache_path)
        self.judge_agent = AgentModule(get_judge_agent(model=CHEEP_MODEL, code_env=code_env, web_env=web_env, file_env=file_env), self.client, cache_path)
        self.idea_agent = AgentModule(get_idea_agent(model=CHEEP_MODEL, file_env=file_env, code_env=code_env), self.client, cache_path)
        # self.survey_agent = AgentModule(get_survey_agent(model=CHEEP_MODEL, file_env=file_env, code_env=code_env), self.client, cache_path)
        self.code_survey_agent = AgentModule(get_code_survey_agent(model=CHEEP_MODEL, file_env=file_env, code_env=code_env), self.client, cache_path)
        self.exp_analyser = AgentModule(get_exp_analyser_agent(model=CHEEP_MODEL, file_env=file_env, code_env=code_env), self.client, cache_path)
    async def forward(self, instance_path: str, task_level: str, local_root: str, workplace_name: str, max_iter_times: int, category: str, references: str, mode: str = "Idea Spark", custom_task: str = None, skip_ml: bool = False, paper_writing_only: bool = False, *args, **kwargs):
        metadata = self.load_ins({"instance_path": instance_path, "task_level": task_level})
        context_variables = {
            "working_dir": workplace_name, # TODO: change to the codebase path
            "date_limit": metadata["date_limit"],
        }

        # Skip GitHub code search if paper_writing_only mode (saves tokens, not needed for articles)
        if paper_writing_only:
            print("[INFO] Paper Writing Only mode: Skipping GitHub code search")
            github_result = "Code search skipped - paper writing only mode"
        else:
            github_result = self.git_search({"metadata": metadata})
        
        # Use custom_task if provided (user question), otherwise load from benchmark
        import re
        if custom_task:
            # User provided a custom task/question
            final_task = custom_task.strip()
            # Remove @ mentions from the task
            final_task = re.sub(r'@\w+\s*', '', final_task).strip()
            actual_references = references if references and references.strip() else ""
            # Try to load benchmark for dataset info, but use custom task
            try:
                data_module = importlib.import_module(f"benchmark.process.dataset_candidate.{category}.metaprompt")
                dataset_description = f"""\
You should select SEVERAL datasets as experimental datasets from the following description:
{data_module.DATASET}

We have already selected the following baselines for these datasets:
{data_module.BASELINE}

The performance comparison of these datasets:
{data_module.COMPARISON}

And the evaluation metrics are:
{data_module.EVALUATION}

{data_module.REF}
"""
            except (ImportError, AttributeError):
                dataset_description = "Please select appropriate datasets for the given task."
        else:
            # Use benchmark task
            try:
                data_module = importlib.import_module(f"benchmark.process.dataset_candidate.{category}.metaprompt")
                final_task = data_module.TASK
                actual_references = references if references and references.strip() else ""
                dataset_description = f"""\
You should select SEVERAL datasets as experimental datasets from the following description:
{data_module.DATASET}

We have already selected the following baselines for these datasets:
{data_module.BASELINE}

The performance comparison of these datasets:
{data_module.COMPARISON}

And the evaluation metrics are:
{data_module.EVALUATION}

{data_module.REF}
"""
            except (ImportError, AttributeError):
                final_task = "Complete the machine learning task."
                actual_references = references if references and references.strip() else ""
                dataset_description = "Please select appropriate datasets for the given task."
        
        # Skip codebase preparation if paper_writing_only mode
        if paper_writing_only:
            print("[INFO] Paper Writing Only mode: Skipping codebase preparation")
            prepare_res = "Codebase preparation skipped - paper writing only mode. Using provided references only."
            paper_list = []
            download_res = "No codebases selected - paper writing only mode."
        else:
            # Search for papers - either from provided references or based on the task
            if actual_references:
                # User provided specific references
                query = f"""\
You are given a list of papers, searching results of the papers on GitHub. 
List of papers:
{actual_references}

Searching results of the papers on GitHub:
{github_result}

Your task is to choose at least 5 repositories as the reference codebases. Note that this time there is no innovative ideas, you should choose the most valuable repositories as the reference codebases.
"""
            else:
                # No specific references, search based on the task
                query = f"""\
You are given a task:
{final_task}

Searching results of relevant papers on GitHub:
{github_result}

Your task is to search for and choose at least 5 repositories as the reference codebases that are relevant to the given task. Note that this time there is no innovative ideas, you should choose the most valuable repositories as the reference codebases.
"""
            messages = [{"role": "user", "content": query}]
            prepare_messages, context_variables = await self.prepare_agent(messages, context_variables)
            prepare_res = prepare_messages[-1]["content"]
            prepare_dict = extract_json_from_output(prepare_res)
            paper_list = prepare_dict.get("reference_papers", [])
            if paper_list:
                download_res = self.download_papaer({"paper_list": paper_list, "local_root": local_root, "workplace_name": workplace_name})
            else:
                download_res = "No papers were selected for download. The agent will proceed with general knowledge."
        
        # Add mode-specific instructions
        mode_instructions = ""
        if mode == "Idea Spark":
            mode_instructions = "\n\nMODE: Idea Spark - Focus on quick ideation and generating innovative concepts rapidly. Prioritize speed and creativity while maintaining feasibility."
        elif mode == "Deep Survey":
            mode_instructions = "\n\nMODE: Deep Survey - Conduct thorough and comprehensive literature review. Be exhaustive in analyzing papers, identifying gaps, and generating well-researched ideas."
        elif mode == "Auto Experiment":
            mode_instructions = "\n\nMODE: Auto Experiment - Generate ideas that are experiment-ready. Focus on ideas that can be quickly validated through experiments and iterative refinement."
        
        # Build the reference section separately to avoid f-string backslash issue
        if actual_references:
            reference_section = f"And a list of papers for your reference:\n{actual_references}"
        else:
            reference_section = "Please use your knowledge and search capabilities to find relevant information and papers for this task."
        
        # Build query based on mode - don't mention papers/downloads if skipped
        if paper_writing_only:
            # Paper writing mode - no code/papers, just idea generation
            idea_query = f"""\
I have a task related to research:
{final_task}
{reference_section}

Your task is to generate innovative research ideas for the given task. Use your knowledge and understanding of the field to propose novel approaches.

Note that the math formula should be as complete as possible.{mode_instructions}
"""
        else:
            # Full mode - mention papers and codebases
            idea_query = f"""\
I have a task related to machine learning:
{final_task}
{reference_section}

I have carefully gone through these papers' github repositories and found download some of them in my local machine, with the following information:
{prepare_res}
And I have also downloaded the corresponding paper in the Tex format, with the following information:
{download_res}

Your task is to thoroughly review research papers and generate innovative ideas for the given task.

Note that the math formula should be as complete as possible.{mode_instructions}
"""
        messages = [{"role": "user", "content": idea_query}]
        context_variables["notes"] = []
        
        # Generate exactly 1 idea for Idea Spark (minimum tokens)
        # Environment variable can override: IDEA_NUM (default: 1)
        IDEA_NUM = int(os.getenv("IDEA_NUM", "1"))  # Default to 1 idea
        if mode == "Idea Spark":
            IDEA_NUM = 1  # Always 1 for Idea Spark to minimize tokens
        elif mode == "Deep Survey":
            IDEA_NUM = min(IDEA_NUM, 2)  # Cap at 2 for Deep Survey
        else:  # Auto Experiment or default
            IDEA_NUM = min(IDEA_NUM, 1)  # Cap at 1 for others
        
        # CRITICAL: Aggressive message history trimming to prevent token explosion
        MAX_MESSAGE_HISTORY = int(os.getenv("MAX_MESSAGE_HISTORY", "2"))  # Reduced to 2 for minimal token usage
        
        def trim_message_history(msgs, max_len=MAX_MESSAGE_HISTORY):
            """Trim message history to prevent token explosion"""
            if len(msgs) <= max_len:
                return msgs
            # Keep first message (initial prompt) and last max_len-1 messages
            return [msgs[0]] + msgs[-(max_len-1):]
        
        # Generate multiple ideas (2 by default) - each is independent to save tokens
        ideas = []
        for i in range(IDEA_NUM):
            # Use fresh messages for each idea to avoid token buildup
            # Only keep the original query, not previous idea responses
            idea_messages = [messages[0]]  # Just the original query
            if i > 0:
                # For subsequent ideas, just ask for another idea (no history)
                idea_messages.append({"role": "user", "content": "Generate another different innovative idea for the same task."})
            
            survey_messages, context_variables = await self.idea_agent(idea_messages, context_variables, iter_times=i+1)
            idea_content = survey_messages[-1]["content"]
            ideas.append(idea_content)
        
        # Use first idea as main result (single response only)
        survey_res = ideas[0] if ideas else "No ideas generated."
        # print(survey_res)

        # Skip code survey if paper_writing_only mode (not needed for article writing)
        if paper_writing_only:
            print("[INFO] Paper Writing Only mode: Skipping code survey")
            # Don't create placeholder text - just skip it entirely
            code_survey_res = "N/A"  # Will be filtered out in formatting
        else:
            code_survey_query = f"""\
I have an innovative idea related to machine learning:
{survey_res}

I have carefully gone through these papers' github repositories and found download some of them in my local machine, in the directory `/workplace`, use the `list_files` tool to navigate the directory.
And I have also downloaded the corresponding paper in the Tex format, with the following information:
{download_res}

Your task is to carefully understand the innovative idea, and thoroughly review codebases and generate a comprehensive implementation report for the innovative idea. Review the codebases systematically and identify all academic concepts in the innovative idea.

Note that the code implementation should be as complete as possible.
You have a maximum of 10 iterations to complete this task. If you cannot find all concepts after thorough review, document what you found and proceed.
"""
            messages = [{"role": "user", "content": code_survey_query}]
            # CRITICAL: Reduce code survey iterations (was 10, now 2-3 max)
            MAX_CODE_SURVEY_ITERATIONS = int(os.getenv("MAX_CODE_SURVEY_ITERATIONS", "2"))  # Reduced from 10 to 2
            code_survey_messages = None
            for iteration in range(MAX_CODE_SURVEY_ITERATIONS):
                # Trim messages before each call to prevent token explosion
                messages = trim_message_history(messages, max_len=MAX_MESSAGE_HISTORY)
                code_survey_messages, context_variables = await self.code_survey_agent(messages, context_variables)
                code_survey_res = code_survey_messages[-1]["content"]
                # Check if agent indicates completion
                if "completed" in code_survey_res.lower() or "finished" in code_survey_res.lower() or iteration >= MAX_CODE_SURVEY_ITERATIONS - 1:
                    break
                # Add continuation message if not complete
                messages.append({"role": "assistant", "content": code_survey_res[:2000]})  # Truncate response to 2000 chars
                messages.append({"role": "user", "content": "Continue reviewing and ensure all academic concepts are covered."})
            
            code_survey_res = code_survey_messages[-1]["content"] if code_survey_messages else "Code survey completed."
        # print(code_survey_res)
        
        context_variables["model_survey"] = code_survey_res

        # Skip plan agent if paper_writing_only mode (no code/papers to plan)
        if paper_writing_only:
            print("[INFO] Paper Writing Only mode: Skipping plan agent (no code implementation needed)")
            plan_res = "N/A"  # Will be filtered out in formatting
        else:
            plan_query = f"""\
I have an innovative ideas related to machine learning:
{survey_res}
And a list of papers for your reference:
{references}

I have carefully gone through these papers' github repositories and found download some of them in my local machine, with the following information:
{prepare_res}

I have also understood the innovative idea, comprehensively reviewed the codebases, and generated a comprehensive implementation report:
{code_survey_res}

We have already selected the following datasets as experimental datasets:
{dataset_description}

Your task is to carefully review the existing resources and understand the task, and give me a detailed plan for the implementation.
"""
            messages = [{"role": "user", "content": plan_query}]
            # Limit plan agent turns to prevent infinite loops (max 5 turns)
            plan_messages, context_variables = await self.coding_plan_agent(messages, context_variables, max_turns=5)
            plan_res = plan_messages[-1]["content"]

        # write the model based on the model survey notes
        ml_dev_query = f"""\
INPUT:
You are given an innovative idea:
{survey_res}. 
and the reference codebases chosen by the `Prepare Agent`:
{prepare_res}
And I have conducted the comprehensive survey on the innovative idea and the papers, and give you the model survey notes:
{survey_res}
You should carefully go through the math formula and the code implementation, and implement the innovative idea according to the plan and existing resources.

We have already selected the following datasets as experimental datasets:
{dataset_description}
Your task is to implement the innovative idea after carefully reviewing the math formula and the code implementation in the paper notes and existing resources in the directory `/{workplace_name}`. You should select ONE most appropriate and lightweight dataset from the given datasets, and implement the idea by creating new model, and EXACTLY run TWO epochs of training and testing on the ACTUAL dataset on the GPU device. Note that EVERY atomic academic concept in model survey notes should be implemented in the project.

PROJECT STRUCTURE REQUIREMENTS:
1. Directory Organization
- Data: `/{workplace_name}/project/data/`
     * Use the dataset selected by the `Plan Agent`
     * NO toy or random datasets
- Model Components: `/{workplace_name}/project/model/`
    * All model architecture files
    * All model components as specified in survey notes
    * Dataset processing scripts and utilities

- Training: `/{workplace_name}/project/training/`
    * Training loop implementation
    * Loss functions
    * Optimization logic

- Testing: `/{workplace_name}/project/testing/`
    * Evaluation metrics
    * Testing procedures

- Data processing: `/{workplace_name}/project/data_processing/`
    * Implement the data processing pipeline

- Main Script: `/{workplace_name}/project/run_training_testing.py`
    * Complete training and testing pipeline
    * Configuration management
    * Results logging

2. Complete Implementation Requirements
   - MUST implement EVERY component from model survey notes
   - NO placeholder code (no `pass`, `...`, `raise NotImplementedError`)
   - MUST include complete logic and mathematical operations
   - Each component MUST be fully functional and tested

3. Dataset and Training Requirements
   - Select and download ONE actual dataset from references
   - Implement full data processing pipeline
   - Train for exactly 2 epochs
   - Test model performance after training
   - Log all metrics and results

4. Integration Requirements
   - All components must work together seamlessly
   - Clear dependencies between modules
   - Consistent coding style and documentation
   - Proper error handling and GPU support

EXECUTION WORKFLOW:
1. Dataset Setup
   - Choose appropriate dataset from references (You MUST use the actual dataset, not the toy or random datasets) [IMPORTANT!!!]
   - Download to data directory `/{workplace_name}/project/data`
   - Implement processing pipeline in `/{workplace_name}/project/data_processing/`
   - Verify data loading

2. Model Implementation
   - Study model survey notes thoroughly
   - Implement each component completely
   - Document mathematical operations
   - Add comprehensive docstrings

3. Training Implementation
   - Complete training loop
   - Loss function implementation
   - Optimization setup
   - Progress monitoring

4. Testing Setup
   - Implement evaluation metrics
   - Create testing procedures
   - Set up results logging
   - Error handling

5. Integration
   - Create run_training_testing.py
   - Configure for 2 epoch training
   - Add GPU support and OOM handling
   - Implement full pipeline execution

VERIFICATION CHECKLIST:
1. Project Structure
   - All directories exist and are properly organized
   - Each component is in correct location
   - Clear separation of concerns

2. Implementation Completeness
   - Every function is fully implemented
   - No placeholder code exists
   - All mathematical operations are coded
   - Documentation is complete

3. Functionality
   - Dataset downloads and loads correctly
   - Training runs for 2 epochs
   - Testing produces valid metrics
   - GPU support is implemented

Remember: 
- MUST use actual dataset (no toy data, download according to the reference codebases) [IMPORTANT!!!]
- Implementation MUST strictly follow model survey notes
- ALL components MUST be fully implemented
- Project MUST run end-to-end without placeholders
- MUST complete 2 epochs of training and testing
"""
        # Skip ML agent execution if skip_ml flag is set (saves significant tokens)
        # In paper writing mode, we don't need ML implementation at all
        if skip_ml or paper_writing_only:
            print("[INFO] Skipping ML agent execution (paper writing mode - research only)")
            # Don't set any ML-related variables - they're not needed
            refine_res = None  # Will be set properly in final_result logic
        else:
            messages = [{"role": "user", "content": ml_dev_query}]
            ml_dev_messages, context_variables = await self.ml_agent(messages, context_variables)
            ml_dev_res = ml_dev_messages[-1]["content"]

            query = f"""\
INPUT:
You are given an innovative idea:
{survey_res}
and the reference codebases chosen by the `Prepare Agent`:
{prepare_res}
and the detailed coding plan:
{plan_res}
The implementation of the project:
{ml_dev_res}
Your task is to evaluate the implementation, and give a suggestion about the implementation. Note that you should carefully check whether the implementation meets the idea, especially the atomic academic concepts in the model survey notes one by one! If not, give comprehensive suggestions about the implementation.

[IMPORTANT] You should fully utilize the existing resources in the reference codebases as much as possible, including using the existing datasets, model components, and training process, but you should also implement the idea by creating new model components!

[IMPORTANT] You should recognize every key point in the innovative idea, and carefully check whether the implementation meets the idea one by one!

[IMPORTANT] Some tips about the evaluation:
1. The implementation should carefully follow the plan. Please check every component in the plan step by step.
2. The implementation should have the test process. All in all, you should train ONE dataset with TWO epochs, and finally test the model on the test dataset within one script. The test metrics should follow the plan.
3. The model should be train on GPU device. If you meet Out of Memory problem, you should try another specific GPU device.
"""
            input_messages = [{
                "role": "user",
                "content": query
            }]
            judge_messages, context_variables = await self.judge_agent(input_messages, context_variables)
            judge_res = judge_messages[-1]["content"]

            # CRITICAL: Drastically reduce iterations (default to 0, max 1)
            MAX_ITER_TIMES = min(max_iter_times, 1) if max_iter_times > 0 else 0  # Cap at 1 iteration max
            MAX_ITER_TIMES = int(os.getenv("MAX_ITER_TIMES", str(MAX_ITER_TIMES)))  # Allow env override
            MAX_ITER_TIMES = min(MAX_ITER_TIMES, 1)  # Hard cap at 1 to prevent token explosion
            
            for i in range(MAX_ITER_TIMES):
                query = f"""\
You are given an innovative idea:
{survey_res}
and the reference codebases chosen by the `Prepare Agent`:
{prepare_res}
and the detailed coding plan:
{plan_res}
And your last implementation of the project:
{ml_dev_res}
The suggestion about your last implementation:
{judge_res}
Your task is to modify the project according to the suggestion. Note that you should MODIFY rather than create a new project! Take full advantage of the existing resources! Still use the SAME DATASET!

[IMPORTANT] You should modify the project in the directory `/{workplace_name}/project`, rather than create a new project!

[IMPORTANT] If you meet dataset missing problem, you should download the dataset from the reference codebases, and put the dataset in the directory `/{workplace_name}/project/data`. 

[IMPORTANT] You CANNOT stop util you 2 epochs of training and testing on your model with the ACTUAL dataset.

[IMPORTANT] You encounter ImportError while using `run_python()`, you should check whether every `__init__.py` file is correctly implemented in the directories in the `/{workplace_name}/project`!

[IMPORTANT] Carefully check whether model and its components are correctly implemented according to the model survey notes!

Remember: 
- Implementation MUST strictly follow model survey notes
- ALL components MUST be fully implemented
- Project MUST run end-to-end without placeholders
- MUST use actual dataset (no toy data)
- MUST complete 2 epochs of training and testing
"""
                # CRITICAL: Trim judge_messages before each call to prevent token explosion
                judge_messages = trim_message_history(judge_messages, max_len=MAX_MESSAGE_HISTORY)
                judge_messages.append({"role": "user", "content": query})
                judge_messages, context_variables = await self.ml_agent(judge_messages, context_variables, iter_times=i+1)
                ml_dev_res = judge_messages[-1]["content"][:3000]  # Truncate to 3000 chars to save tokens
                
                # Truncate long strings to save tokens
                survey_res_short = survey_res[:1000] if len(survey_res) > 1000 else survey_res
                prepare_res_short = prepare_res[:1000] if len(prepare_res) > 1000 else prepare_res
                plan_res_short = plan_res[:1000] if len(plan_res) > 1000 else plan_res
                ml_dev_res_short = ml_dev_res[:2000] if len(ml_dev_res) > 2000 else ml_dev_res
                
                query = f"""\
You are given an innovative idea:
{survey_res_short}
and the reference codebases chosen by the `Prepare Agent`:
{prepare_res_short}
and the detailed coding plan:
{plan_res_short}
The implementation of the project:
{ml_dev_res_short}
Please evaluate the implementation, and give a suggestion about the implementation.
"""
                # CRITICAL: Trim again before judge agent call
                judge_messages = trim_message_history(judge_messages, max_len=MAX_MESSAGE_HISTORY)
                judge_messages.append({"role": "user", "content": query})
                judge_messages, context_variables = await self.judge_agent(judge_messages, context_variables, iter_times=i+1)
                judge_res = judge_messages[-1]["content"][:2000]  # Truncate response
                if '"fully_correct": true' in judge_messages[-1]["content"]:
                    break
            
            # return judge_messages[-1]["content"]
            # submit the code to the environment -> get the result
            
            ml_submit_query = f"""\
You are given an innovative idea:
{survey_res}
And your last implementation of the project:
{ml_dev_res}
The suggestion about your last implementation:
{judge_res}
You have run out the maximum iteration times to implement the idea by running the script `run_training_testing.py` with TWO epochs of training and testing on ONE ACTUAL dataset.
Your task is to submit the code to the environment by running the script `run_training_testing.py` with APPROPRIATE epochs of training and testing on THIS ACTUAL dataset in order to get some stastical results. You must MODIFY the epochs in the script `run_training_testing.py` rather than use the 2 epochs.

[IMPORTANT] In this stage, you are NOT allowed to modify the existing code in the script `run_training_testing.py` except for the epochs!

Note that if your last implementation is not runable, you should finalize the submission with `case_not_resolved` function. But you can temporarily ignore the judgement of the `Judge Agent` which contains the suggestions about the implementation.
After you get the result, you should return the result with your analysis and suggestions about the implementation with `case_resolved` function.
"""
            # CRITICAL: Trim before submit call
            judge_messages = trim_message_history(judge_messages, max_len=MAX_MESSAGE_HISTORY)
            judge_messages.append({"role": "user", "content": ml_submit_query})
            judge_messages, context_variables = await self.ml_agent(judge_messages, context_variables, iter_times="submit")
            submit_res = judge_messages[-1]["content"][:3000]  # Truncate to save tokens

            # CRITICAL: Reduce experiment iterations to 0 by default (was 1-2)
            EXP_ITER_TIMES = int(os.getenv("EXP_ITER_TIMES", "0")) if not skip_ml else 0  # Default to 0
            EXP_ITER_TIMES = min(EXP_ITER_TIMES, 1)  # Hard cap at 1
            for i in range(EXP_ITER_TIMES):
                exp_planner_query = f"""\
You are given an innovative idea:
{survey_res}
And the reference codebases chosen by the `Prepare Agent`:
{prepare_res}
And the detailed coding plan:
{plan_res}
You have conducted the experiments and get the experimental results:
{submit_res}
Your task is to: 
1. Analyze the experimental results and give a detailed analysis report about the results.
2. Analyze the reference codebases and papers, and give a further plan to let `Machine Learning Agent` to do more experiments based on the innovative idea. The further experiments could include but not limited to:
    - Modify the implementation to better fit the idea.
    - Add more experiments to prove the effectiveness and superiority of the idea. 
    - Visualize the experimental results and give a detailed analysis report about the results.
    - ANY other experiments that exsiting concurrent reference papers and codebases have done.
DO NOT use the `case_resolved` function before you have carefully and comprehensively analyzed the experimental results and the reference codebases and papers.
"""
                # CRITICAL: Trim before exp_analyser call
                judge_messages = trim_message_history(judge_messages, max_len=MAX_MESSAGE_HISTORY)
                judge_messages.append({"role": "user", "content": exp_planner_query})
                judge_messages, context_variables = await self.exp_analyser(judge_messages, context_variables, iter_times=f"refine_{i+1}")
                analysis_report = judge_messages[-1]["content"][:2000]  # Truncate to save tokens

                analysis_report = context_variables.get("experiment_report", [{}])[-1].get("analysis_report", analysis_report)[:2000]
                further_plan = context_variables.get("experiment_report", [{}])[-1].get("further_plan", {})
                # print(analysis_report)
                # Truncate long strings to save tokens
                survey_res_short = survey_res[:1000] if len(survey_res) > 1000 else survey_res
                prepare_res_short = prepare_res[:1000] if len(prepare_res) > 1000 else prepare_res
                plan_res_short = plan_res[:1000] if len(plan_res) > 1000 else plan_res
                submit_res_short = submit_res[:2000] if len(submit_res) > 2000 else submit_res
                analysis_report_short = analysis_report[:2000] if len(analysis_report) > 2000 else analysis_report
                
                refine_query = f"""\
You are given an innovative idea:
{survey_res_short}
And the reference codebases chosen by the `Prepare Agent`:
{prepare_res_short}
And the detailed coding plan:
{plan_res_short}
You have conducted the experiments and get the experimental results:
{submit_res_short}
And a detailed analysis report about the results are given by the `Experiment Planner Agent`:
{analysis_report_short}
Your task is to refine the experimental results according to the analysis report by modifying existing code in the directory `/{workplace_name}/project`. You should NOT stop util every experiment is done with ACTUAL results. If you encounter Out of Memory problem, you should try another specific GPU device. If you encounter ANY other problems, you should try your best to solve the problem by yourself.

Note that you should fully utilize the existing code in the directory `/{workplace_name}/project` as much as possible. If you want to add more experiments, you should add the python script in the directory `/{workplace_name}/project/`, like `run_training_testing.py`. Select and output the important results during the experiments into the log files, do NOT output them all in the terminal.
"""
                # CRITICAL: Trim again before ml_agent call
                judge_messages = trim_message_history(judge_messages, max_len=MAX_MESSAGE_HISTORY)
                judge_messages.append({"role": "user", "content": refine_query})
                judge_messages, context_variables = await self.ml_agent(judge_messages, context_variables, iter_times=f"refine_{i+1}")
                refine_res = judge_messages[-1]["content"][:3000]  # Truncate to save tokens

        # Determine final result message - clean summary without ML references
        if skip_ml or paper_writing_only:
            # In paper writing mode, we only do research - no ML/code needed
            final_result_text = """Research completed successfully.

The following research components have been generated:
- Research idea and concept analysis
- Literature survey and review  
- Implementation plan (conceptual)

This is a research-only mode focused on idea generation and analysis. Code implementation is not included."""
        else:
            # Only show refine_res if ML was actually executed
            final_result_text = refine_res if 'refine_res' in locals() and refine_res and refine_res is not None else "Research completed successfully."
        
        # Keep plan_res as dict if it's a dict - don't convert to JSON string
        # The formatter in main_ai_researcher.py will handle dict formatting
        plan_text = plan_res
        if not isinstance(plan_res, (dict, str)):
            plan_text = str(plan_res) if plan_res else None
        elif plan_res == "N/A" or plan_res is None:
            plan_text = None
        
        # Return the final refined result along with key intermediate results
        # Filter out "N/A" values
        final_result = {
            "final_result": final_result_text,
            "selected_idea": survey_res if 'survey_res' in locals() and survey_res and survey_res != "N/A" else None,
            "code_survey": code_survey_res if 'code_survey_res' in locals() and code_survey_res and code_survey_res != "N/A" else None,
            "plan": plan_text if plan_text and plan_text != "N/A" else None,
            "context_notes": context_variables.get("notes", [])
        }
        print(f"[DEBUG] Returning result from forward: {type(final_result)}")
        return final_result
        
def main(args, references, mode="Idea Spark", custom_task=None):
    """
    MAX_ATTEMPTS

    # load the eval instance

    # choose the code base

    # generate the detailed coding plan

    # coding and debuging -> fail to implement the plan

    -> success to implement the plan

    # submit the code to the environment -> get the result

    for attempt in range(MAX_ATTEMPTS): 
        # evaluate the result

        # coding and debuging

        # submit the code to the environment -> get the result
        if done:
            break
    """
    # load the eval instance
    with open(args.instance_path, "r", encoding="utf-8") as f:
        eval_instance = json.load(f)
    instance_id = eval_instance["instance_id"] + "_idea"
    local_root = os.path.join(os.getcwd(),"workplace_paper" , f"task_{instance_id}" + "_" + COMPLETION_MODEL.replace("/", "__"),  args.workplace_name)
    container_name = args.container_name + "_" + instance_id + "_" + COMPLETION_MODEL.replace("/", "__")
    os.makedirs(local_root, exist_ok=True)
    env_config = DockerConfig(container_name = container_name, 
                              workplace_name = args.workplace_name, 
                              communication_port = args.port, 
                              local_root = local_root,
                              )
    
    code_env = DockerEnv(env_config)
    code_env.init_container()
    setup_dataset(args.category, code_env.local_workplace)
    web_env = BrowserEnv(browsergym_eval_env = None, local_root=env_config.local_root, workplace_name=env_config.workplace_name)
    file_env = RequestsMarkdownBrowser(viewport_size=1024 * 4, local_root=env_config.local_root, workplace_name=env_config.workplace_name, downloads_folder=os.path.join(env_config.local_root, env_config.workplace_name, "downloads"))
    
    # Use global log path if available, otherwise use local log
    import global_state
    if hasattr(global_state, 'LOG_PATH') and global_state.LOG_PATH:
        log_path = global_state.LOG_PATH
        # Ensure absolute path
        if not os.path.isabs(log_path):
            log_path = os.path.abspath(log_path)
    else:
        log_path = os.path.abspath(f"log_{instance_id}")
    
    print(f"[DEBUG] Using log path: {log_path}")
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)
    
    # CRITICAL FIX: Use unique cache path based on job_id or custom_task to prevent cache collisions
    # If custom_task is provided, create unique cache based on task hash
    # Otherwise, use instance_id (for benchmark tasks)
    import hashlib
    if custom_task:
        # Create unique cache path based on custom task to prevent cache reuse across different queries
        task_hash = hashlib.md5(custom_task.encode()).hexdigest()[:12]
        unique_cache_id = f"{instance_id}_{task_hash}"
        print(f"[DEBUG] Using unique cache path for custom task: {unique_cache_id}")
    else:
        # For benchmark tasks, use instance_id
        unique_cache_id = instance_id
        print(f"[DEBUG] Using benchmark cache path: {unique_cache_id}")
    
    cache_path = "cache_" + unique_cache_id + "_" + COMPLETION_MODEL.replace("/", "__")
    flow = InnoFlow(cache_path=cache_path, log_path=log_path, code_env=code_env, web_env=web_env, file_env=file_env, model=args.model)
    # ml_result = await flow(instance_path=instance_path)
    
    # DEFAULT: Paper writing only mode (skip code unless explicitly requested)
    # Users must set ENABLE_CODE_IMPLEMENTATION=true or use --enable-code flag to get code search, code survey, and ML implementation
    # Safely check for enable_code attribute (may not exist when called from main_ai_researcher.py)
    enable_code_flag = False
    if hasattr(args, 'enable_code'):
        enable_code_flag = args.enable_code
    else:
        # Attribute doesn't exist, default to False (paper writing only)
        enable_code_flag = False
    
    enable_code_env = os.getenv("ENABLE_CODE_IMPLEMENTATION", "false").lower() in ("true", "1", "yes")
    enable_code = enable_code_flag or enable_code_env
    
    # Deep Survey mode should always enable code implementation (no skipping)
    if mode == "Deep Survey":
        enable_code = True
        paper_writing_only = False
        print("[INFO] Deep Survey mode: Code implementation ENABLED (all steps will run)")
    else:
        paper_writing_only = not enable_code  # Default to paper writing only for other modes
    
    if paper_writing_only:
        print("[INFO] Paper Writing Only mode (DEFAULT): Skipping all code-related steps")
        print("[INFO]   - GitHub code search: SKIPPED")
        print("[INFO]   - Codebase preparation: SKIPPED")
        print("[INFO]   - Code survey: SKIPPED")
        print("[INFO]   - ML implementation: SKIPPED")
        print("[INFO]   To enable code implementation, set: ENABLE_CODE_IMPLEMENTATION=true")
        skip_ml = True  # Skip ML when in paper writing mode
    else:
        print("[INFO] Code Implementation mode: All code-related steps will run")
        print("[INFO]   - GitHub code search: ENABLED")
        print("[INFO]   - Codebase preparation: ENABLED")
        print("[INFO]   - Code survey: ENABLED")
        print("[INFO]   - ML implementation: ENABLED")
        # Check if user also wants to skip ML specifically
        # Safely check for skip_ml attribute (may not exist when called from main_ai_researcher.py)
        skip_ml_flag = getattr(args, 'skip_ml', False)
        skip_ml = skip_ml_flag or os.getenv("SKIP_ML_AGENT", "false").lower() in ("true", "1", "yes")
        if skip_ml:
            print("[INFO]   Note: ML agent is explicitly disabled via SKIP_ML_AGENT")
    
    try:
        result = asyncio.run(flow(instance_path=args.instance_path, task_level=args.task_level, local_root=local_root, workplace_name=args.workplace_name, max_iter_times=args.max_iter_times, category=args.category, references=references, mode=mode, custom_task=custom_task, skip_ml=skip_ml, paper_writing_only=paper_writing_only))
        print(f"[DEBUG] run_infer_idea.main: asyncio.run returned: {type(result)}, value: {result if result else 'None'}")
        if result is None:
            print("[WARNING] run_infer_idea.main: asyncio.run returned None")
            # Fallback if forward didn't return anything
            result = {
                "final_result": "Research process completed. Check logs for details.",
                "selected_idea": "N/A",
                "code_survey": "N/A",
                "plan": "N/A",
                "context_notes": []
            }
    except Exception as e:
        print(f"[ERROR] run_infer_idea.main: Exception in asyncio.run: {e}")
        import traceback
        traceback.print_exc()
        
        # Extract underlying exception from RetryError for better error reporting
        error_message = str(e)
        error_type = type(e).__name__
        
        # Check if it's a RetryError and extract the underlying exception
        if error_type == "RetryError" and hasattr(e, 'last_attempt'):
            if e.last_attempt and e.last_attempt.outcome:
                underlying_exception = e.last_attempt.outcome.exception()
                if underlying_exception:
                    error_type = type(underlying_exception).__name__
                    error_message = str(underlying_exception)
                    print(f"[ERROR] Underlying exception: {error_type} - {error_message}")
        
        result = {
            "final_result": f"Error during research process: {error_type} - {error_message}",
            "selected_idea": "N/A",
            "code_survey": "N/A",
            "plan": "N/A",
            "context_notes": []
        }
    print(f"[DEBUG] run_infer_idea.main returning: {type(result)}, value: {result if result else 'None'}")
    return result




if __name__ == "__main__":
    args = get_args()
    main(args)





"""\
INPUT:
You are given an innovative idea:
Combine DDPM model with transformer model to generate the image.
And `Prepare Agent` has chosen the reference codebases:
{prepare_res}
And `Survey Agent` has given the model survey notes:
{survey_res}

REQUIREMENTS:
1. Model Organization
   - Break down the model into smaller, logical modules based on academic definitions
   - Each module should correspond to one or more academic concepts from the papers
   - Create a clear hierarchy of modules that can be assembled into the final model
   - Example structure:
     * Base modules (fundamental building blocks)
     * Intermediate modules (combining base modules)
     * Main model class (assembling all modules)

2. Module Implementation Guidelines
   - Each module should be in a separate file under `/{workplace_name}/project/model/`
   - Modules should have clear input/output interfaces
   - Include docstrings with academic references and mathematical formulations
   - Implement forward pass with complete mathematical operations

3. Complete Implementation Requirements
   - MUST implement EVERY component from model survey notes
   - NO placeholder code (no `pass`, `...`, `raise NotImplementedError`)
   - MUST include complete logic and mathematical operations
   - Each module MUST be fully functional and tested
   - Final model should inherit from nn.Module and combine all sub-modules

Remember: 
- Break down complex models into smaller, reusable modules
- Each module should map to specific academic concepts
- Implementation MUST strictly follow model survey notes
- ALL components MUST be fully implemented
- Project MUST run end-to-end without placeholders

Task: 
Carefully go through the model survey notes, break down the model into logical modules based on academic definitions, and implement each module in a realistic way. NO placeholder code. 
In this stage, you only care about the model implementation, and don't care about the dataset, training, testing.
"""