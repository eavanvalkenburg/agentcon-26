from __future__ import annotations

import os
import sys
import warnings
import logging
from dataclasses import replace
from pathlib import Path
from typing import Annotated

warnings.filterwarnings("ignore", message=".*experimental.*", category=Warning)

from agent_framework import Agent, FileHistoryProvider, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import configure_otel_providers, get_tracer
from agent_framework_hosting import AgentFrameworkHost, ChannelRequest
from agent_framework_hosting_responses import ResponsesChannel
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()
logging.getLogger("agent_framework").setLevel(logging.INFO)
logger = logging.getLogger("agent_framework.demo.hosting")
logger.setLevel(logging.INFO)
if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    )
    logger.addHandler(console_handler)
configure_otel_providers()
tracer = get_tracer("agent-framework-demo")

# Demo input for demo7b or a Responses client: What is the weather in Tokyo?
SESSIONS_DIR = Path(__file__).resolve().parent / "storage" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@tool(approval_mode="never_require")
def lookup_weather(location: Annotated[str, "The city to look up weather for."]) -> str:
    """Return a deterministic weather report for a city."""
    logger.info("Hosted weather tool called", extra={"location": location})
    high_temp = 5 + (sum(location.encode("utf-8")) % 21)
    reports = {
        "Seattle": f"Seattle is rainy with a high of {high_temp} C.",
        "Amsterdam": f"Amsterdam is cloudy with a high of {high_temp} C.",
        "Tokyo": f"Tokyo is clear with a high of {high_temp} C.",
    }
    return reports.get(location, f"{location} is sunny with a high of {high_temp} C.")


def run_hook(request: ChannelRequest, **_: object) -> ChannelRequest:
    """Keep the host in control of deployment-owned Responses options."""
    logger.info(
        "Responses request received", extra={"has_options": request.options is not None}
    )
    options = dict(request.options or {})
    options.pop("model", None)
    options.pop("temperature", None)
    options.pop("store", None)
    return replace(request, options=options or None)


def build_host() -> AgentFrameworkHost:
    logger.info("Building hosted weather agent")
    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=DefaultAzureCredential(),
        ),
        name="hosted_agent",
        instructions=(
            "You are a friendly weather assistant. Use lookup_weather for weather questions "
            "and answer in one short sentence."
        ),
        tools=[lookup_weather],
        context_providers=[FileHistoryProvider(SESSIONS_DIR)],
        default_options={"store": False},
    )

    return AgentFrameworkHost(
        target=agent, channels=[ResponsesChannel(run_hook=run_hook)], debug=True
    )


app = build_host().app


if __name__ == "__main__":
    with tracer.start_as_current_span("Demo 7 - Hosting server") as span:
        span.set_attribute("demo.number", 7)
        span.set_attribute("demo.name", "Hosting server")
        port = int(os.environ.get("PORT", "8000"))
        logger.info(
            "Starting hosted weather agent", extra={"host": "127.0.0.1", "port": port}
        )
        build_host().serve(host="127.0.0.1", port=port)
