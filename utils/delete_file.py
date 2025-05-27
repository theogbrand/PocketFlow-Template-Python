import os
import logging
from typing import Tuple

def delete_file(target_file: str, working_dir: str = ".") -> Tuple[bool, str]:
    """
    Deletes a file from the file system
    
    Args:
        target_file: Path to the file (relative to working_dir)
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
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(abs_path):
            return False, f"Error: {target_file} is not a file (it may be a directory)"
        
        # Delete the file
        os.remove(abs_path)
        
        success_msg = f"Successfully deleted file: {target_file}"
        logging.info(success_msg)
        return True, success_msg
        
    except PermissionError:
        error_msg = f"Error: Permission denied deleting {target_file}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error deleting {target_file}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def remove_file_content(target_file: str, start_line: int = None, end_line: int = None, working_dir: str = ".") -> Tuple[bool, str]:
    """
    Removes content from a file based on line numbers
    
    Args:
        target_file: Path to the file (relative to working_dir)
        start_line: First line to remove (1-indexed). If None, remove from beginning
        end_line: Last line to remove (1-indexed, inclusive). If None, remove to end
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
        
        total_lines = len(lines)
        
        # Handle default values
        if start_line is None:
            start_line = 1
        if end_line is None:
            end_line = total_lines
        
        # Validate line numbers
        if start_line < 1 or start_line > total_lines:
            return False, f"Error: start_line {start_line} is out of range (1-{total_lines})"
        
        if end_line < 1 or end_line > total_lines:
            return False, f"Error: end_line {end_line} is out of range (1-{total_lines})"
        
        if start_line > end_line:
            return False, f"Error: start_line {start_line} cannot be greater than end_line {end_line}"
        
        # Convert to 0-indexed for list operations
        start_idx = start_line - 1
        end_idx = end_line  # end_line is inclusive, so we don't subtract 1
        
        # Create new file content by removing specified lines
        new_lines = lines[:start_idx] + lines[end_idx:]
        
        # Write back to file
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        if start_line == 1 and end_line == total_lines:
            success_msg = f"Successfully cleared all content from {target_file}"
        else:
            success_msg = f"Successfully removed lines {start_line}-{end_line} from {target_file}"
        
        logging.info(success_msg)
        return True, success_msg
        
    except PermissionError:
        error_msg = f"Error: Permission denied writing to {target_file}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error removing content from {target_file}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

if __name__ == "__main__":
    # Test the functions
    test_file = "test_delete.txt"
    
    # Create test file
    with open(test_file, 'w') as f:
        f.write("Line 1\nLine 2\nLine 3\nLine 4\n")
    
    # Test removing lines
    success, msg = remove_file_content(test_file, 2, 3)
    print(f"Remove lines: {msg}")
    
    # Test deleting file
    success, msg = delete_file(test_file)
    print(f"Delete file: {msg}") 