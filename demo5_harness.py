from __future__ import annotations

import asyncio
import os

from agent_framework import (
    create_harness_agent,
    todos_remaining,
    todos_remaining_message,
)
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from console import build_observers_with_planning, run_agent_async

load_dotenv()

DEFAULT_TOPIC = "Reinforcement learning for AI Agents."

HARNESS_INSTRUCTIONS = f"""\
## Briefing harness

You help prepare high-quality conference material.
Use plan mode to clarify the reinforcement-learning-for-agents topic, define success criteria, and create todos.
When the user switches to execute mode, work through the same flow as the workflow samples:
research the topic, draft a briefing, review it, and then write a final version from the feedback.

The default scenario is: {DEFAULT_TOPIC}.
"""


async def main() -> None:
    agent = create_harness_agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        ),
        max_context_window_tokens=128_000,
        max_output_tokens=16_384,
        name="HarnessAgent",
        description="Plans and produces briefing material.",
        agent_instructions=HARNESS_INSTRUCTIONS,
        loop_should_continue=todos_remaining(looping_modes=["execute"]),
        loop_next_message=todos_remaining_message,
        loop_max_iterations=10,
    )

    await run_agent_async(
        agent,
        session=agent.create_session(),
        observers=build_observers_with_planning(agent),
        initial_mode="plan",
        title="Harness Agent",
        placeholder=f"Enter a briefing request, or press Enter for: {DEFAULT_TOPIC}",
        max_context_window_tokens=128_000,
        max_output_tokens=16_384,
    )


if __name__ == "__main__":
    asyncio.run(main())
