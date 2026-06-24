from __future__ import annotations

import asyncio
import os
import sys
import warnings

warnings.filterwarnings("ignore", message=".*experimental.*", category=Warning)

from agent_framework import Agent
from agent_framework.observability import configure_otel_providers, get_tracer
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()
configure_otel_providers()
sys.stdout.reconfigure(encoding="utf-8")
tracer = get_tracer("agent-framework-demo")

BASE_URL = os.environ.get("HOSTED_RESPONSES_URL", "http://127.0.0.1:8000")
# Demo input to send to the hosted agent: What is the weather in Tokyo?
PROMPTS = [
    "What is the weather in Tokyo?",
    "And what about Amsterdam?",
]


async def main() -> None:
    with tracer.start_as_current_span("Demo 7b - Hosted agent client") as span:
        span.set_attribute("demo.number", 7)
        span.set_attribute("demo.name", "Hosted agent client")
        agent = Agent(
            client=OpenAIChatClient(
                model="hosted_agent", base_url=BASE_URL, api_key="not-needed"
            ),
            name="hosted_client",
        )
        session = agent.create_session()

        for prompt in PROMPTS:
            print(f"User: {prompt}")
            print("Agent: ", end="", flush=True)
            stream = agent.run(prompt, stream=True, session=session)

            async for update in stream:
                if update.text:
                    print(update.text, end="", flush=True)

            response = await stream.get_final_response()
            print(f"\nResponse ID: {response.response_id}\n")


if __name__ == "__main__":
    asyncio.run(main())
