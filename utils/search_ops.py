import os
import re
import logging
from typing import List, Dict, Tuple, Optional
import glob

def grep_search(
    query: str, 
    case_sensitive: bool = True, 
    include_pattern: Optional[str] = None, 
    exclude_pattern: Optional[str] = None,
    working_dir: str = "."
) -> Tuple[bool, List[Dict[str, any]]]:
    """
    Searches through files for specific patterns using ripgrep-like functionality
    
    Args:
        query: The regex pattern to search for
        case_sensitive: Whether the search should be case sensitive
        include_pattern: Glob pattern for files to include (e.g. '*.py')
        exclude_pattern: Glob pattern for files to exclude
        working_dir: Base directory for the search
        
    Returns:
        Tuple of (success_status, list_of_matches)
        Each match is a dict with: {file_path, line_number, content, match_text}
    """
    try:
        abs_working_dir = os.path.abspath(working_dir)
        
        # Security check
        if not os.path.exists(abs_working_dir):
            return False, [{"error": f"Working directory {working_dir} does not exist"}]
        
        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error as e:
            return False, [{"error": f"Invalid regex pattern '{query}': {str(e)}"}]
        
        matches = []
        
        # Get list of files to search
        files_to_search = _get_files_to_search(
            abs_working_dir, include_pattern, exclude_pattern
        )
        
        # Search through files
        for file_path in files_to_search[:100]:  # Limit to 100 files for performance
            try:
                rel_path = os.path.relpath(file_path, abs_working_dir)
                file_matches = _search_file(file_path, pattern, rel_path)
                matches.extend(file_matches)
                
                # Cap results at 50 matches as specified
                if len(matches) >= 50:
                    matches = matches[:50]
                    break
                    
            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read
                continue
            except Exception as e:
                logging.warning(f"Error searching file {file_path}: {str(e)}")
                continue
        
        return True, matches
        
    except Exception as e:
        error_msg = f"Error during search: {str(e)}"
        logging.error(error_msg)
        return False, [{"error": error_msg}]

def _get_files_to_search(working_dir: str, include_pattern: Optional[str], exclude_pattern: Optional[str]) -> List[str]:
    """
    Get list of files to search based on include/exclude patterns
    """
    files = []
    
    # Default to all files if no include pattern specified
    if include_pattern:
        # Use glob to find files matching include pattern
        for root, dirs, filenames in os.walk(working_dir):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, working_dir)
                
                # Check include pattern
                if _matches_pattern(rel_path, include_pattern):
                    files.append(full_path)
    else:
        # Get all text files (common text file extensions)
        text_extensions = {'.txt', '.py', '.js', '.ts', '.html', '.css', '.md', '.json', '.xml', '.yaml', '.yml', '.sql', '.sh', '.bat', '.cfg', '.ini', '.log'}
        
        for root, dirs, filenames in os.walk(working_dir):
            # Skip hidden directories and common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'venv', 'env'}]
            
            for filename in filenames:
                if not filename.startswith('.'):  # Skip hidden files
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in text_extensions or not ext:  # Include files without extension
                        full_path = os.path.join(root, filename)
                        files.append(full_path)
    
    # Apply exclude pattern
    if exclude_pattern:
        files = [f for f in files if not _matches_pattern(
            os.path.relpath(f, working_dir), exclude_pattern
        )]
    
    return files

def _matches_pattern(filepath: str, pattern: str) -> bool:
    """
    Check if filepath matches glob pattern
    """
    try:
        # Convert glob pattern to regex
        import fnmatch
        return fnmatch.fnmatch(filepath, pattern)
    except:
        return False

def _search_file(file_path: str, pattern: re.Pattern, rel_path: str) -> List[Dict[str, any]]:
    """
    Search for pattern in a single file
    """
    matches = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line_matches = pattern.finditer(line.rstrip('\n\r'))
                for match in line_matches:
                    matches.append({
                        "file_path": rel_path,
                        "line_number": line_num,
                        "content": line.rstrip('\n\r'),
                        "match_text": match.group(),
                        "match_start": match.start(),
                        "match_end": match.end()
                    })
    except UnicodeDecodeError:
        # Skip binary files
        pass
    except Exception as e:
        logging.warning(f"Error reading file {file_path}: {str(e)}")
    
    return matches

def search_in_file(file_path: str, query: str, working_dir: str = ".") -> Tuple[bool, List[Dict[str, any]]]:
    """
    Search for a pattern in a specific file only
    
    Args:
        file_path: Path to the specific file to search
        query: The regex pattern to search for
        working_dir: Base directory for relative paths
        
    Returns:
        Tuple of (success_status, list_of_matches)
    """
    try:
        abs_path = os.path.abspath(os.path.join(working_dir, file_path))
        abs_working_dir = os.path.abspath(working_dir)
        
        # Security check
        if not abs_path.startswith(abs_working_dir):
            return False, [{"error": f"Path {file_path} is outside working directory"}]
        
        if not os.path.exists(abs_path):
            return False, [{"error": f"File {file_path} does not exist"}]
        
        if not os.path.isfile(abs_path):
            return False, [{"error": f"{file_path} is not a file"}]
        
        # Compile pattern
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error as e:
            return False, [{"error": f"Invalid regex pattern '{query}': {str(e)}"}]
        
        matches = _search_file(abs_path, pattern, file_path)
        return True, matches
        
    except Exception as e:
        error_msg = f"Error searching file {file_path}: {str(e)}"
        logging.error(error_msg)
        return False, [{"error": error_msg}]

if __name__ == "__main__":
    # Test the function
    success, matches = grep_search("def ", include_pattern="*.py")
    
    if success:
        print(f"Found {len(matches)} matches:")
        for match in matches[:5]:  # Show first 5 matches
            print(f"  {match['file_path']}:{match['line_number']} - {match['content'][:50]}...")
    else:
        print(f"Search failed: {matches}") 