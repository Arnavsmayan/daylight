# Daylight

Plans live in two places: your calendar and your inbox. Daylight brings them into one conversation. Ask what's coming up, uncover commitments tucked into Gmail, find room in your week, and choose what makes it onto your calendar.

## Make room for what matters

| You ask | Daylight does |
| --- | --- |
| "What's on my calendar tomorrow?" | Lays out what's already on your day. |
| "Check my email and calendar. When do I have two free hours for a drive this week?" | Brings inbox commitments and calendar events together to find an open window. |
| "Find a free two-hour workout slot this Sunday and add it to my calendar." | Checks for conflicts, suggests a time, then waits for your go-ahead. |

## Tools

| Tool | Data source | What it does |
| --- | --- | --- |
| `get_calendar_events` | Google Calendar API | Sees what's already on the calendar. |
| `search_gmail` | Gmail API | Surfaces plans and commitments from email. |
| `create_calendar_event` | Google Calendar API | Adds the plan you confirmed. |
| `delete_calendar_event` | Google Calendar API | Removes the event you chose. |

Gemini chooses the right tools and turns their results into a clear answer. Every tool call is visible in the chat, so you can follow Daylight's work.

**Deploy Link:** [Daylight](https://daylight.cloud.run) <br>
**Submitted by:** Arnav Jain (aj3491@columbia.edu)
