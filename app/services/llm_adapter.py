import json
import logging
from typing import Union
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMGenerationAdapter:
    """
    Adapter Deep Module untuk membungkus komunikasi ke LLM Provider.
    Memastikan abstraksi API (OpenAI/Google) tidak bocor ke dalam LangGraph Nodes.
    """
    def __init__(self):
        self.llm = ChatOpenAI(
            model="nvidia/nemotron-3.5-lightning:free", 
            api_key=settings.OPENROUTER_API_KEY, 
            base_url="https://openrouter.ai/api/v1"
        )
    
    def invoke(self, prompt: Union[ChatPromptTemplate, str], kwargs: dict = None) -> str:
        """Eksekusi prompt murni dan kembalikan raw text"""
        if kwargs is None:
            kwargs = {}
        target = prompt | self.llm if isinstance(prompt, ChatPromptTemplate) else self.llm
        result = target.invoke(kwargs if isinstance(prompt, ChatPromptTemplate) else prompt)
        return result.content

    def invoke_and_parse_json(self, prompt: Union[ChatPromptTemplate, str], kwargs: dict = None) -> dict:
        """Eksekusi prompt dan paksa parsing sebagai dict (JSON)"""
        content = self.invoke(prompt, kwargs)
        clean = content.strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"Gagal memparsing JSON dari LLM: {clean}")
            raise e
            
    def invoke_and_clean_sql(self, prompt: Union[ChatPromptTemplate, str], kwargs: dict = None) -> str:
        """Eksekusi prompt khusus Code Generation (SQL)"""
        content = self.invoke(prompt, kwargs)
        return content.strip().replace("```sql", "").replace("```", "").strip()

# Singleton instance
llm_adapter = LLMGenerationAdapter()
