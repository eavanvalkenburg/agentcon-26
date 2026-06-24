from __future__ import annotations

import os
import warnings
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

warnings.filterwarnings("ignore", message=".*experimental.*", category=Warning)

from agent_framework import Agent, tool
from agent_framework.devui import serve
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import configure_otel_providers
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("agent_framework").setLevel(logging.INFO)
logger = logging.getLogger("agent_framework.demo.simple_agent")
configure_otel_providers()


@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, "The city or location to get the weather for."],
) -> str:
    """Get the current weather for a location."""
    logger.info("Weather tool called", extra={"location": location})
    return f"The weather in {location} is sunny with a high of 22 C."


@tool(approval_mode="never_require")
def get_time(
    timezone_name: Annotated[
        str, "Timezone name: UTC, Europe/Amsterdam, or America/New_York."
    ] = "UTC",
) -> str:
    """Get the current time in a timezone."""
    offsets = {
        "UTC": 0,
        "Europe/Amsterdam": 2,
        "America/New_York": -4,
    }
    logger.info("Time tool called", extra={"timezone_name": timezone_name})
    offset = offsets.get(timezone_name, 0)
    now = datetime.now(timezone.utc) + timedelta(hours=offset)
    return f"The current time in {timezone_name} is {now:%H:%M:%S}."


def main() -> None:
    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        ),
        name="simple_agent",
        description="Simple assistant with weather, time, and web search tools.",
        instructions="You are a helpful assistant. Use the available tools when they are useful.",
        tools=[
            get_weather,
            get_time,
            FoundryChatClient.get_web_search_tool(search_context_size="medium"),
        ],
    )

    print("Starting DevUI on http://localhost:8090")
    logger.info("Starting simple agent DevUI", extra={"port": 8090})
    serve(entities=[agent], port=8090, auto_open=True, auth_enabled=False)


if __name__ == "__main__":
    main()
