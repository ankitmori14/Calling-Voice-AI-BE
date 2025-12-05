"""
LiveKit Integration
Connects LangGraph workflow with LiveKit for voice conversations
"""
import asyncio
from livekit import agents
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
from app.core.conversation_manager import get_conversation_manager
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LiveKitVoiceAgent:
    """LiveKit voice agent integrated with LangGraph workflow"""

    def __init__(self):
        self.conversation_manager = get_conversation_manager()
        logger.info("Initialized LiveKit Voice Agent")

    async def handle_participant(self, ctx: JobContext):
        """
        Handle a participant joining the room

        This is the main entry point called by LiveKit when a user connects
        """
        logger.info(f"Participant joining room: {ctx.room.name}")

        # Connect to the room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        # Wait for the first participant
        participant = await ctx.wait_for_participant()
        logger.info(f"Participant connected: {participant.identity}")

        # Create conversation session
        session_id = await self.conversation_manager.create_session(
            user_id=participant.identity
        )

        logger.info(f"Created session {session_id} for {participant.identity}")

        # Create a function tool that processes messages through LangGraph
        @agents.llm.function_tool()
        async def process_user_query(query: str) -> str:
            """
            Process user queries through the Parul University admission system.
            
            This function handles all student queries about courses, fees, admissions,
            scholarships, and campus information using our specialized AI agents.
            
            Args:
                query: The user's question or message
                
            Returns:
                A helpful response from the admission assistant
            """
            logger.info(f"🎤 Function tool called with: {query[:100]}...")
            
            try:
                # Process through LangGraph workflow
                response = await self.conversation_manager.process_message(
                    session_id,
                    query
                )
                
                logger.info(f"🤖 LangGraph response: {response[:100] if response else 'None'}...")
                
                return response if response else "I apologize, I didn't quite understand that. Could you please rephrase your question?"
                
            except Exception as e:
                logger.error(f"❌ Error processing query: {e}", exc_info=True)
                return "I'm sorry, I encountered an error. Please try again or contact our helpline."

        # Create AgentSession with function tool
        session = AgentSession(
            stt=groq.STT(
                model=settings.STT_MODEL,
                language="en",
                api_key=settings.GROQ_API_KEY,
            ),
            llm=groq.LLM(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                api_key=settings.GROQ_API_KEY,
            ),
            tts=openai.TTS(
                voice=settings.TTS_VOICE,
                model=settings.TTS_MODEL,
                speed=settings.TTS_SPEED,
                api_key=settings.OPENAI_API_KEY,
            ),
            vad=silero.VAD.load(),
        )

        # Start the session with our custom instructions and tools
        agent = Agent(
            instructions=self._get_agent_instructions(),
            tools=[process_user_query]  # Register our LangGraph tool
        )

        # Add debug event listeners
        @session.on("user_speech_started")
        def on_user_speech_started():
            logger.info("🎤 User started speaking (VAD triggered)")

        @session.on("user_speech_committed")
        def on_user_speech_committed(msg):
            logger.info(f"📝 User speech transcribed: {msg.content}")

        @session.on("agent_speech_committed")
        def on_agent_speech_committed(msg):
            logger.info(f"🤖 Agent speech generated: {msg.content}")

        await session.start(
            agent=agent,
            room=ctx.room
        )

        logger.info(f"✅ Voice session started for {session_id}")
        logger.info(f"🎯 Function tool registered - LLM will call LangGraph for all queries")

        # Send initial greeting
        initial_greeting = await self.conversation_manager.process_message(
            session_id,
            "__INIT__"  # Special token for initial greeting
        )

        if initial_greeting:
            await session.say(initial_greeting, allow_interruptions=True)
            logger.info(f"📢 Sent initial greeting")

        # The session will now automatically handle conversations
        # The LLM will call our process_user_query tool for each user message

    def _get_agent_instructions(self) -> str:
        """Get agent instructions for LiveKit"""
        return """You are a voice assistant. You MUST use the process_user_query function for EVERY user message.

RULES:
1. When user speaks, IMMEDIATELY call process_user_query with their exact words
2. NEVER respond without calling the function first
3. Speak the exact response you get from the function
4. Do NOT add anything extra to the response
5. IMPORTANT: When the response includes a name, use it naturally - DO NOT say phrases like "you already mentioned your name is..." or "as you told me, your name is...". Just use the name naturally like "Sure, Kapil" or "Okay, Amit"

Example:
User says: "Tell me about engineering courses"
You MUST: Call process_user_query("Tell me about engineering courses")
Then: Speak exactly what the function returns

WRONG: "You already mentioned your name is Kapil, so let me help you..."
RIGHT: "Sure, Kapil! Let me help you..."""


async def entrypoint(ctx: JobContext):
    """
    LiveKit worker entrypoint

    This function is called by LiveKit when starting the worker
    """
    agent = LiveKitVoiceAgent()
    await agent.handle_participant(ctx)


def start_livekit_worker():
    """Start the LiveKit worker"""
    logger.info("Starting LiveKit Worker...")
    logger.info(f"LiveKit URL: {settings.LIVEKIT_URL}")
    logger.info(f"Using models: STT={settings.STT_MODEL}, LLM={settings.LLM_MODEL}, TTS={settings.TTS_MODEL}")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            worker_type=WorkerType.ROOM,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            ws_url=settings.LIVEKIT_URL,
        )
    )


if __name__ == "__main__":
    start_livekit_worker()
