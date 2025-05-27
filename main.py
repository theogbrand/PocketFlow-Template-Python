import os
import logging
import argparse
from flow import create_coding_agent_flow

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coding_agent.log'),
        logging.StreamHandler()
    ]
)

def run_coding_agent(user_query, working_dir=None):
    """
    Run the coding agent with a specific query.
    
    Args:
        user_query (str): The user's coding request
        working_dir (str, optional): Working directory. Defaults to current directory.
    
    Returns:
        dict: The shared memory state after execution
    """
    if working_dir is None:
        working_dir = os.getcwd()
    
    # Initialize shared memory according to design doc
    shared = {
        "user_query": user_query,
        "working_dir": working_dir,
        "history": [],
        "edit_operations": [],
        "response": ""
    }
    
    logging.info(f"Starting coding agent with query: {user_query}")
    logging.info(f"Working directory: {working_dir}")
    
    # Create and run the coding agent flow
    coding_agent_flow = create_coding_agent_flow()
    
    try:
        coding_agent_flow.run(shared)
        
        # Log final state
        logging.info(f"Completed {len(shared['history'])} actions")
        logging.info("Final response delivered to user")
        
        return shared
        
    except Exception as e:
        error_msg = f"Error running coding agent: {str(e)}"
        logging.error(error_msg)
        shared["response"] = f"Error: {error_msg}"
        return shared

def interactive_mode():
    """Run the coding agent in interactive mode."""
    working_dir = os.getcwd()
    
    print("=" * 60)
    print("CODING AGENT - INTERACTIVE MODE")
    print("=" * 60)
    print("Enter your coding requests. Type 'quit' to exit.")
    print(f"Working directory: {working_dir}")
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
        
        print("\nProcessing your request...")
        print("-" * 40)
        
        shared = run_coding_agent(user_query, working_dir)
        
        # Display results
        print("\nAGENT RESPONSE:")
        print("=" * 40)
        print(shared.get("response", "No response generated"))
        print("=" * 40)
        print()

def main():
    """
    Main function for the coding agent.
    Supports both CLI and interactive modes.
    """
    parser = argparse.ArgumentParser(
        description="Coding Agent - AI-powered file operations assistant",
        epilog="Examples:\n"
               "  python main.py --query \"Read the README.md file\"\n"
               "  python main.py --query \"Search for 'TODO' in Python files\"\n"
               "  python main.py  # Interactive mode",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="The coding request to execute. If not provided, starts interactive mode."
    )
    
    parser.add_argument(
        "--working-dir", "-w",
        type=str,
        default=None,
        help="Working directory for file operations. Defaults to current directory."
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine working directory
    working_dir = args.working_dir if args.working_dir else os.getcwd()
    
    if args.query:
        # CLI mode with provided query
        print(f"Executing query: {args.query}")
        print(f"Working directory: {working_dir}")
        print("-" * 50)
        
        shared = run_coding_agent(args.query, working_dir)
        
        # Display results
        print("\n" + "="*50)
        print("CODING AGENT RESPONSE:")
        print("="*50)
        print(shared.get("response", "No response generated"))
        print("="*50)
        
        # Display action summary
        if shared.get("history"):
            print(f"\nActions performed: {len(shared['history'])}")
            for i, action in enumerate(shared['history'], 1):
                # Handle case where action might be None or missing fields
                if action is None:
                    print(f"  {i}. ✗ Unknown action: No action data")
                    continue
                
                # Safely get result and success status
                result = action.get('result', {}) if isinstance(action, dict) else {}
                success = result.get('success', True) if isinstance(result, dict) else True
                status = "✓" if success else "✗"
                
                # Safely get tool and reason
                tool = action.get('tool', 'unknown') if isinstance(action, dict) else 'unknown'
                reason = action.get('reason', 'no reason provided') if isinstance(action, dict) else 'no reason provided'
                
                print(f"  {i}. {status} {tool}: {reason}")
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
