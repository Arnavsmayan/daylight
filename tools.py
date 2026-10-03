"""The tools the harness can run, and the JSON that describes them to the model."""

import json
import os

import requests

GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def get_calendar_events(date: str) -> str:
    """Get events from the primary Google Calendar."""
    token = os.getenv("GOOGLE_CALENDAR_ACCESS_TOKEN")
    if not token:
        return json.dumps({"error": "Set GOOGLE_CALENDAR_ACCESS_TOKEN first."})

    try:
        response = requests.get(
            GOOGLE_EVENTS_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={
                "timeMin": f"{date}T00:00:00Z",
                "timeMax": f"{date}T23:59:59Z",
                "singleEvents": "true",
                "orderBy": "startTime",
            },
        )
        response.raise_for_status()
        events = response.json().get("items", [])
    except requests.RequestException as error:
        return json.dumps({"error": f"Calendar request failed: {error}"})

    return json.dumps({
        "date": date,
        "events": [
            {
                "summary": event.get("summary", "(No title)"),
                "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date")),
                "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date")),
            }
            for event in events
        ],
    })


# What the model sees: the "set notes" in the screenplay.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Look up events in the configured Google Calendar for a date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format, interpreted in UTC."},
                },
                "required": ["date"],
            },
        },
    },
]

# What the harness runs: tool name -> Python function.
TOOL_MAP = {"get_calendar_events": get_calendar_events}


def run_tool(name: str, args: dict) -> str:
    """Run one tool call. Models invent tool names and arguments; never let that crash the loop."""
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args)
    except TypeError as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"})
