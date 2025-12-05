"""
Router Agent
Classifies user intent and routes to appropriate specialist agent
Uses Groq LLM for intent classification
"""
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.base_agent import BaseAgent
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RouterAgent(BaseAgent):
    """Agent for classifying user intent and routing"""

    def __init__(self):
        super().__init__("router")
        self.llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=0.3,  # Lower temperature for more consistent classification
            groq_api_key=settings.GROQ_API_KEY
        )

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify user intent and set next agent"""

        # Mark as visited
        state = self._update_visited_agents(state)

        # Get last user message
        messages = state.get("messages", [])
        if not messages:
            return state

        last_message = messages[-1] if messages else None
        if not last_message or last_message.get("role") != "user":
            return state

        user_query = last_message.get("content", "")

        # Classify intent
        intent = await self._classify_intent(user_query, state)

        # Set next agent based on intent
        state = self._set_context(state, "current_intent", intent)
        state = self._set_context(state, "next_agent", intent)

        logger.info(f"Classified intent: {intent} for query: {user_query[:50]}...")

        return state

    async def _classify_intent(self, query: str, state: Dict[str, Any]) -> str:
        """
        Classify user intent using Groq LLM

        Returns one of: course | fees | admission | followup | general
        """

        system_prompt = """You are an intent classifier for a university admission helpline.
Classify the user's query into ONE of these categories:

1. "course" - Questions about courses, programs, syllabus, duration, eligibility, subjects
   Examples: "tell me about B.Tech", "what courses do you offer", "CSE syllabus"

2. "fees" - Questions about fee structure, payment, costs, discounts
   Examples: "how much is the fee", "payment options", "total cost"

3. "admission" - Questions about admission process, application, documents, deadlines
   Examples: "how to apply", "admission process", "required documents", "last date"

4. "followup" - User wants to schedule visit, get brochure, talk to counselor, provide contact
   Examples: "campus visit", "send brochure", "call me back", "my email is"

5. "general" - General questions, greetings, thank you, or unclear intent
   Examples: "hello", "thank you", "where is the university"

Respond with ONLY the category name, nothing else."""

        # Get context for better classification
        user_name = self._get_user_info(state, "name", "")
        topics_discussed = state.get("topics_discussed", [])

        context_info = f"\nUser name: {user_name}" if user_name else ""
        if topics_discussed:
            context_info += f"\nPrevious topics: {', '.join(topics_discussed)}"

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"{context_info}\n\nUser query: {query}")
            ])

            intent = response.content.strip().lower()

            # Validate intent
            valid_intents = ["course", "fees", "admission", "followup", "general"]
            if intent not in valid_intents:
                logger.warning(f"Invalid intent '{intent}', defaulting to 'general'")
                intent = "general"

            return intent

        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "general"

    def detect_multi_intent(self, query: str) -> bool:
        """
        Detect if query has multiple intents
        Example: "Tell me about B.Tech fees and admission process"
        """
        keywords = {
            "course": ["course", "program", "syllabus", "subjects", "btech", "mba", "bba"],
            "fees": ["fees", "cost", "payment", "price", "scholarship"],
            "admission": ["admission", "apply", "application", "documents", "deadline"]
        }

        query_lower = query.lower()
        detected_intents = []

        for intent, words in keywords.items():
            if any(word in query_lower for word in words):
                detected_intents.append(intent)

        return len(detected_intents) > 1
