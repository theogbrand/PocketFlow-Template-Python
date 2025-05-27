import os
import logging
from typing import Tuple

def list_dir(relative_workspace_path: str, working_dir: str = ".") -> Tuple[bool, str]:
    """
    Lists contents of a directory with a tree visualization
    
    Args:
        relative_workspace_path: Path to list contents of (relative to working_dir)
        working_dir: Base directory for relative paths
        
    Returns:
        Tuple of (success_status, tree_visualization_string)
    """
    try:
        # Handle root directory case
        if relative_workspace_path in [".", "", "/"]:
            target_path = working_dir
        else:
            target_path = os.path.join(working_dir, relative_workspace_path)
        
        abs_path = os.path.abspath(target_path)
        abs_working_dir = os.path.abspath(working_dir)
        
        # Security check: ensure the path is within working_dir
        if not abs_path.startswith(abs_working_dir):
            return False, f"Error: Path {relative_workspace_path} is outside working directory"
        
        # Check if directory exists
        if not os.path.exists(abs_path):
            return False, f"Error: Directory {relative_workspace_path} does not exist"
        
        # Check if it's actually a directory
        if not os.path.isdir(abs_path):
            return False, f"Error: {relative_workspace_path} is not a directory"
        
        # Generate tree visualization
        tree_str = _generate_tree(abs_path, relative_workspace_path or ".")
        
        return True, tree_str
        
    except PermissionError:
        error_msg = f"Error: Permission denied accessing {relative_workspace_path}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error listing directory {relative_workspace_path}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def _generate_tree(directory_path: str, display_name: str, max_depth: int = 3, max_items: int = 50) -> str:
    """
    Generate a tree visualization of directory contents
    
    Args:
        directory_path: Absolute path to the directory
        display_name: Name to display for the root
        max_depth: Maximum depth to traverse
        max_items: Maximum total items to show
        
    Returns:
        String representation of the directory tree
    """
    lines = []
    item_count = 0
    
    def _walk_directory(path: str, prefix: str = "", depth: int = 0) -> None:
        nonlocal item_count
        
        if depth > max_depth or item_count >= max_items:
            return
        
        try:
            # Get directory contents
            items = os.listdir(path)
            
            # Filter out hidden files and common ignore patterns
            filtered_items = []
            for item in items:
                if not item.startswith('.'):  # Skip hidden files
                    if item not in {'__pycache__', 'node_modules', '.git', 'venv', 'env', '.vscode', '.idea'}:
                        filtered_items.append(item)
            
            # Sort items: directories first, then files
            dirs = []
            files = []
            for item in filtered_items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            sorted_items = sorted(dirs) + sorted(files)
            
            # Limit items shown if too many
            if len(sorted_items) > 20:
                sorted_items = sorted_items[:20]
                show_truncated = True
            else:
                show_truncated = False
            
            for i, item in enumerate(sorted_items):
                if item_count >= max_items:
                    break
                
                item_path = os.path.join(path, item)
                is_last = (i == len(sorted_items) - 1) and not show_truncated
                
                # Choose the appropriate tree characters
                if is_last:
                    current_prefix = f"{prefix}└── "
                    next_prefix = f"{prefix}    "
                else:
                    current_prefix = f"{prefix}├── "
                    next_prefix = f"{prefix}│   "
                
                # Add file/directory info
                if os.path.isdir(item_path):
                    lines.append(f"{current_prefix}{item}/")
                    item_count += 1
                    
                    # Recursively process subdirectory
                    if depth < max_depth and item_count < max_items:
                        _walk_directory(item_path, next_prefix, depth + 1)
                else:
                    # Show file with size info
                    try:
                        size = os.path.getsize(item_path)
                        size_str = _format_file_size(size)
                        lines.append(f"{current_prefix}{item} ({size_str})")
                    except:
                        lines.append(f"{current_prefix}{item}")
                    item_count += 1
            
            # Show truncation message if needed
            if show_truncated:
                lines.append(f"{prefix}... ({len(filtered_items) - 20} more items)")
                
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")
        except Exception as e:
            lines.append(f"{prefix}[Error: {str(e)}]")
    
    # Start with the root directory
    lines.append(f"{display_name}/")
    _walk_directory(directory_path)
    
    # Add summary
    if item_count >= max_items:
        lines.append(f"\n... (showing first {max_items} items)")
    
    return "\n".join(lines)

def _format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    if i >= len(size_names):
        i = len(size_names) - 1
    
    p = math.pow(1024, i)
    s = round(size_bytes / p, 1)
    
    # Remove .0 for whole numbers
    if s == int(s):
        s = int(s)
    
    return f"{s} {size_names[i]}"

def get_directory_stats(relative_workspace_path: str, working_dir: str = ".") -> Tuple[bool, dict]:
    """
    Get statistics about a directory (file count, total size, etc.)
    
    Args:
        relative_workspace_path: Path to analyze (relative to working_dir)
        working_dir: Base directory for relative paths
        
    Returns:
        Tuple of (success_status, stats_dict_or_error)
    """
    try:
        if relative_workspace_path in [".", "", "/"]:
            target_path = working_dir
        else:
            target_path = os.path.join(working_dir, relative_workspace_path)
        
        abs_path = os.path.abspath(target_path)
        abs_working_dir = os.path.abspath(working_dir)
        
        if not abs_path.startswith(abs_working_dir):
            return False, {"error": f"Path {relative_workspace_path} is outside working directory"}
        
        if not os.path.exists(abs_path):
            return False, {"error": f"Directory {relative_workspace_path} does not exist"}
        
        if not os.path.isdir(abs_path):
            return False, {"error": f"{relative_workspace_path} is not a directory"}
        
        # Calculate stats
        file_count = 0
        dir_count = 0
        total_size = 0
        
        for root, dirs, files in os.walk(abs_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if not file.startswith('.'):
                    file_count += 1
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except:
                        pass  # Skip files we can't access
            
            dir_count += len(dirs)
        
        stats = {
            "file_count": file_count,
            "directory_count": dir_count,
            "total_size": total_size,
            "total_size_formatted": _format_file_size(total_size)
        }
        
        return True, stats
        
    except Exception as e:
        return False, {"error": str(e)}

if __name__ == "__main__":
    # Test the function
    success, tree = list_dir(".", ".")
    if success:
        print("Directory tree:")
        print(tree)
    else:
        print(f"Error: {tree}")
    
    # Test stats
    success, stats = get_directory_stats(".", ".")
    if success:
        print(f"\nDirectory stats: {stats}")
    else:
        print(f"Stats error: {stats}") 