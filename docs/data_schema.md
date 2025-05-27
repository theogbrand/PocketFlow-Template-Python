# Data Schema Documentation

## Shared Memory Structure

The coding agent uses a structured shared memory dictionary to maintain state across all nodes. Here's the complete schema:

```python
shared = {
    # === CORE CONFIGURATION ===
    "user_query": str,           # Original user request/query
    "working_dir": str,          # Base directory for all file operations
    
    # === ACTION HISTORY ===
    "history": [
        {
            "tool": str,             # Tool name: "read_file", "edit_file", "delete_file", "grep_search", "list_dir", "finish"
            "reason": str,           # Human-readable explanation for why this tool was chosen
            "params": dict,          # Tool-specific parameters (see below for details)
            "result": any,           # Tool execution result (populated by action nodes)
            "timestamp": str,        # ISO format timestamp when action was initiated
            
            # === EDIT-SPECIFIC FIELDS (only for edit_file actions) ===
            "file_content": str,     # File content read during edit process
            "file_success": bool,    # Whether file read was successful
        }
    ],
    
    # === TEMPORARY EDIT STATE ===
    "edit_operations": [
        {
            "start_line": int,       # 1-indexed line number to start replacement
            "end_line": int,         # 1-indexed line number to end replacement  
            "replacement": str       # New content to insert (can be multi-line)
        }
    ],
    
    # === FINAL OUTPUT ===
    "response": str              # Final formatted response to return to user
}
```

## Parameter Schemas by Tool

### read_file
```python
"params": {
    "target_file": str,         # File path (relative to working_dir)
    "explanation": str          # Reason for reading this file
}
```

### edit_file  
```python
"params": {
    "target_file": str,         # File path (relative to working_dir)
    "instructions": str,        # High-level description of what to change
    "code_edit": str,          # Template/example of the desired changes
    "explanation": str          # Reason for editing this file
}
```

### delete_file
```python
"params": {
    "target_file": str,         # File path (relative to working_dir)
    "explanation": str          # Reason for deleting this file
}
```

### grep_search
```python
"params": {
    "query": str,              # Search pattern/text
    "case_sensitive": bool,    # Optional: Whether search is case-sensitive
    "include_pattern": str,    # Optional: File pattern to include (e.g., "*.py")
    "exclude_pattern": str,    # Optional: File pattern to exclude (e.g., "*.log")
    "explanation": str         # Reason for performing this search
}
```

### list_dir
```python
"params": {
    "relative_workspace_path": str,  # Directory path (relative to working_dir)
    "explanation": str               # Reason for listing this directory
}
```

## Result Schemas by Tool

### read_file result
```python
"result": {
    "success": bool,           # Whether file was successfully read
    "content": str,            # File content (or error message if failed)
    "file_path": str          # Absolute path that was read
}
```

### edit_file result
```python
"result": {
    "success": bool,                # Whether all edits were successful
    "total_edits": int,            # Total number of edit operations attempted
    "successful_edits": int,       # Number of edit operations that succeeded
    "details": [                   # List of individual edit results
        {
            "success": bool,       # Whether this specific edit succeeded
            "message": str,        # Success/error message
            "edit": {              # The edit operation that was attempted
                "start_line": int,
                "end_line": int,
                "replacement": str
            }
        }
    ]
}
```

### delete_file result
```python
"result": {
    "success": bool,           # Whether file was successfully deleted
    "message": str,            # Success/error message
    "file_path": str          # Absolute path that was deleted
}
```

### grep_search result
```python
"result": {
    "success": bool,           # Whether search completed successfully
    "matches": [               # List of search matches
        {
            "file": str,       # File path where match was found
            "line": int,       # Line number of the match
            "content": str     # Content of the matching line
        }
    ],
    "query": str              # The search query that was used
}
```

### list_dir result
```python
"result": {
    "success": bool,           # Whether directory listing succeeded
    "tree_visualization": str  # Tree-formatted string showing directory structure
}
```

## Data Flow Examples

### Example 1: Simple File Read
```python
# Initial state
shared = {
    "user_query": "Show me the contents of app.py",
    "working_dir": "/project/src",
    "history": []
}

# After MainDecisionAgentNode
shared["history"] = [
    {
        "tool": "read_file",
        "reason": "User wants to see the contents of app.py",
        "params": {
            "target_file": "app.py",
            "explanation": "Reading file content as requested by user"
        },
        "result": None,
        "timestamp": "2024-01-15T10:30:00Z"
    }
]

# After ReadFileActionNode
shared["history"][0]["result"] = {
    "success": True,
    "content": "import flask\n\napp = flask.Flask(__name__)\n...",
    "file_path": "/project/src/app.py"
}
```

### Example 2: File Edit Process
```python
# After MainDecisionAgentNode (edit_file)
shared["history"] = [
    {
        "tool": "edit_file", 
        "reason": "Add logging to the main function",
        "params": {
            "target_file": "main.py",
            "instructions": "Add import logging and setup basic logging",
            "code_edit": "import logging\nlogging.basicConfig(level=logging.INFO)"
        },
        "result": None,
        "timestamp": "2024-01-15T10:30:00Z"
    }
]

# After ReadTargetFileNode
shared["history"][0]["file_content"] = "def main():\n    print('Hello')\n\nif __name__ == '__main__':\n    main()"
shared["history"][0]["file_success"] = True

# After AnalyzeAndPlanChangesNode  
shared["edit_operations"] = [
    {
        "start_line": 1,
        "end_line": 1, 
        "replacement": "import logging\n\ndef main():"
    }
]

# After ApplyChangesBatchNode
shared["history"][0]["result"] = {
    "success": True,
    "total_edits": 1,
    "successful_edits": 1,
    "details": [...]
}
shared["edit_operations"] = []  # Cleared after use
```

## Path Handling

All file paths in the system follow these rules:

1. **Input paths**: Can be relative or absolute
2. **Storage**: Relative paths are stored as-is in `params`
3. **Processing**: All paths are converted to absolute by joining with `working_dir`
4. **Output**: Absolute paths are returned in results for clarity

Example:
```python
# User provides: "src/main.py"
# working_dir: "/project"
# Stored in params: "src/main.py" 
# Used by utilities: "/project/src/main.py"
# Returned in result: "/project/src/main.py"
``` 