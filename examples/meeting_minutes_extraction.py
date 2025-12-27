"""
Meeting Minutes Extraction Example

Demonstrates extracting structured data from meeting notes and minutes.
"""

from strutex import DocumentProcessor, Object, String, Array


meeting_schema = Object(
    description="Meeting minutes data",
    properties={
        "meeting_title": String,
        "date": String,
        "time": String,
        "location": String(description="Physical or virtual meeting link"),
        "attendees": Array(
            items=Object(properties={
                "name": String,
                "role": String,
                "present": String(description="Present, Absent, or Remote"),
            })
        ),
        "agenda_items": Array(items=String),
        "discussions": Array(
            items=Object(properties={
                "topic": String,
                "summary": String,
                "decisions": Array(items=String),
            })
        ),
        "action_items": Array(
            items=Object(properties={
                "task": String,
                "assignee": String,
                "due_date": String,
                "priority": String,
            })
        ),
        "next_meeting": String,
        "notes": String,
    }
)

meeting_prompt = """
Extract meeting information from these minutes.

Guidelines:
- List all attendees with their roles
- Capture each agenda item discussed
- Note all decisions made
- Extract all action items with assignees and deadlines
"""


def extract_meeting_minutes(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, meeting_prompt, meeting_schema)


if __name__ == "__main__":
    print("Meeting Minutes Extraction Example")
    print(f"Schema fields: {len(meeting_schema.properties)}")
