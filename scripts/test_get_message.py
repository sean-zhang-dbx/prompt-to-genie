"""
Quick test: Ask a question to a Genie space and retrieve suggested follow-up questions.

Tests the Start Conversation + Get Message APIs using the Databricks SDK's native Genie methods.
"""

import json
import time
from databricks.sdk import WorkspaceClient

# --- Config ---
SPACE_ID = "<your-space-id>"
QUESTION = "<your-question>"

# --- Setup ---
w = WorkspaceClient()
host = w.config.host.rstrip("/")
print(f"Workspace: {host}")
print(f"Space ID:  {SPACE_ID}")
print(f"Question:  {QUESTION}")
print()

# --- Step 1: Start a conversation ---
print("=" * 60)
print("Step 1: Starting conversation...")
print("=" * 60)

waiter = w.genie.start_conversation(space_id=SPACE_ID, content=QUESTION)

# Extract IDs from the initial response
conversation_id = waiter.response.conversation_id
message_id = waiter.response.message_id
print(f"Conversation ID: {conversation_id}")
print(f"Message ID:      {message_id}")
print()

# --- Step 2: Poll until message is completed ---
print("=" * 60)
print("Step 2: Polling message status...")
print("=" * 60)

terminal_statuses = {"COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"}
poll_interval = 3  # seconds
max_polls = 60  # up to ~3 min

for i in range(max_polls):
    msg = w.genie.get_message(
        space_id=SPACE_ID,
        conversation_id=conversation_id,
        message_id=message_id,
    )
    status = msg.status.value if msg.status else "UNKNOWN"
    print(f"  Poll {i+1}: status = {status}")

    if status in terminal_statuses:
        break

    time.sleep(poll_interval)
else:
    print("WARNING: Max polls reached, message may still be processing.")

print()

# --- Step 3: Print full response ---
print("=" * 60)
print("Step 3: Full message response")
print("=" * 60)
print(json.dumps(msg.as_dict(), indent=2, default=str))
print()

# --- Step 4: Extract suggested follow-up questions ---
print("=" * 60)
print("Step 4: Suggested follow-up questions")
print("=" * 60)

attachments = msg.attachments or []
found_suggestions = False

for att in attachments:
    # Check for suggested questions
    if att.suggested_questions:
        found_suggestions = True
        questions = att.suggested_questions.questions or []
        print(f"Found {len(questions)} suggested follow-up question(s):")
        for j, q in enumerate(questions, 1):
            print(f"  {j}. {q}")
        print()

    # Show query attachment info if present
    if att.query:
        print("Query attachment:")
        print(f"  Description: {att.query.description or 'N/A'}")
        print(f"  SQL: {att.query.query or 'N/A'}")
        print()

    # Show text attachment if present
    if att.text:
        print("Text attachment:")
        print(f"  Content: {att.text.content or 'N/A'}")
        print()

print()
print("Done!")
