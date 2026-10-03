import json
import os
import re
import secrets
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import litellm
import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel

from tools import TOOLS, run_tool

# --- Config ---

SYSTEM_PROMPT = (
    "You are Daylight, a calendar planning assistant. Your purpose is to help manage "
    "the user's calendar. You can look up calendar events and search Gmail for event "
    "details and commitments, such as an event time mentioned in an email. Use that "
    "information to answer schedule questions and identify possible calendar conflicts. "
    "Do not offer to draft or send emails; email is only used to find calendar-related "
    "information. To schedule or delete an event, first identify the exact event or "
    "proposed time and ask the user to confirm it. Do not call a create or delete tool "
    "until the user clearly confirms that exact action. Check for calendar conflicts "
    "before proposing a new event. "
    "When searching Gmail for a date, try reasonable date formats such as 'Oct 8', "
    "'October 8', '10/8', and '8/10' rather than relying on one exact spelling. "
    "Check matching email contents to confirm the event date before reporting a match. "
    "Use Eastern Time (ET) for dates and times. "
    "Use the current ET date provided in the conversation for today, tomorrow, and "
    "other relative dates. Interpret next week as Sunday through Saturday. Distinguish "
    "an email's sent date from the event date described inside it. Call "
    "get_calendar_events for calendar questions and search_gmail for email questions. "
    "After receiving tool results, read and understand them, then explain the useful "
    "information in a clear, natural response. Do not repeat raw JSON or use Markdown "
    "formatting."
)
MAX_TOOL_ROUNDS = 15

# --- The Harness ---


def run_agent(
    messages: list[dict],
    refresh_token: str | None = None,
    session_id: str | None = None,
    initial_tool_calls: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Complete until the model answers without asking for a tool.

    Returns the final text and a record of every tool call made along the way.
    """
    tool_calls = initial_tool_calls or []

    for _ in range(MAX_TOOL_ROUNDS):
        reply = litellm.completion(
            model="vertex_ai/gemini-3.5-flash-lite",
            vertex_location="global",
            messages=messages,
            tools=TOOLS,
        ).choices[0].message

        # Append assistant's reply (text, tool calls, or both) to the context.
        # model_dump() keeps it a plain dict: the raw object carries provider-specific
        # fields that trip Pydantic when LiteLLM re-serializes it next round.
        messages += [reply.model_dump()]

        if not reply.tool_calls:
            return reply.content, tool_calls

        # The harness, not the model, runs each tool and appends the result
        for call in reply.tool_calls:
            args = json.loads(call.function.arguments)
            if call.function.name in {"create_calendar_event", "delete_calendar_event"}:
                action = {"name": call.function.name, "args": args}
                if session_id and session_id not in pending_calendar_actions:
                    pending_calendar_actions[session_id] = {**action, "asked": False}
                pending = pending_calendar_actions.get(session_id, action)
                result = json.dumps({
                    "confirmation_required": True,
                    "action": pending["name"],
                    "details": pending["args"],
                    "message": "Do not execute this yet. Present the exact action to the user and ask for confirmation.",
                })
            else:
                result = run_tool(call.function.name, args, refresh_token)
            tool_calls += [{"name": call.function.name, "args": args, "result": result}]

            messages += [{"role": "tool", "tool_call_id": call.id, "content": result}]

    return "Sorry, I hit my tool-call limit before finishing.", tool_calls


# --- Session Store ---

# session_id -> list of messages. In-memory, single process.
sessions: dict[str, list] = {}
calendar_tokens: dict[str, str] = {}
oauth_states: dict[str, str] = {}
pending_calendar_actions: dict[str, dict] = {}


def is_explicit_confirmation(message: str) -> bool:
    normalized = re.sub(r"[^a-z ]", " ", message.lower())
    normalized = " ".join(normalized.split())
    return normalized in {
        "yes", "yes please", "confirm", "confirmed", "go ahead", "do it",
        "proceed", "add it", "delete it", "thats right",
    }


def asks_for_confirmation(message: str) -> bool:
    text = message.lower()
    return "?" in text and any(phrase in text for phrase in (
        "should i", "shall i", "would you like", "do you want me to", "confirm",
    ))


def google_redirect_uri(request: Request) -> str:
    return os.getenv("GOOGLE_REDIRECT_URI") or str(request.url_for("google_callback"))

# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/auth/google")
def google_login(request: Request):
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    if not client_id:
        return PlainTextResponse("Set GOOGLE_OAUTH_CLIENT_ID in Cloud Run.", status_code=500)

    browser_id = request.cookies.get("daylight_user") or uuid.uuid4().hex
    state = secrets.token_urlsafe(24)
    oauth_states[state] = browser_id
    redirect_uri = google_redirect_uri(request)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    response = RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    )
    response.set_cookie(
        "daylight_user",
        browser_id,
        httponly=True,
        samesite="lax",
        secure=redirect_uri.startswith("https://"),
    )
    return response


@app.get("/auth/callback", name="google_callback")
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        return PlainTextResponse(f"Google sign-in failed: {error}", status_code=400)

    browser_id = request.cookies.get("daylight_user")
    if not browser_id or oauth_states.pop(state, None) != browser_id or not code:
        return PlainTextResponse("Google sign-in failed. Try /auth/google again.", status_code=400)

    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        return PlainTextResponse("Set Google OAuth client ID and secret in Cloud Run.", status_code=500)

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": google_redirect_uri(request),
        },
    )
    token_response.raise_for_status()
    refresh_token = token_response.json().get("refresh_token")
    if not refresh_token:
        return PlainTextResponse("Google did not return a refresh token. Try signing in again.", status_code=400)

    calendar_tokens[browser_id] = refresh_token
    return HTMLResponse(
        "<p>Google connected. Close this window to return to Daylight.</p>"
        "<script>window.opener.postMessage('daylight-google-connected', window.location.origin);window.close();</script>"
    )


@app.get("/auth/status")
def auth_status(request: Request):
    browser_id = request.cookies.get("daylight_user")
    return {"connected": bool(calendar_tokens.get(browser_id))}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):
    # Get or create the session
    session_id = request.session_id or str(uuid.uuid4())
    today_et = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    system_message = f"{SYSTEM_PROMPT} Current date in ET: {today_et}."
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": system_message}]
    else:
        sessions[session_id][0]["content"] = system_message

    # Append user's message to the context
    sessions[session_id] += [{"role": "user", "content": request.message}]

    try:
        browser_id = http_request.cookies.get("daylight_user")
        refresh_token = calendar_tokens.get(browser_id)
        initial_tool_calls = []
        pending = pending_calendar_actions.get(session_id)
        if pending:
            if pending.get("asked") and is_explicit_confirmation(request.message):
                pending_calendar_actions.pop(session_id, None)
                result = run_tool(pending["name"], pending["args"], refresh_token)
                initial_tool_calls.append({
                    "name": pending["name"],
                    "args": pending["args"],
                    "result": result,
                })
                sessions[session_id].append({
                    "role": "system",
                    "content": "The user explicitly confirmed the pending calendar action. "
                    "It has now been attempted. Do not repeat the action. Tool result: " + result,
                })
            else:
                pending_calendar_actions.pop(session_id, None)
        response, tool_calls = run_agent(
            sessions[session_id], refresh_token, session_id, initial_tool_calls
        )
        pending = pending_calendar_actions.get(session_id)
        if pending:
            pending["asked"] = asks_for_confirmation(response)
    except Exception as e:
        # Auth, billing, a model that is not running: show it in the chat, not as a 500.
        response, tool_calls = f"Model call failed: {type(e).__name__}: {str(e)[:300]}", []

    return ChatResponse(response=response, session_id=session_id, tool_calls=tool_calls)


@app.post("/clear")
def clear(session_id: str | None = None):
    sessions.pop(session_id, None)
    pending_calendar_actions.pop(session_id, None)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
