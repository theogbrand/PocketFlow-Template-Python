import os
import logging
from typing import Tuple

def read_file(target_file: str, working_dir: str = ".") -> Tuple[bool, str]:
    """
    Reads content from specified files
    
    Args:
        target_file: Path to the file (relative to working_dir)
        working_dir: Base directory for relative paths
        
    Returns:
        Tuple of (success_status, file_content_or_error_message)
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
        
        # Read the file
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logging.info(f"Successfully read file: {target_file}")
        return True, content
        
    except PermissionError:
        error_msg = f"Error: Permission denied reading {target_file}"
        logging.error(error_msg)
        return False, error_msg
    except UnicodeDecodeError:
        error_msg = f"Error: Cannot decode {target_file} as UTF-8"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error reading {target_file}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def get_file_info(target_file: str, working_dir: str = ".") -> Tuple[bool, dict]:
    """
    Gets file information (size, modification time, etc.)
    
    Args:
        target_file: Path to the file (relative to working_dir)
        working_dir: Base directory for relative paths
        
    Returns:
        Tuple of (success_status, file_info_dict_or_error_message)
    """
    try:
        abs_path = os.path.abspath(os.path.join(working_dir, target_file))
        abs_working_dir = os.path.abspath(working_dir)
        
        if not abs_path.startswith(abs_working_dir):
            return False, {"error": f"Path {target_file} is outside working directory"}
        
        if not os.path.exists(abs_path):
            return False, {"error": f"File {target_file} does not exist"}
        
        stat_info = os.stat(abs_path)
        file_info = {
            "size": stat_info.st_size,
            "modified": stat_info.st_mtime,
            "is_file": os.path.isfile(abs_path),
            "is_dir": os.path.isdir(abs_path),
            "permissions": oct(stat_info.st_mode)[-3:]
        }
        
        return True, file_info
        
    except Exception as e:
        return False, {"error": str(e)}

if __name__ == "__main__":
    # Test the function
    success, content = read_file("README.md", ".")
    if success:
        print(f"File content preview: {content[:200]}...")
    else:
        print(f"Error: {content}") 