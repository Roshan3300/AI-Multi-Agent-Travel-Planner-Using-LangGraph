import os
import re
from dotenv import load_dotenv
from tools.tavily_tool import tavily_search

load_dotenv()

TRAIN_API_KEY = os.getenv("TRAIN_API_KEY")
TRAIN_API_URL = os.getenv("TRAIN_API_URL")


def parse_train_route(query: str) -> tuple[str, str]:
    """Extract origin and destination from user query."""
    match = re.search(r"from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+)", query, re.IGNORECASE)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        return origin, destination

    match = re.search(r"to\s+([A-Za-z\s]+)", query, re.IGNORECASE)
    if match:
        return "origin", match.group(1).strip()

    return None, None


def is_train_feasible(origin: str, destination: str) -> bool:
    """Check if train travel is feasible (primarily for India)."""
    if not origin or not destination:
        return False
    
    # Basic distance heuristic - trains viable for >100km routes
    # India has extensive rail network
    india_cities = ["mumbai", "delhi", "bangalore", "hyderabad", "kolkata", "chennai", 
                    "pune", "jaipur", "ahmedabad", "lucknow", "indore", "surat", "bhopal"]
    
    origin_lower = origin.lower()
    dest_lower = destination.lower()
    
    # If both are in India, trains are feasible
    for city in india_cities:
        if city in origin_lower or city in dest_lower:
            return True
    
    # Generic India keywords
    if any(kw in origin_lower or kw in dest_lower for kw in ["india", "delhi", "mumbai", "bangalore"]):
        return True
    
    # If domestic/same country trip mentioned
    return origin_lower != dest_lower


def train_search(query: str) -> str:
    """Search for real train schedules using web search, focusing on Indian routes."""
    origin, destination = parse_train_route(query)
    
    if not is_train_feasible(origin, destination):
        return ""
    
    # Try official API first if configured
    if TRAIN_API_KEY and TRAIN_API_URL:
        try:
            import requests
            response = requests.get(
                TRAIN_API_URL,
                params={"api_key": TRAIN_API_KEY, "q": f"{origin} to {destination}", "limit": 5},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "results" in data:
                routes = []
                for item in data["results"][:5]:
                    routes.append(
                        f"🚂 {item.get('origin', origin)} → {item.get('destination', destination)} | "
                        f"Depart: {item.get('departure_time', 'TBD')} | "
                        f"Duration: {item.get('duration', 'TBD')}"
                    )
                if routes:
                    return "\n".join(routes)
        except Exception:
            pass
    
    # Fall back to web search for real train info
    search_query = f"train schedule {origin} to {destination} india rail ticket price"
    train_results = tavily_search(search_query)
    
    if train_results:
        return f"🚂 Train Travel Options:\n{train_results}"
    
    # Only return placeholder if nothing found and region is India
    if origin and destination:
        return (
            f"🚂 Train Routes Available:\n"
            f"- Route: {origin} to {destination}\n"
            f"- Availability: Check Indian Railways website or RailYatri app\n"
            f"- Classes: Sleeper, 1AC, 2AC, 3AC, General available\n"
            f"- Booking: Visit indianrailways.gov.in or authorized agents"
        )
    
    return ""
