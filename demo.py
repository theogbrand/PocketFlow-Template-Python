#!/usr/bin/env python3
"""
Demo script for the Coding Agent
Shows various capabilities of the agent with predefined examples.
"""

import os
import logging
import subprocess
import sys
from flow import create_coding_agent_flow

# Set up logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coding_agent_demo.log'),
        logging.StreamHandler()
    ]
)

def demo_cli_usage():
    """Demonstrate CLI usage of the coding agent."""
    
    print("=" * 60)
    print("CODING AGENT CLI DEMO")
    print("=" * 60)
    print("Demonstrating command-line usage of the coding agent")
    print()
    
    # CLI demo examples
    cli_examples = [
        {
            "name": "Directory Listing",
            "command": 'python main.py --query "Show me the structure of the current directory"',
            "description": "List directory contents via CLI"
        },
        {
            "name": "File Reading",
            "command": 'python main.py --query "Read the contents of README.md"',
            "description": "Read a file via CLI"
        },
        {
            "name": "Text Search",
            "command": 'python main.py --query "Search for \'pocketflow\' in Python files"',
            "description": "Search for text patterns via CLI"
        },
        {
            "name": "Help Command",
            "command": 'python main.py --help',
            "description": "Show available CLI options"
        }
    ]
    
    for i, example in enumerate(cli_examples, 1):
        print(f"CLI Example {i}: {example['name']}")
        print(f"Description: {example['description']}")
        print(f"Command: {example['command']}")
        print("-" * 40)
        
        # Ask user if they want to run this command
        try:
            choice = input("Run this command? (y/n/s=skip all): ").strip().lower()
            if choice == 's':
                print("Skipping remaining CLI demos.")
                break
            elif choice == 'y':
                print(f"Executing: {example['command']}")
                print("=" * 40)
                
                # Run the command
                try:
                    result = subprocess.run(
                        example['command'],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    print("STDOUT:")
                    print(result.stdout)
                    if result.stderr:
                        print("STDERR:")
                        print(result.stderr)
                    print(f"Return code: {result.returncode}")
                    
                except subprocess.TimeoutExpired:
                    print("Command timed out after 60 seconds")
                except Exception as e:
                    print(f"Error running command: {e}")
            else:
                print("Skipped.")
                
        except (EOFError, KeyboardInterrupt):
            print("\nExiting CLI demo.")
            break
        
        print("=" * 60)
        print()

def demo_coding_agent():
    """Run a series of demo tasks to showcase the coding agent."""
    
    working_dir = os.getcwd()
    coding_agent_flow = create_coding_agent_flow()
    
    # Demo examples
    demo_tasks = [
        {
            "name": "List Directory Contents",
            "query": "Show me the structure of the current directory",
            "description": "Demonstrates directory listing with tree visualization"
        },
        {
            "name": "Read a File",
            "query": "Read the contents of README.md",
            "description": "Demonstrates file reading capability"
        },
        {
            "name": "Search for Text",
            "query": "Search for 'pocketflow' in Python files",
            "description": "Demonstrates grep search functionality"
        },
        {
            "name": "Create and Edit File",
            "query": "Create a simple hello.py file with a function that prints 'Hello, World!'",
            "description": "Demonstrates file creation and editing"
        }
    ]
    
    print("=" * 60)
    print("CODING AGENT DEMO")
    print("=" * 60)
    print()
    
    for i, task in enumerate(demo_tasks, 1):
        print(f"Demo {i}: {task['name']}")
        print(f"Description: {task['description']}")
        print(f"Query: {task['query']}")
        print("-" * 40)
        
        # Initialize shared memory for this task
        shared = {
            "user_query": task["query"],
            "working_dir": working_dir,
            "history": [],
            "edit_operations": [],
            "response": ""
        }
        
        try:
            # Run the coding agent
            coding_agent_flow.run(shared)
            
            # Display results
            print("AGENT RESPONSE:")
            print(shared.get("response", "No response generated"))
            print()
            print(f"Actions performed: {len(shared['history'])}")
            for j, action in enumerate(shared['history'], 1):
                status = "✓" if action.get('result', {}).get('success', True) else "✗"
                print(f"  {j}. {status} {action['tool']}: {action['reason']}")
            
        except Exception as e:
            print(f"Error in demo task: {str(e)}")
        
        print("=" * 60)
        print()
        
        # Pause between demos
        try:
            input("Press Enter to continue to next demo...")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting demo.")
            break
        print()

def interactive_mode():
    """Run the coding agent in interactive mode."""
    
    working_dir = os.getcwd()
    coding_agent_flow = create_coding_agent_flow()
    
    print("=" * 60)
    print("CODING AGENT - INTERACTIVE MODE")
    print("=" * 60)
    print("Enter your coding requests. Type 'quit' to exit.")
    print()
    
    while True:
        try:
            user_query = input("Your request: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_query:
            print("Please enter a request.")
            continue
        
        # Initialize shared memory
        shared = {
            "user_query": user_query,
            "working_dir": working_dir,
            "history": [],
            "edit_operations": [],
            "response": ""
        }
        
        print("\nProcessing your request...")
        print("-" * 40)
        
        try:
            # Run the coding agent
            coding_agent_flow.run(shared)
            
            # Display results
            print("\nAGENT RESPONSE:")
            print("=" * 40)
            print(shared.get("response", "No response generated"))
            print("=" * 40)
            
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print()

if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Predefined demos (programmatic)")
    print("2. Interactive mode")
    print("3. CLI usage demos")
    print()
    
    try:
        choice = input("Enter choice (1, 2, or 3): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        sys.exit(0)
    
    if choice == "1":
        demo_coding_agent()
    elif choice == "2":
        interactive_mode()
    elif choice == "3":
        demo_cli_usage()
    else:
        print("Invalid choice. Exiting.") 