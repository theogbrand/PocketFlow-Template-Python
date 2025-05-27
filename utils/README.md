# Coding Agent Utility Functions

This directory contains utility functions that provide the "body" for the coding agent's "brain" - enabling it to interact with files, search code, and communicate with language models.

## Overview

All utility functions follow these principles:
- **Relative Path Support**: All file paths are interpreted relative to a `working_dir` parameter
- **Security**: Path traversal protection to prevent access outside working directory
- **Error Handling**: Robust error handling with descriptive error messages
- **Return Format**: Consistent `(bool, result)` tuple format for success/failure indication

## Core Utilities

### 1. LLM Wrapper (`call_llm.py`)

**Purpose**: Interface with language model APIs

**Functions**:
- `call_llm(prompt, model="gpt-4o")` - Basic LLM call
- `call_llm_with_retries(prompt, max_retries=3)` - LLM call with retry logic

**Usage**:
```python
from utils.call_llm import call_llm

response = call_llm("Explain this code: def hello(): print('hi')")
print(response)
```

**Requirements**: Set `OPENAI_API_KEY` environment variable

### 2. File Reading (`read_file.py`)

**Purpose**: Read file contents and metadata

**Functions**:
- `read_file(target_file, working_dir=".")` - Read entire file content
- `get_file_info(target_file, working_dir=".")` - Get file metadata (size, permissions, etc.)

**Usage**:
```python
from utils.read_file import read_file

success, content = read_file("main.py", "/path/to/project")
if success:
    print(f"File content: {content}")
else:
    print(f"Error: {content}")
```

### 3. File Editing (`replace_file.py`)

**Purpose**: Modify file contents

**Functions**:
- `replace_file(target_file, start_line, end_line, new_content, working_dir=".")` - Replace lines in file
- `insert_file(target_file, content, line_number=None, working_dir=".")` - Insert content at specific line or append

**Usage**:
```python
from utils.replace_file import replace_file, insert_file

# Replace lines 5-7 with new content
success, msg = replace_file("app.py", 5, 7, "# New code here\n", "/project")

# Insert at line 10
success, msg = insert_file("app.py", "new_function()\n", 10, "/project")
```

### 4. File Deletion (`delete_file.py`)

**Purpose**: Delete files and remove content

**Functions**:
- `delete_file(target_file, working_dir=".")` - Delete entire file
- `remove_file_content(target_file, start_line=None, end_line=None, working_dir=".")` - Remove specific lines

**Usage**:
```python
from utils.delete_file import delete_file, remove_file_content

# Delete entire file
success, msg = delete_file("temp.txt", "/project")

# Remove lines 10-20
success, msg = remove_file_content("app.py", 10, 20, "/project")
```

### 5. Search Operations (`search_ops.py`)

**Purpose**: Search for patterns in files

**Functions**:
- `grep_search(query, case_sensitive=True, include_pattern=None, exclude_pattern=None, working_dir=".")` - Search across multiple files
- `search_in_file(file_path, query, working_dir=".")` - Search in specific file

**Usage**:
```python
from utils.search_ops import grep_search, search_in_file

# Search for function definitions in Python files
success, matches = grep_search("def ", include_pattern="*.py", working_dir="/project")
for match in matches:
    print(f"{match['file_path']}:{match['line_number']} - {match['content']}")

# Search in specific file
success, matches = search_in_file("main.py", "import", "/project")
```

**Match Format**:
```python
{
    "file_path": "relative/path/to/file.py",
    "line_number": 42,
    "content": "def example_function():",
    "match_text": "def ",
    "match_start": 0,
    "match_end": 4
}
```

### 6. Directory Operations (`dir_ops.py`)

**Purpose**: Navigate and analyze directory structure

**Functions**:
- `list_dir(relative_workspace_path, working_dir=".")` - Generate tree visualization
- `get_directory_stats(relative_workspace_path, working_dir=".")` - Get directory statistics

**Usage**:
```python
from utils.dir_ops import list_dir, get_directory_stats

# Get tree visualization
success, tree = list_dir("src", "/project")
if success:
    print(tree)

# Get directory stats
success, stats = get_directory_stats(".", "/project")
print(f"Files: {stats['file_count']}, Size: {stats['total_size_formatted']}")
```

## Security Features

All utilities implement security measures:

1. **Path Traversal Protection**: Prevents access to files outside the working directory
2. **Input Validation**: Validates file paths, line numbers, and other parameters
3. **Permission Handling**: Graceful handling of permission denied errors
4. **Binary File Detection**: Skips binary files in search operations

## Error Handling

All functions return a tuple `(success: bool, result: Any)` where:
- `success=True`: Operation succeeded, `result` contains the actual result
- `success=False`: Operation failed, `result` contains error message

## Testing

Run the test suite to verify all utilities work correctly:

```bash
python test_utils.py
```

This will test all utility functions with temporary files and directories.

## Integration with PocketFlow

These utilities are designed to be used within PocketFlow nodes:

```python
from pocketflow import Node
from utils.read_file import read_file

class ReadFileNode(Node):
    def prep(self, shared):
        return shared["file_path"]
    
    def exec(self, file_path):
        success, content = read_file(file_path, shared["working_dir"])
        if not success:
            raise Exception(content)
        return content
    
    def post(self, shared, prep_res, exec_res):
        shared["file_content"] = exec_res
```

## Dependencies

- `openai>=1.0.0` - For LLM API calls
- `pyyaml>=6.0` - For YAML parsing (structured output)
- Standard library modules: `os`, `re`, `logging`, `tempfile`, etc.

Install dependencies:
```bash
pip install -r requirements.txt
``` 