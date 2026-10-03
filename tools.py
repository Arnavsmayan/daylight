"""The tools the harness can run, and the JSON that describes them to the model."""

import json
import os
import requests

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def get_calendar_events(date: str, refresh_token: str | None = None) -> str:
    """Get events from the primary Google Calendar."""
    if not refresh_token:
        return json.dumps({"error": "Sign in with Google first at /auth/google."})

    try:
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        response = requests.get(
            GOOGLE_EVENTS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
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
            "description": "Look up events in the signed-in user's Google Calendar for a date.",
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


def run_tool(name: str, args: dict, refresh_token: str | None = None) -> str:
    """Run one tool call. Models invent tool names and arguments; never let that crash the loop."""
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args, refresh_token=refresh_token)
    except TypeError as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"})
