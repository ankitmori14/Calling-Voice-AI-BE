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
from livekit.plugins import openai, silero, google, groq

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Simple agent instructions
AGENT_INSTRUCTIONS = """You are a helpful and friendly AI voice assistant.
Your role is to have natural conversations with users and assist them with their questions.
Keep your responses concise and conversational, as this is a voice interface.
Be warm, engaging, and helpful."""


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the agent
    This function is called when a user connects to the room
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # Optimized for low latency
    logger.info("Using Groq STT and LLM with OpenAI TTS (optimized for speed)")
    session = AgentSession(
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",  # Specify language for faster processing
        ),
        llm=groq.LLM(
            model="llama-3.1-8b-instant",  # Faster 8B model instead of 70B
            temperature=0.7,
        ),
        tts=openai.TTS(
            voice="alloy",
            model="tts-1",  # Use faster tts-1 instead of tts-1-hd
            speed=1.1,  # Slightly faster speech
        ),
        vad=silero.VAD.load(),
    )

    # Start the session with Agent instance
    await session.start(
        agent=Agent(instructions=AGENT_INSTRUCTIONS),
        room=ctx.room
    )

    # Send initial greeting
    await session.say("Hello! I'm your AI voice assistant. How can I help you today?")

    logger.info("Agent session started successfully and ready for conversation")


def main():
    """
    Main function to start the worker
    """
    logger.info("Starting LiveKit Voice Agent Worker...")
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
