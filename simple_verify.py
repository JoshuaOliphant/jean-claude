from jean_claude.core.beads import BeadsClient, BeadsTask
import json

# Test basic functionality
client = BeadsClient()
print(f"BeadsClient instance created: {client}")
print(f"Has fetch_task: {hasattr(client, 'fetch_task')}")
print(f"Has parse_task_json: {hasattr(client, 'parse_task_json')}")

# Test parse_task_json
test_json = json.dumps({
    "id": "test-1",
    "title": "Test",
    "description": "Desc",
    "status": "open"
})

task = client.parse_task_json(test_json)
print(f"\nParsed task: {task.id}, {task.title}, {task.description}, {task.status}")
print(f"Task has acceptance_criteria: {hasattr(task, 'acceptance_criteria')}")
print("\n✅ All basic checks passed!")
