"""The tools the harness can run, and the JSON that describes them to the model."""

import json
import os
import requests

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
GMAIL_MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"


def get_access_token(refresh_token: str) -> str:
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_calendar_events(date: str, refresh_token: str | None = None) -> str:
    """Get events from the primary Google Calendar."""
    if not refresh_token:
        return json.dumps({"error": "Sign in with Google first at /auth/google."})

    try:
        access_token = get_access_token(refresh_token)
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
                "id": event.get("id"),
                "summary": event.get("summary", "(No title)"),
                "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date")),
                "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date")),
            }
            for event in events
        ],
    })


def create_calendar_event(
    summary: str,
    start: str,
    end: str,
    refresh_token: str | None = None,
) -> str:
    """Create an event in the primary Google Calendar."""
    if not refresh_token:
        return json.dumps({"error": "Sign in with Google first at /auth/google."})

    try:
        access_token = get_access_token(refresh_token)
        response = requests.post(
            GOOGLE_EVENTS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "summary": summary,
                "start": {"dateTime": start, "timeZone": "America/New_York"},
                "end": {"dateTime": end, "timeZone": "America/New_York"},
            },
        )
        response.raise_for_status()
    except requests.RequestException as error:
        return json.dumps({"error": f"Calendar event creation failed: {error}"})

    event = response.json()
    return json.dumps({"created": True, "id": event.get("id"), "summary": summary})


def delete_calendar_event(event_id: str, refresh_token: str | None = None) -> str:
    """Delete an event from the primary Google Calendar by its event ID."""
    if not refresh_token:
        return json.dumps({"error": "Sign in with Google first at /auth/google."})

    try:
        access_token = get_access_token(refresh_token)
        response = requests.delete(
            f"{GOOGLE_EVENTS_URL}/{event_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except requests.RequestException as error:
        return json.dumps({"error": f"Calendar event deletion failed: {error}"})

    return json.dumps({"deleted": True, "id": event_id})


def search_gmail(query: str, refresh_token: str | None = None) -> str:
    """Search Gmail and return a few matching message details."""
    if not refresh_token:
        return json.dumps({"error": "Sign in with Google first at /auth/google."})

    try:
        headers = {"Authorization": f"Bearer {get_access_token(refresh_token)}"}
        response = requests.get(
            GMAIL_MESSAGES_URL,
            headers=headers,
            params={"q": query, "maxResults": 5},
        )
        response.raise_for_status()
        messages = response.json().get("messages", [])
        results = []
        for message in messages:
            detail = requests.get(
                f"{GMAIL_MESSAGES_URL}/{message['id']}",
                headers=headers,
                params=[
                    ("format", "metadata"),
                    ("metadataHeaders", "From"),
                    ("metadataHeaders", "Subject"),
                    ("metadataHeaders", "Date"),
                ],
            )
            detail.raise_for_status()
            item = detail.json()
            message_headers = {
                h["name"].lower(): h["value"]
                for h in item.get("payload", {}).get("headers", [])
            }
            email_date = message_headers.get("date")
            results.append({
                "from": message_headers.get("from"),
                "subject": message_headers.get("subject"),
                "date": email_date,
                "snippet": item.get("snippet", ""),
            })
    except requests.RequestException as error:
        detail = error.response.text[:500] if error.response is not None else str(error)
        return json.dumps({"error": f"Gmail search failed: {detail}"})

    return json.dumps({"query": query, "messages": results})


# What the model sees: the "set notes" in the screenplay.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Create an event in the signed-in user's primary Google Calendar. Ask the user to confirm the exact event and time first. If they reply yes to that question, call this tool with the proposed details. Use Eastern Time for start and end.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Short event title."},
                    "start": {"type": "string", "description": "Start datetime in ISO 8601 format with ET offset, for example 2026-10-04T13:00:00-04:00."},
                    "end": {"type": "string", "description": "End datetime in ISO 8601 format with ET offset."},
                },
                "required": ["summary", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": "Delete an event from the signed-in user's primary Google Calendar by its event ID. Look up the event and ask the user to confirm deleting it first. If they reply yes to that question, call this tool with the event ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "Event ID returned by get_calendar_events."},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_gmail",
            "description": "Search the signed-in user's Gmail messages and return matching snippets. For date searches, use a date format such as 'Oct 8', 'October 8', '10/8', or '8/10'; verify the actual event date from the returned email snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search text, such as interview or project meeting."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Look up events in the signed-in user's Google Calendar for a date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format."},
                },
                "required": ["date"],
            },
        },
    },
]

# What the harness runs: tool name -> Python function.
TOOL_MAP = {
    "get_calendar_events": get_calendar_events,
    "create_calendar_event": create_calendar_event,
    "delete_calendar_event": delete_calendar_event,
    "search_gmail": search_gmail,
}


def run_tool(name: str, args: dict, refresh_token: str | None = None) -> str:
    """Run one tool call. Models invent tool names and arguments; never let that crash the loop."""
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args, refresh_token=refresh_token)
    except TypeError as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"})
