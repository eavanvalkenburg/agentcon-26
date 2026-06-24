from __future__ import annotations

import asyncio
import os

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("HOSTED_RESPONSES_URL", "http://127.0.0.1:8000")
PROMPTS = [
    "What is the weather in Tokyo?",
    "And what about Amsterdam?",
]


async def main() -> None:
    agent = Agent(
        client=OpenAIChatClient(base_url=BASE_URL, api_key="not-needed"),
        name="hosted_weather_client",
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
