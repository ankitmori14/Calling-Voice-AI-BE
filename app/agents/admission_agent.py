"""
Admission Process Agent
Provides information about admission process, requirements, and deadlines
"""
from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.data.data_loader import get_data_loader
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AdmissionAgent(BaseAgent):
    """Agent for admission process queries"""

    def __init__(self):
        super().__init__("admission")
        self.data_loader = get_data_loader()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process admission information request"""

        # Mark as visited
        state = self._update_visited_agents(state)

        # Get last user message
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if not last_message or last_message.get("role") != "user":
            return state

        user_query = last_message.get("content", "").lower()

        # Get selected course for specific information
        course_id = self._get_context(state, "selected_course")

        # Determine what aspect of admission process user is asking about
        if any(word in user_query for word in ["document", "required", "certificate", "marksheet"]):
            response = self._get_documents_info()
        elif any(word in user_query for word in ["date", "deadline", "when", "last date"]):
            response = self._get_important_dates()
        elif any(word in user_query for word in ["entrance", "exam", "test", "jee", "cat"]):
            response = self._get_entrance_test_info(course_id)
        elif any(word in user_query for word in ["step", "process", "procedure", "how to"]):
            response = self._get_full_admission_process()
        else:
            # Give overview
            response = self._get_admission_overview()

        state = self._add_message(state, response)

        # Add to topics discussed
        if "topics_discussed" not in state:
            state["topics_discussed"] = []
        if "Admission Process" not in state["topics_discussed"]:
            state["topics_discussed"].append("Admission Process")

        return state

    def _get_admission_overview(self) -> str:
        """Get overview of admission process"""

        admission_data = self.data_loader.admission.get("admission_process", {})

        response = """**Parul University Admission Process**

The admission process is simple and straightforward:

**5 Easy Steps:**
1. **Online Application** - Fill form and pay ₹1,000 fee
2. **Entrance Test** - Take PU-CET or submit JEE/CAT scores
3. **Counseling** - Choose your branch based on rank
4. **Document Verification** - Submit original documents
5. **Fee Payment** - Pay first semester fee and confirm admission

**Timeline:**
- Applications Open: 1st January 2025
- Last Date to Apply: 30th April 2025
- Entrance Test: 15th May 2025
- Counseling: 1st-15th June 2025
- Classes Start: 1st July 2025

Would you like detailed information about any specific step?"""

        return response

    def _get_full_admission_process(self) -> str:
        """Get detailed admission process"""

        response = """**Detailed Admission Process**

**Step 1: Online Application**
- Visit: admissions.paruluniversity.ac.in
- Fill application form (takes 15 minutes)
- Upload photo and documents
- Pay application fee: ₹1,000
- Deadline: 30th April 2025
- ⚡ Apply before 15th March for 5% early bird discount!

**Step 2: Entrance Test**
Choose one option:
a) PU-CET (Parul University Test)
   - Date: 15th May 2025
   - Duration: 2 hours, 100 questions
   - Online test from home
   - Syllabus: 12th standard (PCM/PCB)

b) Submit JEE Main scores (for engineering)
c) Submit CAT/MAT scores (for MBA)
d) Direct admission for BBA based on 12th marks

**Step 3: Counseling**
- Online counseling: 1st-15th June 2025
- Choose branch preference based on rank
- Seat allotment in 2 rounds
- Accept/reject seat online

**Step 4: Document Verification**
Upload scanned copies and bring originals on joining:
- 10th & 12th marksheets
- Transfer certificate
- Aadhar card
- Character certificate
- Passport size photos (6 nos)
- Caste certificate (if applicable)

**Step 5: Fee Payment**
- Pay first semester fee within 7 days
- Scholarships auto-applied if eligible
- Payment modes: Online, DD, Bank Transfer

**Contact for Help:**
- Helpline: 1800-123-4567
- WhatsApp: +91-98765-43210
- Email: admissions@paruluniversity.ac.in

Need help with any specific step?"""

        return response

    def _get_documents_info(self) -> str:
        """Get required documents information"""

        response = """**Required Documents for Admission**

**Mandatory Documents:**
✓ 10th Marksheet (Original + 2 photocopies)
✓ 12th Marksheet (Original + 2 photocopies)
✓ 12th Passing Certificate (Original + 2 photocopies)
✓ Aadhar Card (Original + 2 photocopies)
✓ Transfer Certificate from previous institution (Original)
✓ Character Certificate (Original)
✓ Passport Size Photos (6 numbers)

**Additional Documents (if applicable):**
- Migration Certificate (if from different board/university)
- Caste Certificate (for reservation/scholarship)
- Income Certificate (for EWS/scholarship)
- Sports Certificate (for sports quota)
- Domicile Certificate (if required)

**Document Verification:**
- Upload scanned copies during online application
- Bring originals for physical verification on joining day
- All documents should be attested

**Important Notes:**
- Keep extra photocopies for your records
- Ensure all certificates are from recognized boards
- Documents in languages other than English/Hindi need translation

Need more information about the admission process?"""

        return response

    def _get_important_dates(self) -> str:
        """Get important dates"""

        dates = self.data_loader.admission.get("important_dates", {})

        response = """**Important Admission Dates 2025**

📅 **Application Period:**
- Applications Open: 1st January 2025
- Early Bird Deadline: **15th March 2025** (5% discount)
- Application Closes: 30th April 2025

📅 **Entrance Test:**
- PU-CET Exam Date: 15th May 2025
- Result Declaration: 25th May 2025

📅 **Counseling:**
- Round 1: 1st June - 7th June 2025
- Round 2: 8th June - 15th June 2025

📅 **Session Start:**
- Classes Begin: 1st July 2025

**⚡ Important:**
- Apply before 15th March to get 5% early bird discount
- Entrance test is online, you can take it from home
- Document verification can be done online

**Missed a deadline?**
Don't worry! Contact our admission helpline for special late admission options.

Would you like to know about the entrance test or required documents?"""

        return response

    def _get_entrance_test_info(self, course_id: str = None) -> str:
        """Get entrance test information"""

        response = """**Entrance Test Options**

**For Engineering (B.Tech):**
Option 1: PU-CET (Parul University Common Entrance Test)
- Date: 15th May 2025
- Mode: Online from home
- Duration: 2 hours
- Questions: 100 (PCM based)
- Syllabus: 12th standard

Option 2: JEE Main Scores
- Submit your JEE Main scorecard
- No separate test needed

**For MBA:**
- Submit CAT or MAT scorecard
- OR take PU management entrance test

**For BBA:**
- Direct admission based on 12th marks
- No entrance test required

**For B.Pharma:**
- PU-CET (PCB/PCM based)
- OR relevant state/national exam scores

**Test Preparation:**
- Syllabus: Based on 12th standard
- Sample papers available on website
- Mock tests provided after registration

**Registration:**
- Register while filling application form
- Test link sent via email
- Can be taken from home with webcam

Need help with application process or have questions about eligibility?"""

        return response
