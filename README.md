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
| `get_calendar_events` | Google Calendar API | Pulls the day's events and their times, giving Daylight a clear view of what's booked. |
| `search_gmail` | Gmail API | Searches matching messages and surfaces sender, subject, date, and snippets where plans may be hiding. |
| `create_calendar_event` | Google Calendar API | Adds the agreed event title and ET start/end times to your calendar after you confirm. |
| `delete_calendar_event` | Google Calendar API | Removes the selected event by its calendar ID after you confirm the change. |

Gemini chooses the right tools and turns their results into a clear answer. Every tool call is visible in the chat, so you can follow Daylight's work.

**Deploy Link:** [Daylight](https://daylight.cloud.run) <br>
**Submitted by:** Arnav Jain (aj3491@columbia.edu)
