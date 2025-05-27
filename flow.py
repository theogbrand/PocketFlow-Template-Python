from pocketflow import Flow
from nodes import (
    MainDecisionAgentNode,
    ReadFileActionNode,
    GrepSearchActionNode,
    ListDirectoryActionNode,
    DeleteFileActionNode,
    ReadTargetFileNode,
    AnalyzeAndPlanChangesNode,
    ApplyChangesBatchNode,
    FormatResponseNode
)

def create_coding_agent_flow():
    """Create and return the coding agent flow."""
    
    # Create main decision agent
    main_agent = MainDecisionAgentNode()
    
    # Create action nodes
    read_file_action = ReadFileActionNode()
    grep_search_action = GrepSearchActionNode()
    list_dir_action = ListDirectoryActionNode()
    delete_file_action = DeleteFileActionNode()
    
    # Create edit file sub-flow nodes
    read_target_file = ReadTargetFileNode()
    analyze_and_plan = AnalyzeAndPlanChangesNode()
    apply_changes = ApplyChangesBatchNode()
    
    # Create response formatter
    format_response = FormatResponseNode()
    
    # Connect main agent to action nodes
    main_agent - "read_file" >> read_file_action
    main_agent - "grep_search" >> grep_search_action
    main_agent - "list_dir" >> list_dir_action
    main_agent - "delete_file" >> delete_file_action
    main_agent - "edit_file" >> read_target_file
    main_agent - "finish" >> format_response
    
    # Connect action nodes back to main agent for next decision
    read_file_action - "decide_next" >> main_agent
    grep_search_action - "decide_next" >> main_agent
    list_dir_action - "decide_next" >> main_agent
    delete_file_action - "decide_next" >> main_agent
    
    # Connect edit file sub-flow
    read_target_file - "analyze_plan" >> analyze_and_plan
    read_target_file - "decide_next" >> main_agent  # If file read failed
    analyze_and_plan - "apply_changes" >> apply_changes
    apply_changes - "decide_next" >> main_agent
    
    # Response formatter
    format_response - "done" >> None  # End of flow
    
    return Flow(start=main_agent)

def create_qa_flow():
    """Legacy QA flow - kept for compatibility."""
    from nodes import GetQuestionNode, AnswerNode
    
    get_question_node = GetQuestionNode()
    answer_node = AnswerNode()
    
    get_question_node >> answer_node
    
    return Flow(start=get_question_node)

coding_agent_flow = create_coding_agent_flow()