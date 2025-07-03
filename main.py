import json
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig, function_tool
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

# Use absolute path for todo.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TODO_PATH = os.path.join(BASE_DIR, "todo.json")

externel_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=externel_client,
)

config = RunConfig(
    model=model,
    model_provider=externel_client,
    tracing_disabled=True,
)

#Read Todo
@function_tool
def read_todo():
    """Read all todo items."""
    try:
        with open(TODO_PATH, "r") as file:
            todos = json.load(file)
        return todos
    except FileNotFoundError:
        return []

#Add Todo
@function_tool
def add_todo(title: str, description: str, due_date: str):
    """Add a new todo item"""
    try:
        try:
            with open(TODO_PATH, "r") as file:
                todos = json.load(file)
        except FileNotFoundError:
            todos = []
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in todo.json")

        new_todo = {
            "id": len(todos) + 1,
            "title": title,
            "description": description,
            "due_date": due_date,
            "completed": False
        }

        todos.append(new_todo)
        with open(TODO_PATH, "w") as file:
            json.dump(todos, file, indent=4)

        return new_todo

    except Exception as e:
        raise Exception(f"Failed to add Todo item: {str(e)}")

#Delete Todo
@function_tool
def delete_todo(todo_id: int):
    """Delete a todo item by its ID."""
    try:
        try:
            with open(TODO_PATH, "r") as file:
                todos = json.load(file)
        except FileNotFoundError:
            return {"error": "No todo list found."}
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in todo.json")

        original_length = len(todos)
        todos = [todo for todo in todos if todo.get("id") != todo_id]

        if len(todos) == original_length:
            return {"error": f"Todo with id {todo_id} not found."}

        # Reassign IDs to keep them sequential (optional)
        for idx, todo in enumerate(todos, start=1):
            todo["id"] = idx

        with open(TODO_PATH, "w") as file:
            json.dump(todos, file, indent=4)

        return {"success": f"Todo with id {todo_id} deleted."}
    except Exception as e:
        return {"error": f"Failed to delete Todo item: {str(e)}"}

#Update Todo 
@function_tool
def update_todo(todo_id: int, title: str = None, description: str = None, due_date: str = None, completed: bool = None):
    """Update an existing todo item by its ID. You can update title, description, due date, or completed status."""
    try:
        # File read karna
        try:
            with open(TODO_PATH, "r") as file:
                todos = json.load(file)
        except FileNotFoundError:
            return {"error": "No todo list found."}
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in todo.json")

        # Todo find karna
        todo_found = False
        for todo in todos:
            if todo.get("id") == todo_id:
                todo_found = True
                if title is not None:
                    todo["title"] = title
                if description is not None:
                    todo["description"] = description
                if due_date is not None:
                    todo["due_date"] = due_date
                if completed is not None:
                    todo["completed"] = completed
                break

        if not todo_found:
            return {"error": f"Todo with id {todo_id} not found."}

        # File write karna (updated data ke sath)
        with open(TODO_PATH, "w") as file:
            json.dump(todos, file, indent=4)

        return {"success": f"Todo with id {todo_id} updated."}
    except Exception as e:
        return {"error": f"Failed to update Todo item: {str(e)}"}


# Agent setup with all tools
agent = Agent(
    name="GeminiAgent",
    instructions="""
You are a smart todo assistant. Use tools to manage tasks:

- Use read_todo to show all tasks.
- Use add_todo to add new tasks. Extract title, description, and due_date from user input intelligently. If not clear, ask briefly.
- Use delete_todo to delete a task by ID.
- Use update_todo to update a task's fields (title, description, due_date, completed). Infer values if possible.

Always choose the correct tool based on user intent. Never guess ID — ask if missing. Keep responses short and helpful.
""",
    tools=[read_todo, add_todo, delete_todo, update_todo],
    model=model,
)



user_input = input("Enter your command: ")
result = Runner.run_sync(
    agent,
    input=user_input,
    run_config=config,
)
print(result.final_output)