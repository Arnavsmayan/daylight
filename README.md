# Daylight

Your schedule is split between calendar events and emails. Daylight brings both together. Ask what is coming up, uncover plans mentioned in Gmail, or find a clear window in your week. When you want to add or remove an event, Daylight checks the details with you first.

## Put Daylight to work

| You ask | Daylight does |
| --- | --- |
| "What's on my calendar tomorrow?" | Pulls up your events for the day. |
| "Check my email and calendar. When do I have two free hours for a drive this week?" | Connects email commitments with your calendar and finds an open window. |
| "Find a free two-hour workout slot this Sunday and add it to my calendar." | Checks for conflicts, suggests a time, and waits for your go-ahead. |

## Tools

| Tool | Data source | What it does |
| --- | --- | --- |
| `get_calendar_events` | Google Calendar API | Brings back the events on a date. |
| `search_gmail` | Gmail API | Finds messages with plans, times, and commitments. |
| `create_calendar_event` | Google Calendar API | Puts a confirmed event on your calendar. |
| `delete_calendar_event` | Google Calendar API | Removes the event you confirmed. |

Gemini picks the tools for the request and combines their results into an answer. Every tool call appears in the chat, so you can see how Daylight got there.

**Deploy Link:** [Daylight](https://daylight.cloud.run) <br>
**Submitted by:** Arnav Jain (aj3491@columbia.edu)
