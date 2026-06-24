from __future__ import annotations

import asyncio
import os
from typing import Annotated, Any, Literal

from agent_framework import Agent, tool
from agent_framework.devui import serve
from agent_framework.foundry import FoundryChatClient
from agent_framework.hyperlight import HyperlightCodeActProvider
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


@tool(approval_mode="never_require")
def compute(
    operation: Annotated[
        Literal["add", "subtract", "multiply", "divide"], "Math operation to perform."
    ],
    a: Annotated[float, "First number."],
    b: Annotated[float, "Second number."],
) -> float:
    """Perform a math operation inside the sandbox."""
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b else float("inf"),
    }
    return operations[operation]


@tool(approval_mode="never_require")
async def fetch_data(
    table: Annotated[str, "Table name to fetch: users or products."],
) -> list[dict[str, Any]]:
    """Fetch sample data inside the sandbox."""
    await asyncio.sleep(0.2)
    data = {
        "users": [
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
            {"id": 3, "name": "Charlie", "role": "admin"},
        ],
        "products": [
            {"id": 101, "name": "Widget", "price": 9.99},
            {"id": 102, "name": "Gadget", "price": 19.99},
        ],
    }
    return data.get(table, [])


def main() -> None:

    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        ),
        name="codeact_agent",
        description="Assistant with Hyperlight CodeAct sandbox exposed through DevUI.",
        instructions=(
            "You are a helpful assistant. Use execute_code for calculations or data analysis. "
            "Inside the sandbox, call host tools with call_tool(...)."
        ),
        context_providers=[
            HyperlightCodeActProvider(
                tools=[compute, fetch_data], approval_mode="never_require"
            )
        ],
    )

    print("Starting CodeAct DevUI on http://localhost:8091")
    serve(entities=[agent], port=8091, auto_open=True, auth_enabled=False)


if __name__ == "__main__":
    main()
