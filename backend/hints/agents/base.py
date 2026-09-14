import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all adaptive intelligence agents."""
    
    def __init__(self, model_name: str, temperature: float = 0.5):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model_name = model_name
        self.temperature = temperature
        
        # Configure LangSmith if available
        self._setup_tracing()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=self.temperature
        )
        
        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()
        
        logger.info(f"🤖 Agent Initialized: {self.__class__.__name__} using {self.model_name}")

    def _setup_tracing(self):
        """Standardize LangSmith tracing across agents."""
        langsmith_key = settings.LANGSMITH_API_KEY
        if langsmith_key:
            os.environ["LANGCHAIN_API_KEY"] = langsmith_key
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGSMITH_TRACING_V2)
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
