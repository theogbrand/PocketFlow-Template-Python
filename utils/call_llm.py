import os
import json
import logging
from typing import List, Dict, Any, Union

def call_llm(prompt: Union[str, List[Dict[str, str]]], model: str = "claude-3-5-sonnet-20241022") -> str:
    """
    Makes API calls to language model services using LiteLLM for multi-provider support
    
    Supported models:
        - OpenAI: "gpt-4o", "gpt-4", "gpt-3.5-turbo"
        - Claude: "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"  
        - Gemini: "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"
    
    Required environment variables (set only for providers you use):
        - OPENAI_API_KEY: For OpenAI models
        - ANTHROPIC_API_KEY: For Claude models  
        - GOOGLE_API_KEY: For Gemini models
    
    Args:
        prompt: Either a string prompt or list of messages
        model: Model name to use
        
    Returns:
        LLM response text
    """
    try:
        import litellm
        
        # Convert string prompt to messages format if needed
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.1  # Lower temperature for more consistent responses
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"LLM call failed with model {model}: {e}")
        raise

def call_llm_with_retries(prompt: Union[str, List[Dict[str, str]]], model: str = "claude-3-5-sonnet-20241022", max_retries: int = 3) -> str:
    """
    Call LLM with retry logic for better reliability
    """
    import time
    
    for attempt in range(max_retries):
        try:
            return call_llm(prompt, model)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
            logging.warning(f"LLM call attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")

if __name__ == "__main__":
    # Test the function with different models
    test_prompt = "Hello, how are you?"
    
    # Test with different models (uncomment as needed)
    models_to_test = [
        # "claude-sonnet-4-20250514",       # Claude (requires ANTHROPIC_API_KEY) - DEFAULT
        # "gpt-4o",                         # OpenAI (requires OPENAI_API_KEY)
        "gemini/gemini-2.5-pro-preview-05-06",      # Gemini 2.0 (requires GOOGLE_API_KEY)
    ]
    
    for model in models_to_test:
        try:
            print(f"\nTesting {model}...")
            response = call_llm(test_prompt, model)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error with {model}: {e}")
