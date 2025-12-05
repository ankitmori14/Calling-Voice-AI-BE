"""
LangGraph Workflow
Main conversation graph connecting all agents
"""
from typing import Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.agents.greeting_agent import GreetingAgent
from app.agents.router_agent import RouterAgent
from app.agents.course_agent import CourseAgent
from app.agents.fees_agent import FeesAgent
from app.agents.admission_agent import AdmissionAgent
from app.agents.followup_agent import FollowupAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Define conversation state schema
class ConversationState(TypedDict):
    """State schema for conversation"""
    session_id: str
    messages: Annotated[list, add_messages]
    user_info: Dict[str, Any]
    context: Dict[str, Any]
    visited_agents: list[str]
    topics_discussed: list[str]
    conversation_count: int


class ParulAdmissionWorkflow:
    """Main LangGraph workflow for Parul admission system"""

    def __init__(self):
        self.greeting_agent = GreetingAgent()
        self.router_agent = RouterAgent()
        self.course_agent = CourseAgent()
        self.fees_agent = FeesAgent()
        self.admission_agent = AdmissionAgent()
        self.followup_agent = FollowupAgent()

        self.graph = self._create_graph()
        logger.info("Initialized Parul Admission Workflow")

    def _create_graph(self) -> StateGraph:
        """Create and compile the LangGraph workflow"""

        # Create workflow
        workflow = StateGraph(ConversationState)

        # Add nodes for each agent
        workflow.add_node("greeting", self._greeting_node)
        workflow.add_node("router", self._router_node)
        workflow.add_node("course", self._course_node)
        workflow.add_node("fees", self._fees_node)
        workflow.add_node("admission", self._admission_node)
        workflow.add_node("followup", self._followup_node)

        # Set entry point
        workflow.set_entry_point("greeting")

        # Add conditional edges from greeting
        workflow.add_conditional_edges(
            "greeting",
            self._route_after_greeting,
            {
                "router": "router",
                "end": END
            }
        )

        # Add conditional edges from router to specialist agents
        workflow.add_conditional_edges(
            "router",
            self._route_to_specialist,
            {
                "course": "course",
                "fees": "fees",
                "admission": "admission",
                "followup": "followup",
                "end": END
            }
        )

        # All specialist agents can loop back to router or end
        for agent in ["course", "fees", "admission", "followup"]:
            workflow.add_conditional_edges(
                agent,
                self._route_after_specialist,
                {
                    "router": "router",
                    "end": END
                }
            )

        # Compile the graph
        return workflow.compile()

    async def _greeting_node(self, state: ConversationState) -> ConversationState:
        """Greeting agent node"""
        logger.debug("Executing greeting node")
        return await self.greeting_agent.process(state)

    async def _router_node(self, state: ConversationState) -> ConversationState:
        """Router agent node"""
        logger.debug("Executing router node")
        return await self.router_agent.process(state)

    async def _course_node(self, state: ConversationState) -> ConversationState:
        """Course agent node"""
        logger.debug("Executing course node")
        return await self.course_agent.process(state)

    async def _fees_node(self, state: ConversationState) -> ConversationState:
        """Fees agent node"""
        logger.debug("Executing fees node")
        return await self.fees_agent.process(state)

    async def _admission_node(self, state: ConversationState) -> ConversationState:
        """Admission agent node"""
        logger.debug("Executing admission node")
        return await self.admission_agent.process(state)

    async def _followup_node(self, state: ConversationState) -> ConversationState:
        """Follow-up agent node"""
        logger.debug("Executing followup node")
        return await self.followup_agent.process(state)

    def _route_after_greeting(self, state: ConversationState) -> str:
        """Decide next step after greeting"""

        # Check if user has provided name and is ready
        ready = state.get("context", {}).get("ready_for_inquiry", False)

        if ready:
            return "router"
        else:
            return "end"  # Wait for user's next message

    def _route_to_specialist(self, state: ConversationState) -> str:
        """Route to appropriate specialist agent based on intent"""

        intent = state.get("context", {}).get("current_intent", "general")

        intent_map = {
            "course": "course",
            "fees": "fees",
            "admission": "admission",
            "followup": "followup",
            "general": "followup"  # General queries go to followup for contact info
        }

        return intent_map.get(intent, "end")

    def _route_after_specialist(self, state: ConversationState) -> str:
        """Decide what to do after specialist agent"""

        # Check if there are more messages to process
        messages = state.get("messages", [])

        # If last message is from user, route to router
        if messages and messages[-1].get("role") == "user":
            return "router"

        # Otherwise, end (wait for user's next message)
        return "end"

    async def process_message(self, session_id: str, user_message: str, existing_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user message through the workflow

        Args:
            session_id: Unique session identifier
            user_message: User's message text
            existing_state: Previous conversation state (if any)

        Returns:
            Updated conversation state with agent's response
        """

        # Initialize or update state
        if existing_state:
            state = existing_state
        else:
            state = {
                "session_id": session_id,
                "messages": [],
                "user_info": {},
                "context": {},
                "visited_agents": [],
                "topics_discussed": [],
                "conversation_count": 0
            }

        # Add user message to state
        state["messages"].append({
            "role": "user",
            "content": user_message
        })

        # Check if user is providing their name (waiting_for_name context)
        if state.get("context", {}).get("waiting_for_name"):
            # Extract name
            name = self.greeting_agent.extract_name_from_message(user_message)
            state["user_info"]["name"] = name
            state["context"]["waiting_for_name"] = False
            logger.info(f"Captured user name: {name}")

        # Run through workflow
        try:
            result = await self.graph.ainvoke(state)

            # Increment conversation count
            result["conversation_count"] = result.get("conversation_count", 0) + 1

            logger.info(f"Processed message for session {session_id}, conversation count: {result['conversation_count']}")

            return result

        except Exception as e:
            logger.error(f"Error processing message: {e}")

            # Return state with error message
            state["messages"].append({
                "role": "assistant",
                "content": "I apologize, but I encountered an error. Please try again or contact our helpline at 1800-123-4567."
            })

            return state


# Global workflow instance
_workflow_instance = None


def get_workflow() -> ParulAdmissionWorkflow:
    """Get global workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ParulAdmissionWorkflow()
    return _workflow_instance
