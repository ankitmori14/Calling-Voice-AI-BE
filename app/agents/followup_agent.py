"""
Follow-up Agent
Collects contact information, schedules campus visits, sends brochures
"""
from typing import Dict, Any
import re
from app.agents.base_agent import BaseAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FollowupAgent(BaseAgent):
    """Agent for follow-up actions and contact collection"""

    def __init__(self):
        super().__init__("followup")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process follow-up requests"""

        # Mark as visited
        state = self._update_visited_agents(state)

        # Get last user message
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if not last_message or last_message.get("role") != "user":
            return state

        user_query = last_message.get("content", "").lower()

        # Extract contact information if provided
        email = self._extract_email(user_query)
        phone = self._extract_phone(user_query)

        if email:
            state = self._set_user_info(state, "email", email)
        if phone:
            state = self._set_user_info(state, "phone", phone)

        # Determine what user wants
        if any(word in user_query for word in ["campus", "visit", "tour", "see"]):
            response = self._handle_campus_visit_request(state)

        elif any(word in user_query for word in ["brochure", "pdf", "document", "send", "share"]):
            response = self._handle_brochure_request(state)

        elif any(word in user_query for word in ["call", "callback", "contact", "talk", "counselor"]):
            response = self._handle_callback_request(state)

        elif email or phone:
            # User provided contact, acknowledge and ask what they want
            response = self._acknowledge_contact(state)

        else:
            # General follow-up offer
            response = self._offer_followup_options(state)

        state = self._add_message(state, response)

        # Add to topics discussed
        if "topics_discussed" not in state:
            state["topics_discussed"] = []
        if "Follow-up" not in state["topics_discussed"]:
            state["topics_discussed"].append("Follow-up")

        return state

    def _extract_email(self, text: str) -> str:
        """Extract email from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        if match:
            return match.group(0)
        return None

    def _extract_phone(self, text: str) -> str:
        """Extract Indian phone number from text"""
        # Pattern for Indian phone numbers (10 digits, optional +91)
        phone_patterns = [
            r'(\+91[\s-]?)?[6-9]\d{9}',
            r'\b\d{10}\b'
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                # Clean up
                phone = re.sub(r'[\s-]', '', phone)
                if len(phone) == 10 and phone[0] in '6789':
                    return phone
                elif len(phone) == 12 and phone.startswith('91'):
                    return phone[2:]

        return None

    def _handle_campus_visit_request(self, state: Dict[str, Any]) -> str:
        """Handle campus visit booking request"""

        user_name = self._get_user_info(state, "name", "there")
        email = self._get_user_info(state, "email")
        phone = self._get_user_info(state, "phone")

        response = f"""**Campus Visit Booking**

Great choice, {user_name}! I'd love to arrange a campus tour for you.

**Our campus tour includes:**
- Department and lab visits
- Library and learning centers
- Hostel facilities
- Sports complex
- Interaction with faculty and students
- Admission guidance session

**Available Slots:**
- Monday to Saturday: 10:00 AM - 5:00 PM
- Duration: 2-3 hours

**To confirm your visit, I need:**"""

        if not phone:
            response += "\n- Your mobile number"
        if not email:
            response += "\n- Your email address"

        if phone and email:
            response += f"""

✅ **Your Details:**
- Mobile: {phone}
- Email: {email}

Your campus visit request has been noted! Our admission team will contact you within 2 hours to confirm the date and time.

You'll receive:
- Confirmation SMS
- Google Maps location link
- Visitor pass QR code
- Campus tour schedule"""

        else:
            response += "\n\nPlease share your contact details so we can confirm your visit."

        return response

    def _handle_brochure_request(self, state: Dict[str, Any]) -> str:
        """Handle brochure send request"""

        user_name = self._get_user_info(state, "name", "there")
        email = self._get_user_info(state, "email")
        phone = self._get_user_info(state, "phone")
        selected_course = self._get_context(state, "selected_course")

        response = f"""**Course Brochure & Information**

Perfect, {user_name}! I can send you detailed information about"""

        if selected_course:
            course = None
            from app.data.data_loader import get_data_loader
            course = get_data_loader().get_course_by_id(selected_course)
            if course:
                response += f" {course['name']}"
        else:
            response += " our programs"

        response += ".\n\n**What you'll receive:**"
        response += "\n- Detailed course brochure"
        response += "\n- Fee structure PDF"
        response += "\n- Placement statistics"
        response += "\n- Scholarship information"
        response += "\n- Application form link"

        if email or phone:
            response += "\n\n**Sending to:**"
            if email:
                response += f"\n📧 Email: {email}"
            if phone:
                response += f"\n📱 WhatsApp: {phone}"

            response += "\n\n✅ You'll receive all materials within 5 minutes!"

        else:
            response += "\n\n**Where should I send it?**"
            response += "\nPlease provide your:"
            response += "\n- Email address, OR"
            response += "\n- WhatsApp number"

        return response

    def _handle_callback_request(self, state: Dict[str, Any]) -> str:
        """Handle callback/counselor request"""

        user_name = self._get_user_info(state, "name", "there")
        phone = self._get_user_info(state, "phone")

        response = f"""**Callback Request**

Absolutely, {user_name}! I'll connect you with our admission counselor.

**Our counselors can help with:**
- Detailed course guidance
- Career counseling
- Scholarship evaluation
- Application assistance
- Special admission cases

"""

        if phone:
            response += f"""✅ **Your Contact:** {phone}

**Callback Options:**
1. Within 30 minutes (9 AM - 6 PM on working days)
2. Schedule for later (choose your preferred time)

Our counselor will call you within 30 minutes during working hours (Mon-Sat, 9 AM - 6 PM).

**Meanwhile, is there anything else you'd like to know?**"""

        else:
            response += """**To arrange a callback, I need:**
- Your mobile number
- Preferred time to call (optional)

Please share your number and I'll have our counselor reach out!"""

        return response

    def _acknowledge_contact(self, state: Dict[str, Any]) -> str:
        """Acknowledge contact information received"""

        email = self._get_user_info(state, "email")
        phone = self._get_user_info(state, "phone")
        user_name = self._get_user_info(state, "name", "there")

        response = f"Thank you for sharing your details, {user_name}!\n\n"

        response += "**Your Contact Information:**\n"
        if email:
            response += f"📧 Email: {email}\n"
        if phone:
            response += f"📱 Phone: {phone}\n"

        response += "\n**What would you like me to do?**\n"
        response += "1. Send course brochure and fee details\n"
        response += "2. Schedule a campus visit\n"
        response += "3. Arrange a callback from admission counselor\n"
        response += "4. All of the above\n\n"

        response += "Just let me know your preference!"

        return response

    def _offer_followup_options(self, state: Dict[str, Any]) -> str:
        """Offer general follow-up options"""

        user_name = self._get_user_info(state, "name", "there")

        response = f"""**How Can I Help You Further, {user_name}?**

I can assist you with:

📱 **Get in Touch:**
- Schedule a campus visit
- Arrange callback from admission counselor
- Send detailed brochure via Email/WhatsApp

📞 **Contact Information:**
- Helpline: 1800-123-4567 (Toll-free)
- WhatsApp: +91-98765-43210
- Email: admissions@paruluniversity.ac.in

🏛️ **Visit Us:**
Parul University
P.O. Limda, Waghodia
Vadodara - 391760, Gujarat

📝 **Quick Actions:**
- Apply Online: admissions.paruluniversity.ac.in
- Virtual Campus Tour: Available on website

What would you like to do next?"""

        return response
