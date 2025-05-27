import os
import json
import logging
from typing import List, Dict, Any, Union

def call_llm(prompt: Union[str, List[Dict[str, str]]], model: str = "gpt-4o") -> str:
    """
    Makes API calls to language model services
    
    Args:
        prompt: Either a string prompt or list of messages
        model: Model name to use
        
    Returns:
        LLM response text
    """
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = OpenAI(api_key=api_key)
        
        # Convert string prompt to messages format if needed
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1  # Lower temperature for more consistent responses
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"LLM call failed: {e}")
        raise

def call_llm_with_retries(prompt: Union[str, List[Dict[str, str]]], max_retries: int = 3) -> str:
    """
    Call LLM with retry logic for better reliability
    """
    import time
    
    for attempt in range(max_retries):
        try:
            return call_llm(prompt)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
            logging.warning(f"LLM call attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")

if __name__ == "__main__":
    # Test the function
    test_prompt = "Hello, how are you?"
    try:
        response = call_llm(test_prompt)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
