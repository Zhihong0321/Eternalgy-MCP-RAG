import os
import httpx
from typing import List, Dict, Optional, Any
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

class ZaiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.z.ai/api/coding/paas/v4", timeout: int = 300):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        
        # Create a custom HTTP client for better performance and stability
        self.http_client = httpx.Client(
            timeout=float(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=self.http_client
        )

    def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "glm-4.5-flash", 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None
    ) -> ChatCompletionMessage:
        """
        Send a chat request to Z.ai API, optionally with tools.
        Returns the full message object (content, tool_calls, etc).
        """
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            
            # Handle reasoning content fallback logic
            content = message.content
            reasoning_content = getattr(message, "reasoning_content", None)
            
            if not content and reasoning_content:
                message.content = reasoning_content
                
            return message

        except Exception as e:
            raise e
