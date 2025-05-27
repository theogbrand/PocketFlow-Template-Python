#!/usr/bin/env python3
"""
Simple test script to demonstrate CLI functionality of the coding agent.
"""

import subprocess
import sys

def run_command(command, description):
    """Run a command and display the output."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"COMMAND: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("OUTPUT:")
        print(result.stdout)
        
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
        
        print(f"Return Code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run CLI tests."""
    print("🚀 Testing Coding Agent CLI Functionality")
    
    # Test commands
    tests = [
        {
            "command": "uv run python main.py --help",
            "description": "Show help information"
        },
        {
            "command": 'uv run python main.py --query "Show me the current directory structure" --verbose',
            "description": "List directory with verbose logging"
        },
        {
            "command": 'uv run python main.py --query "Read the first 10 lines of README.md"',
            "description": "Read file content"
        }
    ]
    
    for test in tests:
        run_command(test["command"], test["description"])
        
        # Ask user if they want to continue
        try:
            choice = input("\nContinue to next test? (y/n): ").strip().lower()
            if choice != 'y':
                print("Stopping tests.")
                break
        except (EOFError, KeyboardInterrupt):
            print("\nStopping tests.")
            break
    
    print(f"\n{'='*60}")
    print("CLI TESTING COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 