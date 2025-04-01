import json
from datetime import datetime, timedelta

class VaccineRecommender:
    def __init__(self, nip_file, iap_file):
        """Initialize with both schedule files"""
        with open(nip_file) as f:
            self.nip_schedule = json.load(f)["schedule"]
        with open(iap_file) as f:
            self.iap_data = json.load(f)
            self.iap_schedule = self.iap_data["schedule"]
            self.age_units = self.iap_data["age_units"]
            self.categories = self.iap_data["categories"]
    
    def parse_age(self, age_str, schedule_type="nip"):
        """Convert age string to days for comparison"""
        if not age_str:
            return float('inf')
            
        age_str = age_str.lower().strip()
        
        if age_str == "at birth":
            return 0
        if age_str == "annually from 6m":
            return 6 * 30  # 6 months in days
        if age_str == "post-exposure":
            return float('inf')  # Special case
        
        # Handle NIP schedule ages
        if schedule_type == "nip":
            if "within" in age_str:
                if "24 hours" in age_str:
                    return 1  # 1 day
                elif "15 days" in age_str:
                    return 15
            
            # Extract numeric value
            numeric_part = ''.join(c for c in age_str if c.isdigit())
            if not numeric_part:
                return float('inf')
                
            value = int(numeric_part)
            
            if "week" in age_str:
                return value * 7
            elif "month" in age_str:
                return value * 30
            elif "year" in age_str:
                return value * 365
            elif "day" in age_str:
                return value
        
        # Handle IAP schedule ages
        elif schedule_type == "iap":
            if age_str.endswith('w'):
                return int(age_str[:-1]) * 7
            elif age_str.endswith('m'):
                return int(age_str[:-1]) * 30
            elif age_str.endswith('y'):
                return int(age_str[:-1]) * 365
        
        return float('inf')  # Default for unrecognized formats
    
    def get_nip_recommendations(self, child_age_days):
        """Get NIP vaccines due at or before child_age_days"""
        recommendations = []
        
        for vaccine in self.nip_schedule:
            due_age = self.parse_age(vaccine["due_age"], "nip")
            
            max_age = float('inf')
            if "max_age" in vaccine:
                max_age = self.parse_age(vaccine["max_age"], "nip")
            
            if due_age <= child_age_days <= max_age:
                recommendations.append({
                    **vaccine,
                    "schedule_type": "NIP",
                    "category": "Government Program"
                })
                
        return recommendations
    
    def get_iap_recommendations(self, child_age_days):
        """Get IAP vaccines due at or before child_age_days"""
        recommendations = []
        
        for vaccine in self.iap_schedule:
            for age_str in vaccine["schedule"]:
                if age_str == "Annually from 6m":
                    if child_age_days >= 6*30:  # 6 months
                        recommendations.append({
                            **vaccine,
                            "due_age": "Annual",
                            "schedule_type": "IAP",
                            "is_annual": True
                        })
                    continue
                elif age_str == "Post-exposure":
                    continue  # Skip post-exposure vaccines
                
                due_age = self.parse_age(age_str, "iap")
                max_age = due_age + 30  # 1 month window
                
                if due_age <= child_age_days <= max_age:
                    recommendations.append({
                        **vaccine,
                        "due_age": age_str,
                        "schedule_type": "IAP",
                        "is_annual": False
                    })
        
        return recommendations
    
    def get_all_schedules(self):
        """Get complete schedules from both programs"""
        return {
            "nip": self.nip_schedule,
            "iap": self.iap_schedule,
            "iap_categories": self.categories
        }
    
    def get_formatted_schedule(self, schedule_type):
        """Get schedule in a more user-friendly format"""
        if schedule_type == "nip":
            return self.nip_schedule
        elif schedule_type == "iap":
            formatted = []
            for vaccine in self.iap_schedule:
                formatted_doses = []
                for dose in vaccine["schedule"]:
                    if dose == "Birth":
                        formatted_doses.append("At birth")
                    elif dose == "Annually from 6m":
                        formatted_doses.append("Annually (starting at 6 months)")
                    elif dose == "Post-exposure":
                        formatted_doses.append("Post-exposure only")
                    else:
                        try:
                            unit = self.age_units.get(dose[-1], "")
                            value = dose[:-1]
                            formatted_doses.append(f"{value} {unit}")
                        except (IndexError, KeyError):
                            formatted_doses.append(dose)
                
                formatted.append({
                    "vaccine": vaccine["vaccine"],
                    "schedule": ", ".join(formatted_doses),
                    "category": vaccine["category"]
                })
            return formatted
        return []