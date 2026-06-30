import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


def build_flight_query(query: str) -> str:
    match = re.search(r"from\s+(.+?)\s+to\s+(.+?)(?:$|\s)", query, re.IGNORECASE)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        return f"{origin} to {destination}"

    match = re.search(r"to\s+(.+?)(?:$|\s)", query, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return query.strip()


def search_flights(query):
    if not API_KEY:
        return "Flight search unavailable: missing API key."

    url = "https://api.aviationstack.com/v1/flights"
    params = {
        "access_key": API_KEY,
        "limit": 5,
        "query": build_flight_query(query)
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return "Flight search failed: the API returned an unexpected non-JSON response."
        data = response.json()
    except Exception as exc:
        return f"Flight search failed: {exc}"

    flights = []
    if isinstance(data, dict) and "data" in data:
        for flight in data["data"][:5]:
            airline = flight.get("airline", {}).get("name", "Unknown")
            departure = flight.get("departure", {}).get("airport", "Unknown")
            arrival = flight.get("arrival", {}).get("airport", "Unknown")
            status = flight.get("flight_status", "Unknown")

            flights.append(
                f"Airline: {airline}\nDeparture: {departure}\nArrival: {arrival}\nStatus: {status}"
            )

    if not flights:
        return "No flight results available."

    return "\n\n".join(flights)