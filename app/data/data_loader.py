"""
Data loader for JSON-based knowledge base
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataLoader:
    """Load and manage knowledge base data from JSON files"""

    def __init__(self, data_dir: str = "./app/data"):
        self.data_dir = Path(data_dir)
        self._courses: Optional[List[Dict]] = None
        self._fees: Optional[List[Dict]] = None
        self._scholarships: Optional[Dict] = None
        self._admission: Optional[Dict] = None

        # Load all data on initialization
        self.load_all()

    def load_json(self, filename: str) -> Any:
        """Load a JSON file"""
        file_path = self.data_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {filename} successfully")
            return data
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON in {filename}: {e}")
            return None

    def load_all(self):
        """Load all data files"""
        logger.info("Loading all knowledge base data...")

        courses_data = self.load_json("courses.json")
        self._courses = courses_data.get("courses", []) if courses_data else []

        fees_data = self.load_json("fees.json")
        self._fees = fees_data.get("fee_structure", []) if fees_data else []

        self._scholarships = self.load_json("scholarships.json")
        self._admission = self.load_json("admission.json")

        logger.info(f"Loaded {len(self._courses)} courses, {len(self._fees)} fee structures")

    @property
    def courses(self) -> List[Dict]:
        """Get all courses"""
        return self._courses or []

    @property
    def fees(self) -> List[Dict]:
        """Get all fee structures"""
        return self._fees or []

    @property
    def scholarships(self) -> Dict:
        """Get scholarship data"""
        return self._scholarships or {}

    @property
    def admission(self) -> Dict:
        """Get admission process data"""
        return self._admission or {}

    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """Get course by ID"""
        for course in self.courses:
            if course.get("id") == course_id:
                return course
        return None

    def get_course_by_name(self, name: str) -> Optional[Dict]:
        """Get course by name (fuzzy match)"""
        name_lower = name.lower()
        for course in self.courses:
            if name_lower in course.get("name", "").lower():
                return course
        return None

    def search_courses(self, query: str) -> List[Dict]:
        """Search courses by name, description, or department"""
        query_lower = query.lower()
        results = []
        for course in self.courses:
            if (query_lower in course.get("name", "").lower() or
                query_lower in course.get("description", "").lower() or
                query_lower in course.get("department", "").lower()):
                results.append(course)
        return results

    def get_fees_by_course_id(self, course_id: str) -> Optional[Dict]:
        """Get fee structure for a course"""
        for fee in self.fees:
            if fee.get("course_id") == course_id:
                return fee
        return None

    def calculate_scholarship(self, percentage: float, course_id: str) -> Dict:
        """Calculate scholarship based on percentage"""
        result = {
            "eligible": False,
            "scholarship_name": None,
            "discount_percentage": 0,
            "original_tuition": 0,
            "discount_amount": 0,
            "final_tuition": 0
        }

        # Get course fees
        fee_structure = self.get_fees_by_course_id(course_id)
        if not fee_structure:
            return result

        original_tuition = fee_structure["breakdown"]["tuition"]
        result["original_tuition"] = original_tuition

        # Check merit-based scholarship
        merit_scholarships = self.scholarships.get("scholarship_rules", {}).get("merit_based", {}).get("tiers", [])

        for tier in merit_scholarships:
            if tier["min_percentage"] <= percentage <= tier["max_percentage"]:
                result["eligible"] = True
                result["scholarship_name"] = "Merit Scholarship"
                result["discount_percentage"] = tier["discount_percentage"]
                result["discount_amount"] = (original_tuition * tier["discount_percentage"]) / 100
                result["final_tuition"] = original_tuition - result["discount_amount"]
                break

        return result

    def get_courses_by_level(self, level: str) -> List[Dict]:
        """Get courses by level (undergraduate/postgraduate)"""
        return [c for c in self.courses if c.get("level") == level]

    def get_courses_by_department(self, department: str) -> List[Dict]:
        """Get courses by department"""
        return [c for c in self.courses if c.get("department", "").lower() == department.lower()]


# Global data loader instance
data_loader = DataLoader()


def get_data_loader() -> DataLoader:
    """Get global data loader instance"""
    return data_loader
