"""
Course Information Agent
Provides information about courses, programs, eligibility, syllabus
"""
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.data.data_loader import get_data_loader
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CourseAgent(BaseAgent):
    """Agent for course information queries"""

    def __init__(self):
        super().__init__("course")
        self.data_loader = get_data_loader()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process course information request"""

        # Mark as visited
        state = self._update_visited_agents(state)

        # Get last user message
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if not last_message or last_message.get("role") != "user":
            return state

        user_query = last_message.get("content", "").lower()

        # Identify which course user is asking about
        course = self._identify_course(user_query)

        if course:
            response = self._generate_course_response(course, user_query)
            state = self._set_context(state, "selected_course", course["id"])

            # Add to topics discussed
            if "topics_discussed" not in state:
                state["topics_discussed"] = []
            if course["name"] not in state["topics_discussed"]:
                state["topics_discussed"].append(course["name"])

        else:
            # Show available courses
            response = self._list_available_courses()

        state = self._add_message(state, response)
        return state

    def _identify_course(self, query: str) -> Dict[str, Any]:
        """Identify which course the user is asking about"""

        # Keywords for each course
        course_keywords = {
            "BTECH_CSE": ["computer science", "cse", "cs", "software", "it", "information technology", "btech cse", "b.tech cse"],
            "BTECH_MECH": ["mechanical", "mech", "automobile", "manufacturing", "btech mech", "b.tech mech"],
            "MBA": ["mba", "master of business", "business administration", "management"],
            "BBA": ["bba", "bachelor of business", "business administration"],
            "BPHARMA": ["pharmacy", "pharma", "b.pharma", "b pharmacy", "pharmaceutical"]
        }

        for course_id, keywords in course_keywords.items():
            if any(keyword in query for keyword in keywords):
                return self.data_loader.get_course_by_id(course_id)

        # Try fuzzy search
        results = self.data_loader.search_courses(query)
        if results:
            return results[0]

        return None

    def _generate_course_response(self, course: Dict, query: str) -> str:
        """Generate detailed course information response"""

        name = course["name"]
        duration = course["duration_years"]
        seats = course["seats"]
        description = course["description"]
        eligibility = course["eligibility"]

        # Base information
        response = f"""**{name}**

{description}

**Duration:** {duration} years ({course['duration_semesters']} semesters)
**Seats Available:** {seats}

**Eligibility:**
- Education: {eligibility['education']}"""

        if "subjects" in eligibility:
            response += f"\n- Required Subjects: {', '.join(eligibility['subjects'])}"
        if "minimum_percentage" in eligibility:
            response += f"\n- Minimum Percentage: {eligibility['minimum_percentage']}%"

        # Add specializations if query mentions it
        if "specialization" in query or "branch" in query:
            if course.get("specializations"):
                response += f"\n\n**Specializations Available:**\n"
                for spec in course["specializations"]:
                    response += f"- {spec}\n"

        # Add subjects if query mentions syllabus
        if "subject" in query or "syllabus" in query or "curriculum" in query:
            if course.get("subjects"):
                response += f"\n**Key Subjects:**\n"
                for subject in course["subjects"][:6]:  # Show first 6
                    response += f"- {subject}\n"

        # Add career options
        if "career" in query or "job" in query or "placement" in query:
            if course.get("career_options"):
                response += f"\n**Career Opportunities:**\n"
                for career in course["career_options"]:
                    response += f"- {career}\n"

        # Suggest next steps
        response += f"\n\nWould you like to know about the fee structure, admission process, or scholarship options for {name}?"

        return response

    def _list_available_courses(self) -> str:
        """List all available courses"""

        courses = self.data_loader.courses

        response = "We offer the following programs at Parul University:\n\n"

        # Group by level
        ug_courses = [c for c in courses if c["level"] == "undergraduate"]
        pg_courses = [c for c in courses if c["level"] == "postgraduate"]

        if ug_courses:
            response += "**Undergraduate Programs:**\n"
            for course in ug_courses:
                response += f"- {course['name']} ({course['duration_years']} years)\n"

        if pg_courses:
            response += "\n**Postgraduate Programs:**\n"
            for course in pg_courses:
                response += f"- {course['name']} ({course['duration_years']} years)\n"

        response += "\nWhich program would you like to know more about?"

        return response
