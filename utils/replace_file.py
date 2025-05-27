import os
import logging
from typing import Tuple

def replace_file(target_file: str, start_line: int, end_line: int, new_content: str, working_dir: str = ".") -> Tuple[bool, str]:
    """
    Replaces content in a file based on line numbers
    
    Args:
        target_file: Path to the file (relative to working_dir)
        start_line: First line to replace (1-indexed)
        end_line: Last line to replace (1-indexed, inclusive)
        new_content: New content to insert
        working_dir: Base directory for relative paths
        
    Returns:
        Tuple of (success_status, result_message)
    """
    try:
        # Construct absolute path
        abs_path = os.path.abspath(os.path.join(working_dir, target_file))
        
        # Security check: ensure the path is within working_dir
        abs_working_dir = os.path.abspath(working_dir)
        if not abs_path.startswith(abs_working_dir):
            return False, f"Error: Path {target_file} is outside working directory"
        
        # Check if file exists
        if not os.path.exists(abs_path):
            return False, f"Error: File {target_file} does not exist"
        
        # Check if it's actually a file
        if not os.path.isfile(abs_path):
            return False, f"Error: {target_file} is not a file"
        
        # Read the current file content
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Validate line numbers
        total_lines = len(lines)
        if start_line < 1 or start_line > total_lines:
            return False, f"Error: start_line {start_line} is out of range (1-{total_lines})"
        
        if end_line < 1 or end_line > total_lines:
            return False, f"Error: end_line {end_line} is out of range (1-{total_lines})"
        
        if start_line > end_line:
            return False, f"Error: start_line {start_line} cannot be greater than end_line {end_line}"
        
        # Prepare new content - ensure it ends with newline if not empty
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'
        
        # Convert to 0-indexed for list operations
        start_idx = start_line - 1
        end_idx = end_line  # end_line is inclusive, so we don't subtract 1
        
        # Create new file content
        new_lines = lines[:start_idx] + [new_content] + lines[end_idx:]
        
        # Write back to file
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        success_msg = f"Successfully replaced lines {start_line}-{end_line} in {target_file}"
        logging.info(success_msg)
        return True, success_msg
        
    except PermissionError:
        error_msg = f"Error: Permission denied writing to {target_file}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error replacing content in {target_file}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def insert_file(target_file: str, content: str, line_number: int = None, working_dir: str = ".") -> Tuple[bool, str]:
    """
    Writes or inserts content to a target file
    
    Args:
        target_file: Path to the file (relative to working_dir)
        content: Content to insert
        line_number: Line number to insert at (1-indexed). If None, append to end
        working_dir: Base directory for relative paths
        
    Returns:
        Tuple of (success_status, result_message)
    """
    try:
        abs_path = os.path.abspath(os.path.join(working_dir, target_file))
        abs_working_dir = os.path.abspath(working_dir)
        
        if not abs_path.startswith(abs_working_dir):
            return False, f"Error: Path {target_file} is outside working directory"
        
        # Ensure content ends with newline
        if content and not content.endswith('\n'):
            content += '\n'
        
        # If file doesn't exist, create it
        if not os.path.exists(abs_path):
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Created new file {target_file} with content"
        
        # Read existing content
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Insert content
        if line_number is None:
            # Append to end
            lines.append(content)
            action = "appended to end of"
        else:
            # Insert at specific line
            if line_number < 1 or line_number > len(lines) + 1:
                return False, f"Error: line_number {line_number} is out of range (1-{len(lines) + 1})"
            
            lines.insert(line_number - 1, content)
            action = f"inserted at line {line_number} of"
        
        # Write back to file
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        success_msg = f"Successfully {action} {target_file}"
        logging.info(success_msg)
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Error inserting content to {target_file}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

if __name__ == "__main__":
    # Test the functions
    test_file = "test_replace.txt"
    
    # Create test file
    success, msg = insert_file(test_file, "Line 1\nLine 2\nLine 3\n")
    print(f"Create: {msg}")
    
    # Replace line 2
    success, msg = replace_file(test_file, 2, 2, "Modified Line 2")
    print(f"Replace: {msg}")
    
    # Clean up
    try:
        os.remove(test_file)
    except:
        pass 