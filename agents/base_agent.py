"""
Base Agent class for the multi-agent paper reviewer system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import os
import sys
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Ensure emoji/Unicode in agent logs don't crash on Windows consoles (cp1252).
# Every agent imports this module, so this runs before any agent prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, role: str, model: str = None, api_key: str = None):
        """
        Initialize the base agent.

        Args:
            name: Agent name
            role: Agent role description
            model: LLM model to use (defaults to MODEL_NAME env or llama-3.1-8b-instant)
            api_key: Groq API key. If not provided, falls back to the GROQ_API_KEY
                     environment variable. On the public app this is supplied per
                     session from the user's pasted key and is never stored.
        """
        self.name = name
        self.role = role
        self.model = model or os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
        key = api_key or os.getenv("GROQ_API_KEY")
        # Client is None when no key is available; call_llm handles that gracefully.
        self.client = Groq(api_key=key) if key else None
        self.tool_calls_count = 0
        
    def call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        Call the Groq LLM API.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            
        Returns:
            LLM response text
        """
        if self.client is None:
            return "Error: No Groq API key provided. Please paste your Groq API key to run the review."
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return f"Error: {str(e)}"
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Processing results
        """
        pass
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Returns:
            System prompt string
        """
        return f"""You are {self.name}, a specialized agent in a multi-agent paper review system.
Your role: {self.role}

Provide clear, concise, and accurate responses. Focus on being helpful for students 
trying to understand academic papers."""
    
    def format_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format agent output.
        
        Args:
            content: Raw content dictionary
            
        Returns:
            Formatted output dictionary
        """
        return {
            "agent": self.name,
            "role": self.role,
            "tool_calls": self.tool_calls_count,
            "output": content
        }