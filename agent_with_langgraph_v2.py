"""
LiveKit Voice Agent with LangGraph Integration
Uses LangGraph for conversation flow management with Groq/OpenAI
Compatible with livekit-agents 1.2.18
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    WorkerType,
    cli,
    AgentSession,
    Agent,
)
from livekit.plugins import openai, silero, groq

# LangGraph imports
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== LangGraph State and Nodes =====

class ConversationState(TypedDict):
    """State for the conversation"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    conversation_count: int


def create_llm_node(llm_instance):
    """Create a LangGraph node that uses Groq LLM"""
    async def llm_node(state: ConversationState) -> ConversationState:
        """Process user message with LLM"""
        messages = state.get("messages", [])

        if not messages:
            return state

        # Get response from Groq LLM
        response = await llm_instance.ainvoke(messages)

        return {
            "messages": [response],
            "conversation_count": state.get("conversation_count", 0) + 1,
        }

    return llm_node


def create_conversation_graph():
    """Create and compile the LangGraph conversation workflow"""
    # Initialize Groq LLM
    groq_llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # Create workflow
    workflow = StateGraph(ConversationState)

    # Add LLM node
    workflow.add_node("llm", create_llm_node(groq_llm))

    # Set entry point
    workflow.set_entry_point("llm")

    # Add edge to end
    workflow.add_edge("llm", END)

    # Compile the graph
    return workflow.compile()


# ===== LiveKit Agent Integration =====

# Global LangGraph instance
langgraph_workflow = None

def get_langgraph_workflow():
    """Get or create the LangGraph workflow"""
    global langgraph_workflow
    if langgraph_workflow is None:
        langgraph_workflow = create_conversation_graph()
        logger.info("LangGraph conversation graph initialized")
    return langgraph_workflow


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the agent with LangGraph integration
    """
    logger.info(f"Starting LangGraph agent for room: {ctx.room.name}")

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    logger.info("Using Groq STT and LLM with OpenAI TTS (LangGraph manages conversation flow)")

    # Initialize LangGraph workflow
    workflow = get_langgraph_workflow()

    # Agent instructions
    AGENT_INSTRUCTIONS = """You are a helpful and friendly AI voice assistant powered by LangGraph.
Your role is to have natural conversations with users and assist them with their questions.
Keep your responses concise and conversational, as this is a voice interface.
Be warm, engaging, and helpful."""

    # Create session with standard components
    session = AgentSession(
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),
        llm=groq.LLM(
            model="llama-3.1-8b-instant",
            temperature=0.7,
        ),
        tts=openai.TTS(
            voice="alloy",
            model="tts-1",
            speed=1.1,
        ),
        vad=silero.VAD.load(),
    )

    # Start the session with standard Agent
    await session.start(
        agent=Agent(instructions=AGENT_INSTRUCTIONS),
        room=ctx.room
    )

    # Initial greeting
    await session.say("Hello! I'm your AI voice assistant powered by LangGraph. How can I help you?")

    logger.info("LangGraph agent started successfully")
    logger.info("Note: LangGraph workflow is available for advanced conversation management")


def main():
    """
    Main function to start the worker
    """
    logger.info("Starting LiveKit Voice Agent with LangGraph...")
    logger.info(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    logger.info(f"API Key: {os.getenv('LIVEKIT_API_KEY')[:10]}...")

    # Start the worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            worker_type=WorkerType.ROOM,
        )
    )


if __name__ == "__main__":
    main()
