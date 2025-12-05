"""
Fees & Payment Agent
Provides fee structure, payment options, and calculates scholarships
"""
from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.data.data_loader import get_data_loader
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FeesAgent(BaseAgent):
    """Agent for fees and payment queries"""

    def __init__(self):
        super().__init__("fees")
        self.data_loader = get_data_loader()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process fees information request"""

        # Mark as visited
        state = self._update_visited_agents(state)

        # Get selected course from context
        course_id = self._get_context(state, "selected_course")

        # Get last user message
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if not last_message or last_message.get("role") != "user":
            return state

        user_query = last_message.get("content", "").lower()

        # If no course selected, try to identify from query
        if not course_id:
            from app.agents.course_agent import CourseAgent
            course_agent = CourseAgent()
            course = course_agent._identify_course(user_query)
            if course:
                course_id = course["id"]
                state = self._set_context(state, "selected_course", course_id)

        if course_id:
            # Check if user mentioned percentage (for scholarship)
            percentage = self._extract_percentage(user_query)

            if percentage:
                response = self._generate_fees_with_scholarship(course_id, percentage)
                state = self._set_context(state, "scholarship_percentage", percentage)
            else:
                response = self._generate_fees_response(course_id, user_query)

        else:
            response = "I'd be happy to help with fee information! Which course are you interested in? We offer B.Tech CSE, B.Tech Mechanical, MBA, BBA, and B.Pharma."

        state = self._add_message(state, response)

        # Add to topics discussed
        if "topics_discussed" not in state:
            state["topics_discussed"] = []
        if "Fees" not in state["topics_discussed"]:
            state["topics_discussed"].append("Fees")

        return state

    def _extract_percentage(self, query: str) -> float:
        """Extract percentage from user query"""
        import re

        # Look for patterns like "85%", "85 percent", "scored 85"
        patterns = [
            r'(\d+\.?\d*)\s*%',
            r'(\d+\.?\d*)\s*percent',
            r'scored\s+(\d+\.?\d*)',
            r'got\s+(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*in\s+12th'
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def _generate_fees_response(self, course_id: str, query: str) -> str:
        """Generate fee structure response"""

        fee_data = self.data_loader.get_fees_by_course_id(course_id)
        course = self.data_loader.get_course_by_id(course_id)

        if not fee_data or not course:
            return "Sorry, I couldn't find fee information for that course."

        course_name = course["name"]
        annual_fee = fee_data["annual_fee"]
        breakdown = fee_data["breakdown"]

        response = f"""**Fee Structure for {course_name}**

**Annual Fee:** ₹{annual_fee:,}

**Breakdown:**"""

        for key, value in breakdown.items():
            label = key.replace("_", " ").title()
            response += f"\n- {label}: ₹{value:,}"

        # Payment options
        if "payment" in query or "installment" in query:
            response += "\n\n**Payment Options:**\n"
            for option in fee_data["payment_options"]:
                response += f"\n{option['type'].title()}: {option['description']}"
                if "discount_percentage" in option:
                    response += f" - Save {option['discount_percentage']}% (₹{option['amount']:,})"
                else:
                    response += f" - ₹{option['amount_per_installment']:,} per installment"

        # Additional costs
        if "hostel" in query or "total" in query or "additional" in query:
            additional = fee_data["additional_costs"]
            response += "\n\n**Additional Costs (Optional):**"
            response += f"\n- Hostel (AC): ₹{additional['hostel']:,}/year (includes mess)"
            if additional.get("books_approx"):
                response += f"\n- Books: ₹{additional['books_approx']:,}/year (approx.)"

        # Suggest scholarship
        response += "\n\n💡 You may be eligible for scholarships based on your 12th percentage! Would you like me to calculate your scholarship?"

        return response

    def _generate_fees_with_scholarship(self, course_id: str, percentage: float) -> str:
        """Generate fee response with scholarship calculation"""

        fee_data = self.data_loader.get_fees_by_course_id(course_id)
        course = self.data_loader.get_course_by_id(course_id)
        scholarship = self.data_loader.calculate_scholarship(percentage, course_id)

        if not fee_data or not course:
            return "Sorry, I couldn't find fee information for that course."

        course_name = course["name"]
        annual_fee = fee_data["annual_fee"]

        response = f"""**Fee Structure for {course_name} with Scholarship**

**Your 12th Percentage:** {percentage}%\n"""

        if scholarship["eligible"]:
            response += f"""
✅ **Congratulations! You're eligible for {scholarship['scholarship_name']}**

**Scholarship Details:**
- Discount: {scholarship['discount_percentage']}% on tuition fees
- Original Tuition: ₹{scholarship['original_tuition']:,}
- Scholarship Amount: ₹{scholarship['discount_amount']:,}
- **Your Tuition: ₹{scholarship['final_tuition']:,}**

**Total Annual Fee after Scholarship:**
- Tuition: ₹{scholarship['final_tuition']:,}"""

            # Add other fees
            other_fees = annual_fee - fee_data["breakdown"]["tuition"]
            total_with_scholarship = scholarship['final_tuition'] + other_fees

            response += f"\n- Other Fees: ₹{other_fees:,}"
            response += f"\n- **Total: ₹{total_with_scholarship:,}**"

            response += f"\n\n**You Save: ₹{scholarship['discount_amount']:,} per year!**"

            # Additional discounts
            response += "\n\n**Additional Discounts Available:**"
            response += "\n- Early Bird (apply before 15th March): 5% extra"
            response += "\n- Sibling Discount: 10% if you have a sibling at Parul"

            response += f"\n\nWith all discounts, your fee could be as low as ₹{int(total_with_scholarship * 0.85):,}/year!"

        else:
            response += f"""
**Scholarship Status:** Not eligible for merit scholarship
- Merit scholarships require 70%+ in 12th standard

**Your Fee:** ₹{annual_fee:,}/year

**Other Scholarship Options:**
- Sports Scholarship (if you're a state/national player)
- EWS Scholarship (if family income < ₹3 lakhs/year)
- Government schemes (Post-Matric, PM Scholarship)
"""

        response += "\n\nWould you like to know about the admission process or payment options?"

        return response
