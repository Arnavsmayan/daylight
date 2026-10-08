# Daylight

Daylight is a calendar planning assistant connected to Google Calendar and Gmail. Ask about your schedule, find commitments mentioned in email, or plan around open time. Daylight checks for conflicts and asks before adding or deleting calendar events.

## What it can do

| Ask something like | What Daylight does |
| --- | --- |
| "What's on my calendar tomorrow?" | Looks up your events for that date. |
| "Check my email and calendar. When do I have two free hours for a drive this week?" | Searches Gmail for relevant commitments and compares them with your calendar. |
| "Find a free two-hour workout slot this Sunday and add it to my calendar." | Checks for conflicts, suggests a time, and asks you to confirm before adding it. |

## Tools

| Tool | Data source | What it does |
| --- | --- | --- |
| `get_calendar_events` | Google Calendar API | Finds events on a given date. |
| `search_gmail` | Gmail API | Finds emails that may contain event details or commitments. |
| `create_calendar_event` | Google Calendar API | Adds an event after the user confirms the proposed time. |
| `delete_calendar_event` | Google Calendar API | Removes an event after the user confirms which event to delete. |

Gemini chooses which tools to call and uses their results to answer. Daylight shows each tool call in the chat.

**Deploy Link:** [Daylight](https://daylight.cloud.run) <br>
**Submitted by:** Arnav Jain (aj3491@columbia.edu)
