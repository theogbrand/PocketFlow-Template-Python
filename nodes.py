import os
import yaml
import logging
from datetime import datetime
from pocketflow import Node, BatchNode
from utils.call_llm import call_llm
from utils.read_file import read_file
from utils.delete_file import delete_file
from utils.replace_file import replace_file
from utils.search_ops import grep_search
from utils.dir_ops import list_dir

# Configure logger for nodes
logger = logging.getLogger(__name__)


class MainDecisionAgentNode(Node):
    """Main agent that decides which tool to use based on user query and context."""
    
    def prep(self, shared):
        user_query = shared["user_query"]
        history = shared.get("history", [])
        working_dir = shared["working_dir"]
        
        logger.info(f"MainDecisionAgent: Processing user query: '{user_query}'")
        logger.info(f"MainDecisionAgent: Working directory: {working_dir}")
        logger.info(f"MainDecisionAgent: History contains {len(history)} previous actions")
        
        # Format history for context
        history_context = ""
        if history:
            history_context = "\nPrevious actions:\n"
            for i, action in enumerate(history[-3:]):  # Show last 3 actions
                history_context += f"{i+1}. {action['tool']}: {action['reason']}\n"
                if action.get('result'):
                    result_preview = str(action['result'])[:100] + "..." if len(str(action['result'])) > 100 else str(action['result'])
                    history_context += f"   Result: {result_preview}\n"
        
        return {
            "user_query": user_query,
            "history_context": history_context,
            "working_dir": working_dir,
            "has_history": len(history) > 0
        }
    
    def exec(self, prep_res):
        logger.info("MainDecisionAgent: Calling LLM to decide next action")
        
        prompt = f"""You are a coding assistant with access to file operations. Analyze the user's request and decide which tool to use.

USER REQUEST: {prep_res['user_query']}
WORKING DIRECTORY: {prep_res['working_dir']}
{prep_res['history_context']}

AVAILABLE TOOLS:
1. read_file - Read contents of a specific file
   Parameters: target_file (path), explanation (reason)
   
2. edit_file - Modify a file with specific changes  
   Parameters: target_file (path), instructions (what to change), code_edit (the actual changes)
   
3. delete_file - Remove a file
   Parameters: target_file (path), explanation (reason)
   
4. grep_search - Search for text patterns in files
   Parameters: query (search term), case_sensitive (optional), include_pattern (optional), exclude_pattern (optional), explanation (reason)
   
5. list_dir - Show directory contents with tree visualization
   Parameters: relative_workspace_path (directory path), explanation (reason)
   
6. finish - Complete the task and provide final response

Decide which tool to use next. Output in YAML format:

```yaml
tool: <tool_name>
reason: <brief explanation why this tool is needed>
params:
  target_file: <file_path>  # if applicable
  explanation: <explanation>  # if applicable
  instructions: <edit_instructions>  # for edit_file only
  code_edit: <code_changes>  # for edit_file only
  query: <search_term>  # for grep_search only
  relative_workspace_path: <dir_path>  # for list_dir only
```"""

        response = call_llm(prompt)
        
        # Parse YAML response
        try:
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            result = yaml.safe_load(yaml_str)
            logger.info(f"MainDecisionAgent: Successfully parsed LLM response")
        except Exception as e:
            logger.warning(f"MainDecisionAgent: Failed to parse LLM response: {e}")
            # Fallback parsing
            result = {"tool": "finish", "reason": "Unable to parse tool selection", "params": {}}
        
        # Validate result
        valid_tools = ["read_file", "edit_file", "delete_file", "grep_search", "list_dir", "finish"]
        if result.get("tool") not in valid_tools:
            logger.warning(f"MainDecisionAgent: Invalid tool '{result.get('tool')}' selected, defaulting to finish")
            result = {"tool": "finish", "reason": "Invalid tool selected", "params": {}}
        
        logger.info(f"MainDecisionAgent: Selected tool '{result['tool']}' with reason: {result['reason']}")
        return result
    
    def post(self, shared, prep_res, exec_res):
        # Add new action to history (will be updated with result by action nodes)
        action_entry = {
            "tool": exec_res["tool"],
            "reason": exec_res["reason"],
            "params": exec_res.get("params", {}),
            "result": None,  # Will be filled by action nodes
            "timestamp": datetime.now().isoformat()
        }
        
        if "history" not in shared:
            shared["history"] = []
        shared["history"].append(action_entry)
        
        logger.info(f"MainDecisionAgent: Added action to history, transitioning to '{exec_res['tool']}'")
        return exec_res["tool"]


class ReadFileActionNode(Node):
    """Reads a file and stores content in history."""
    
    def prep(self, shared):
        last_action = shared["history"][-1]
        target_file = last_action["params"].get("target_file", "")
        working_dir = shared["working_dir"]
        
        logger.info(f"ReadFileAction: Preparing to read file '{target_file}' in directory '{working_dir}'")
        return {"target_file": target_file, "working_dir": working_dir}
    
    def exec(self, prep_res):
        logger.info(f"ReadFileAction: Reading file '{prep_res['target_file']}'")
        success, content = read_file(prep_res["target_file"], prep_res["working_dir"])
        
        if success:
            logger.info(f"ReadFileAction: Successfully read file '{prep_res['target_file']}' ({len(content)} characters)")
        else:
            logger.error(f"ReadFileAction: Failed to read file '{prep_res['target_file']}': {content}")
        
        return {"success": success, "content": content, "file_path": prep_res["target_file"]}
    
    def post(self, shared, prep_res, exec_res):
        # Update last history entry with result
        shared["history"][-1]["result"] = exec_res
        logger.info("ReadFileAction: Updated history with result, returning to main agent")
        return "decide_next"


class GrepSearchActionNode(Node):
    """Performs grep search and stores results in history."""
    
    def prep(self, shared):
        last_action = shared["history"][-1]
        params = last_action["params"]
        working_dir = shared["working_dir"]
        
        search_params = {
            "query": params.get("query", ""),
            "case_sensitive": params.get("case_sensitive", False),
            "include_pattern": params.get("include_pattern"),
            "exclude_pattern": params.get("exclude_pattern"),
            "working_dir": working_dir
        }
        
        logger.info(f"GrepSearchAction: Preparing search for '{search_params['query']}' in '{working_dir}'")
        if search_params["include_pattern"]:
            logger.info(f"GrepSearchAction: Include pattern: {search_params['include_pattern']}")
        if search_params["exclude_pattern"]:
            logger.info(f"GrepSearchAction: Exclude pattern: {search_params['exclude_pattern']}")
        
        return search_params
    
    def exec(self, search_params):
        logger.info(f"GrepSearchAction: Executing search for '{search_params['query']}'")
        success, matches = grep_search(**search_params)
        
        if success:
            logger.info(f"GrepSearchAction: Search completed successfully, found {len(matches)} matches")
        else:
            logger.error(f"GrepSearchAction: Search failed: {matches}")
        
        return {"success": success, "matches": matches, "query": search_params["query"]}
    
    def post(self, shared, prep_res, exec_res):
        shared["history"][-1]["result"] = exec_res
        logger.info("GrepSearchAction: Updated history with search results, returning to main agent")
        return "decide_next"


class ListDirectoryActionNode(Node):
    """Lists directory contents with tree visualization."""
    
    def prep(self, shared):
        last_action = shared["history"][-1]
        dir_path = last_action["params"].get("relative_workspace_path", ".")
        working_dir = shared["working_dir"]
        
        logger.info(f"ListDirectoryAction: Preparing to list directory '{dir_path}' in '{working_dir}'")
        return {"dir_path": dir_path, "working_dir": working_dir}
    
    def exec(self, prep_res):
        logger.info(f"ListDirectoryAction: Listing directory '{prep_res['dir_path']}'")
        success, tree_str = list_dir(prep_res["dir_path"], prep_res["working_dir"])
        
        if success:
            logger.info(f"ListDirectoryAction: Successfully listed directory")
        else:
            logger.error(f"ListDirectoryAction: Failed to list directory: {tree_str}")
        
        return {"success": success, "tree_visualization": tree_str}
    
    def post(self, shared, prep_res, exec_res):
        shared["history"][-1]["result"] = exec_res
        logger.info("ListDirectoryAction: Updated history with directory listing, returning to main agent")
        return "decide_next"


class DeleteFileActionNode(Node):
    """Deletes a file."""
    
    def prep(self, shared):
        last_action = shared["history"][-1]
        target_file = last_action["params"].get("target_file", "")
        working_dir = shared["working_dir"]
        
        logger.info(f"DeleteFileAction: Preparing to delete file '{target_file}' in directory '{working_dir}'")
        return {"target_file": target_file, "working_dir": working_dir}
    
    def exec(self, prep_res):
        logger.info(f"DeleteFileAction: Deleting file '{prep_res['target_file']}'")
        success, message = delete_file(prep_res["target_file"], prep_res["working_dir"])
        
        if success:
            logger.info(f"DeleteFileAction: Successfully deleted file '{prep_res['target_file']}'")
        else:
            logger.error(f"DeleteFileAction: Failed to delete file '{prep_res['target_file']}': {message}")
        
        return {"success": success, "message": message, "file_path": prep_res["target_file"]}
    
    def post(self, shared, prep_res, exec_res):
        shared["history"][-1]["result"] = exec_res
        logger.info("DeleteFileAction: Updated history with deletion result, returning to main agent")
        return "decide_next"


class ReadTargetFileNode(Node):
    """First step in edit process - reads the target file."""
    
    def prep(self, shared):
        last_action = shared["history"][-1]
        target_file = last_action["params"].get("target_file", "")
        working_dir = shared["working_dir"]
        
        logger.info(f"EditAgent-ReadTarget: Starting edit process for file '{target_file}'")
        return {"target_file": target_file, "working_dir": working_dir}
    
    def exec(self, prep_res):
        logger.info(f"EditAgent-ReadTarget: Reading target file '{prep_res['target_file']}'")
        success, content = read_file(prep_res["target_file"], prep_res["working_dir"])
        
        if success:
            logger.info(f"EditAgent-ReadTarget: Successfully read target file ({len(content)} characters)")
        else:
            logger.error(f"EditAgent-ReadTarget: Failed to read target file: {content}")
        
        return {"success": success, "content": content, "file_path": prep_res["target_file"]}
    
    def post(self, shared, prep_res, exec_res):
        # Store file content for edit planning
        shared["history"][-1]["file_content"] = exec_res["content"]
        shared["history"][-1]["file_success"] = exec_res["success"]
        
        if exec_res["success"]:
            logger.info("EditAgent-ReadTarget: File read successful, proceeding to analyze and plan")
            return "analyze_plan"
        else:
            # File read failed, update result and return to main decision
            shared["history"][-1]["result"] = exec_res
            logger.error("EditAgent-ReadTarget: File read failed, returning to main agent")
            return "decide_next"


class AnalyzeAndPlanChangesNode(Node):
    """Analyzes edit instructions and creates specific edit plan."""
    
    def prep(self, shared):
        last_action = shared["history"][-1]
        file_content = last_action.get("file_content", "")
        instructions = last_action["params"].get("instructions", "")
        code_edit = last_action["params"].get("code_edit", "")
        
        logger.info(f"EditAgent-Analyze: Planning edits based on instructions: '{instructions[:100]}...'")
        logger.info(f"EditAgent-Analyze: File content length: {len(file_content)} characters")
        
        return {
            "file_content": file_content,
            "instructions": instructions,
            "code_edit": code_edit
        }
    
    def exec(self, prep_res):
        logger.info("EditAgent-Analyze: Calling LLM to analyze and plan specific edits")
        
        prompt = f"""You need to analyze the edit instructions and create a specific edit plan.

CURRENT FILE CONTENT:
```
{prep_res['file_content']}
```

EDIT INSTRUCTIONS: {prep_res['instructions']}

CODE EDIT TEMPLATE:
```
{prep_res['code_edit']}
```

Create a plan to apply these edits. Return a list of specific edit operations in YAML format.
Each edit should specify the exact line numbers and replacement content.

IMPORTANT:
- Line numbers are 1-indexed
- If inserting new content, use the same start_line and end_line
- If deleting lines, set replacement to empty string
- For replacements, specify the exact range to replace

Output format:
```yaml
edits:
  - start_line: 1
    end_line: 3
    replacement: |
      new content here
      can be multiple lines
  - start_line: 10
    end_line: 10
    replacement: "single line replacement"
```"""

        response = call_llm(prompt)
        
        try:
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            result = yaml.safe_load(yaml_str)
            edits = result.get("edits", [])
            logger.info(f"EditAgent-Analyze: Successfully parsed edit plan with {len(edits)} operations")
        except Exception as e:
            logger.error(f"EditAgent-Analyze: Failed to parse edit plan: {e}")
            edits = []
        
        # Validate and sort edits (descending order by start_line)
        valid_edits = []
        for edit in edits:
            if all(key in edit for key in ["start_line", "end_line", "replacement"]):
                valid_edits.append(edit)
                logger.info(f"EditAgent-Analyze: Valid edit - lines {edit['start_line']}-{edit['end_line']}")
            else:
                logger.warning(f"EditAgent-Analyze: Invalid edit skipped: {edit}")
        
        # Sort in descending order by start_line for safe application
        valid_edits.sort(key=lambda x: x["start_line"], reverse=True)
        logger.info(f"EditAgent-Analyze: Sorted {len(valid_edits)} valid edits for application")
        
        return valid_edits
    
    def post(self, shared, prep_res, exec_res):
        shared["edit_operations"] = exec_res
        logger.info(f"EditAgent-Analyze: Stored {len(exec_res)} edit operations, proceeding to apply changes")
        return "apply_changes"


class ApplyChangesBatchNode(BatchNode):
    """Applies the planned edits to the file."""
    
    def prep(self, shared):
        edit_operations = shared.get("edit_operations", [])
        last_action = shared["history"][-1]
        target_file = last_action["params"].get("target_file", "")
        working_dir = shared["working_dir"]
        
        logger.info(f"EditAgent-Apply: Preparing to apply {len(edit_operations)} edits to '{target_file}'")
        
        # Add target_file and working_dir to each edit operation for exec()
        enhanced_operations = []
        for i, op in enumerate(edit_operations):
            enhanced_op = op.copy()
            enhanced_op["target_file"] = target_file
            enhanced_op["working_dir"] = working_dir
            enhanced_operations.append(enhanced_op)
            logger.info(f"EditAgent-Apply: Edit {i+1}: lines {op['start_line']}-{op['end_line']}")
        
        return enhanced_operations
    
    def exec(self, edit_operation):
        # Note: BatchNode exec() doesn't have access to shared, so we need to pass the data through prep
        # This is a limitation we need to work around
        start_line = edit_operation["start_line"]
        end_line = edit_operation["end_line"]
        replacement = edit_operation["replacement"]
        target_file = edit_operation["target_file"]
        working_dir = edit_operation["working_dir"]
        
        logger.info(f"EditAgent-Apply: Applying edit to lines {start_line}-{end_line} in '{target_file}'")
        success, message = replace_file(target_file, start_line, end_line, replacement, working_dir)
        
        if success:
            logger.info(f"EditAgent-Apply: Successfully applied edit to lines {start_line}-{end_line}")
        else:
            logger.error(f"EditAgent-Apply: Failed to apply edit to lines {start_line}-{end_line}: {message}")
        
        return {"success": success, "message": message, "edit": edit_operation}
    
    def post(self, shared, prep_res, exec_res_list):
        # Compile edit results
        all_success = all(result["success"] for result in exec_res_list)
        edit_summary = {
            "success": all_success,
            "total_edits": len(exec_res_list),
            "successful_edits": sum(1 for result in exec_res_list if result["success"]),
            "details": exec_res_list
        }
        
        # Update history with edit result
        shared["history"][-1]["result"] = edit_summary
        
        # Clear edit operations
        shared["edit_operations"] = []
        
        logger.info(f"EditAgent-Apply: Edit process complete - {edit_summary['successful_edits']}/{edit_summary['total_edits']} edits successful")
        if all_success:
            logger.info("EditAgent-Apply: All edits applied successfully, returning to main agent")
        else:
            logger.warning("EditAgent-Apply: Some edits failed, returning to main agent")
        
        return "decide_next"


class FormatResponseNode(Node):
    """Creates final response for user based on action history."""
    
    def prep(self, shared):
        history = shared.get("history", [])
        user_query = shared["user_query"]
        
        logger.info(f"FormatResponse: Generating final response for user query: '{user_query}'")
        logger.info(f"FormatResponse: Processing {len(history)} completed actions")
        
        return {"history": history, "user_query": user_query}
    
    def exec(self, prep_res):
        logger.info("FormatResponse: Calling LLM to generate final response")
        
        prompt = f"""Create a helpful response to the user based on the completed actions.

ORIGINAL USER REQUEST: {prep_res['user_query']}

ACTIONS COMPLETED:
"""
        
        for i, action in enumerate(prep_res['history'], 1):
            prompt += f"\n{i}. {action['tool']} - {action['reason']}\n"
            
            if action.get('result'):
                result = action['result']
                if action['tool'] == 'read_file':
                    if result.get('success'):
                        content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                        prompt += f"   ✓ Successfully read file. Content preview: {content_preview}\n"
                    else:
                        prompt += f"   ✗ Failed to read file: {result.get('content', 'Unknown error')}\n"
                        
                elif action['tool'] == 'grep_search':
                    if result.get('success'):
                        matches = result.get('matches', [])
                        prompt += f"   ✓ Found {len(matches)} matches for '{result['query']}'\n"
                        for match in matches[:3]:  # Show first 3 matches
                            prompt += f"     - {match['file']}:{match['line']} {match['content'][:50]}...\n"
                    else:
                        prompt += f"   ✗ Search failed\n"
                        
                elif action['tool'] == 'list_dir':
                    if result.get('success'):
                        prompt += f"   ✓ Listed directory contents\n"
                    else:
                        prompt += f"   ✗ Failed to list directory\n"
                        
                elif action['tool'] == 'edit_file':
                    if result.get('success'):
                        prompt += f"   ✓ Successfully applied {result['successful_edits']}/{result['total_edits']} edits\n"
                    else:
                        prompt += f"   ✗ Edit failed: {result.get('details', 'Unknown error')}\n"
                        
                elif action['tool'] == 'delete_file':
                    if result.get('success'):
                        prompt += f"   ✓ Successfully deleted file\n"
                    else:
                        prompt += f"   ✗ Failed to delete file: {result.get('message', 'Unknown error')}\n"

        prompt += f"""

Provide a clear, helpful summary of what was accomplished. Be specific about:
- What files were read, modified, or created
- What searches were performed and their results  
- Any issues encountered
- Next steps if applicable

Keep the response concise but informative."""

        response = call_llm(prompt)
        logger.info("FormatResponse: Successfully generated final response")
        return response
    
    def post(self, shared, prep_res, exec_res):
        shared["response"] = exec_res
        logger.info("FormatResponse: Final response stored, marking task as complete")
        return "done"

# Legacy nodes for backward compatibility
class GetQuestionNode(Node):
    """Legacy node - gets user input directly."""
    
    def exec(self, _):
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        shared["question"] = exec_res
        return "default"

class AnswerNode(Node):
    """Legacy node - answers questions using LLM."""
    
    def prep(self, shared):
        return shared["question"]
    
    def exec(self, question):
        return call_llm(question)
    
    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        return "default"