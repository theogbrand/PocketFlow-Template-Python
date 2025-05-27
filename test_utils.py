#!/usr/bin/env python3
"""
Test script for all utility functions in the coding agent
"""

import os
import tempfile
import shutil
from utils.call_llm import call_llm
from utils.read_file import read_file, get_file_info
from utils.replace_file import replace_file, insert_file
from utils.delete_file import delete_file, remove_file_content
from utils.search_ops import grep_search, search_in_file
from utils.dir_ops import list_dir, get_directory_stats

def test_file_operations():
    """Test file operations utilities"""
    print("=== Testing File Operations ===")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")
        
        # Test file creation and insertion
        test_file = "test.py"
        content = """def hello_world():
    print("Hello, World!")
    return "success"

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
"""
        
        success, msg = insert_file(test_file, content, working_dir=temp_dir)
        print(f"✓ Insert file: {success} - {msg}")
        
        # Test file reading
        success, file_content = read_file(test_file, working_dir=temp_dir)
        print(f"✓ Read file: {success} - Content length: {len(file_content) if success else file_content}")
        
        # Test file info
        success, info = get_file_info(test_file, working_dir=temp_dir)
        print(f"✓ Get file info: {success} - Size: {info.get('size', 'N/A')} bytes")
        
        # Test replace file content
        success, msg = replace_file(test_file, 2, 3, '    print("Hello, Coding Agent!")\n    return "modified"\n', working_dir=temp_dir)
        print(f"✓ Replace file content: {success} - {msg}")
        
        # Test remove file content
        success, msg = remove_file_content(test_file, 7, 8, working_dir=temp_dir)
        print(f"✓ Remove file content: {success} - {msg}")
        
        # Test delete file
        success, msg = delete_file(test_file, working_dir=temp_dir)
        print(f"✓ Delete file: {success} - {msg}")

def test_search_operations():
    """Test search operations utilities"""
    print("\n=== Testing Search Operations ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        files_content = {
            "main.py": """def main():
    print("Main function")
    process_data()

def process_data():
    data = [1, 2, 3]
    return data
""",
            "utils.py": """def helper_function():
    return "helper"

class UtilClass:
    def process(self):
        return "processed"
""",
            "config.json": """{
    "name": "test_project",
    "version": "1.0.0"
}"""
        }
        
        # Create test files
        for filename, content in files_content.items():
            success, msg = insert_file(filename, content, working_dir=temp_dir)
            print(f"Created {filename}: {success}")
        
        # Test grep search for function definitions
        success, matches = grep_search("def ", include_pattern="*.py", working_dir=temp_dir)
        print(f"✓ Grep search for 'def ': {success} - Found {len(matches)} matches")
        if success and matches:
            for match in matches[:3]:  # Show first 3 matches
                print(f"   {match['file_path']}:{match['line_number']} - {match['content'].strip()}")
        
        # Test search in specific file
        success, matches = search_in_file("main.py", "print", working_dir=temp_dir)
        print(f"✓ Search in specific file: {success} - Found {len(matches)} matches")
        
        # Test case-insensitive search
        success, matches = grep_search("FUNCTION", case_sensitive=False, working_dir=temp_dir)
        print(f"✓ Case-insensitive search: {success} - Found {len(matches)} matches")

def test_directory_operations():
    """Test directory operations utilities"""
    print("\n=== Testing Directory Operations ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directory structure
        os.makedirs(os.path.join(temp_dir, "src", "modules"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "tests"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "docs"), exist_ok=True)
        
        # Create some files
        files = [
            "README.md",
            "main.py",
            "src/app.py",
            "src/modules/utils.py",
            "src/modules/helpers.py",
            "tests/test_main.py",
            "docs/guide.md"
        ]
        
        for file_path in files:
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(f"# Content of {file_path}\n")
        
        # Test list directory
        success, tree = list_dir(".", working_dir=temp_dir)
        print(f"✓ List directory: {success}")
        if success:
            print("Directory tree:")
            print(tree)
        
        # Test directory stats
        success, stats = get_directory_stats(".", working_dir=temp_dir)
        print(f"✓ Directory stats: {success}")
        if success:
            print(f"   Files: {stats['file_count']}, Dirs: {stats['directory_count']}, Size: {stats['total_size_formatted']}")
        
        # Test subdirectory listing
        success, tree = list_dir("src", working_dir=temp_dir)
        print(f"✓ List subdirectory: {success}")
        if success:
            print("Src directory tree:")
            print(tree)

def test_llm_wrapper():
    """Test LLM wrapper (requires API key)"""
    print("\n=== Testing LLM Wrapper ===")
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ Skipping LLM test - OPENAI_API_KEY not set")
        return
    
    try:
        # Simple test prompt
        response = call_llm("Say 'Hello from coding agent!' and nothing else.")
        print(f"✓ LLM call successful: {response[:50]}...")
    except Exception as e:
        print(f"✗ LLM call failed: {str(e)}")

def main():
    """Run all tests"""
    print("Testing Coding Agent Utility Functions")
    print("=" * 50)
    
    test_file_operations()
    test_search_operations() 
    test_directory_operations()
    test_llm_wrapper()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main() 