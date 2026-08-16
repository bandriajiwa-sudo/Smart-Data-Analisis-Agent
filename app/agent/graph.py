import logging
from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes.router import node_intent_router
from app.agent.nodes.sql_generator import node_sql_generator
from app.agent.nodes.executor import node_sql_executor
from app.agent.nodes.error_handler import node_error_handler
from app.agent.nodes.answer_generator import node_answer_generator
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings

logger = logging.getLogger(__name__)

def route_from_intent(state: AgentState) -> str:
    if state.intent == "general_chat":
        return "general_chat"
    return "sql_generator"

def route_from_execution(state: AgentState) -> str:
    if state.status == "error":
        if state.retry_count >= 3:
            return "answer_generator"
        return "error_handler"
    return "answer_generator"

def general_chat_fallback(state: AgentState) -> dict:
    return {"final_answer": "Halo! Saya asisten Smart Data POS. Ada yang bisa saya bantu dengan analisis basis data jualan anda hari ini?", "status": "success"}

async def create_agent_graph(checkpointer):
    """Build and compile LangGraph Stateful Logic with Persistent PG Memory"""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("intent_router", node_intent_router)
    workflow.add_node("sql_generator", node_sql_generator)
    workflow.add_node("sql_executor", node_sql_executor)
    workflow.add_node("error_handler", node_error_handler)
    workflow.add_node("answer_generator", node_answer_generator)
    workflow.add_node("general_chat", general_chat_fallback)

    workflow.add_edge(START, "intent_router")
    workflow.add_conditional_edges("intent_router", route_from_intent)
    
    workflow.add_edge("sql_generator", "sql_executor")
    
    workflow.add_conditional_edges("sql_executor", route_from_execution)
    
    workflow.add_edge("error_handler", "sql_executor")
    
    workflow.add_edge("general_chat", END)
    workflow.add_edge("answer_generator", END)
    
    await checkpointer.setup()
    
    app = workflow.compile(checkpointer=checkpointer)
    return app
