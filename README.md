# Daylight

**A calendar planner that checks beyond your calendar.**

An empty slot is not always free. A meeting confirmation might be sitting in Gmail, while your classes and appointments live in Google Calendar. Daylight reads both, brings the useful details into one conversation, and helps you decide where a new plan fits.

## What Daylight Does

- **See the whole picture.** Ask about a day or a date range. Daylight checks Calendar and looks through Gmail for relevant commitments, then gives you a plain-English rundown in Eastern Time.
- **Spot the overlap.** Before suggesting a time, it compares the events it found with what you want to do, so a proposed workout or study session does not quietly collide with another plan.
- **Make a plan.** Give it a task and a duration. It can suggest an opening and create the Google Calendar event after you confirm the exact time and title.
- **Change course.** It can look up an existing event and delete it, but only after you confirm which event should go.

Daylight shows its tool calls in the chat. You can see what it checked before it answers or changes your calendar.

## Under the Hood

| Tool | Source | Job |
| --- | --- | --- |
| `get_calendar_events` | Google Calendar API | Reads booked events for a day or date range, including their times and event IDs. |
| `search_gmail` | Gmail API | Finds messages that mention plans not obvious from the calendar and returns the details Daylight can inspect. |
| `create_calendar_event` | Google Calendar API | Adds the event you approved, with its title and Eastern Time start and end. |
| `delete_calendar_event` | Google Calendar API | Removes the specific event you approved for deletion. |

Gemini chooses and calls these tools, reads their results, and turns them into a useful answer. Calendar changes wait for an explicit yes.

## Try It

1. "What's on my schedule tomorrow? Check my calendar and email."
2. "Check my email and calendar. When do I have two free hours for a drive this week?"
3. "Find a free two-hour workout slot this Sunday and add it to my calendar."

**Live app:** [daylight.cloud.run](https://daylight.cloud.run)

**Submitted by:** Arnav Jain (aj3491@columbia.edu)
