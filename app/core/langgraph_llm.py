"""
Custom LLM Wrapper for LangGraph
Wraps the LangGraph workflow to work with LiveKit AgentSession
"""
from livekit import agents
from app.core.conversation_manager import ConversationManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LangGraphLLM(agents.llm.LLM):
    """
    Custom LLM implementation that routes requests through LangGraph workflow
    """
    
    def __init__(self, conversation_manager: ConversationManager, session_id: str):
        super().__init__()
        self.conversation_manager = conversation_manager
        self.session_id = session_id
        self._last_response = ""
        logger.info(f"Initialized LangGraphLLM for session {session_id}")
    
    async def chat(
        self,
        chat_ctx: agents.llm.ChatContext,
        **kwargs
    ) -> "agents.llm.LLMStream":
        """Process chat through LangGraph"""
        # Get user message
        messages = chat_ctx.messages
        user_message = ""
        if messages:
            last_message = messages[-1]
            user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        logger.info(f"🎤 User: {user_message[:100]}...")
        
        try:
            # Process through LangGraph
            response = await self.conversation_manager.process_message(
                self.session_id,
                user_message
            )
            self._last_response = response if response else "I didn't understand that."
            logger.info(f"🤖 Response: {self._last_response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            self._last_response = "I encountered an error. Please try again."
        
        # Create stream - using the simplest possible approach
        from livekit.agents.llm import llm as llm_module
        
        return llm_module.LLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=[],
            conn_options=llm_module.APIConnectOptions()
        )
