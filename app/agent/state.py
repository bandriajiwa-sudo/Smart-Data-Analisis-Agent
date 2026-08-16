from typing import Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

class AgentState(BaseModel):
    """State Machine untuk Smart Data Analyst Agent"""

    # Thread Identity
    thread_id: str = Field(description="Unique identifier untuk sesi user")
    user_id: str = Field(default="unknown", description="Identifier user dari sistem POS")

    # Conversation Memory
    messages: Annotated[list, add_messages] = Field(
        default_factory=list,
        description="Histori percakapan multi-turn"
    )

    # Intent Classification
    intent: Optional[str] = Field(
        default=None,
        description="Klasifikasi intent: database_query | data_analysis | general_chat"
    )

    # SQL Generation & Execution
    generated_sql: Optional[str] = Field(
        default=None,
        description="Query SQL yang dihasilkan oleh LLM"
    )
    query_result: Optional[dict] = Field(
        default=None,
        description="Hasil eksekusi query dari PostgreSQL"
    )

    # Self-Healing Mechanism
    error_log: Optional[str] = Field(
        default=None,
        description="Pesan error dari PostgreSQL"
    )
    retry_count: int = Field(
        default=0,
        description="Jumlah percobaan koreksi query (max: 3)",
        ge=0,
        le=3
    )

    # Final Output
    final_answer: Optional[str] = Field(
        default=None,
        description="Jawaban akhir dalam natural language"
    )

    # Metadata
    execution_time_ms: Optional[int] = Field(
        default=None,
        description="Waktu eksekusi total dalam milidetik"
    )
    status: str = Field(
        default="pending",
        description="Status eksekusi: pending | processing | success | error | max_retry_exceeded"
    )
