from __future__ import annotations

import asyncio
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=".*experimental.*", category=Warning)

from agent_framework import (
    create_harness_agent,
    todos_remaining,
    todos_remaining_message,
)
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import configure_otel_providers, get_tracer
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from console import build_observers_with_planning, run_agent_async

load_dotenv()
configure_otel_providers()
tracer = get_tracer("agent-framework-demo")

# Demo input to paste in the harness: Prepare a 5-minute briefing about reinforcement learning for AI agents with research, draft, review, and final steps.
DEFAULT_TOPIC = "Reinforcement learning for AI Agents."
SKILLS_DIR = str(Path(__file__).resolve().parent / "skills")

HARNESS_INSTRUCTIONS = f"""\
## Briefing harness

You help prepare high-quality conference material.
Use plan mode to clarify the reinforcement-learning-for-agents topic, define success criteria, and create todos.
When the user switches to execute mode, work through the same flow as the workflow samples:
research the topic, draft a briefing, review it, and then write a final version from the feedback.

The default scenario is: {DEFAULT_TOPIC}.
"""


async def main() -> None:
    with tracer.start_as_current_span("Demo 5 - Harness agent + skills") as span:
        span.set_attribute("demo.number", 5)
        span.set_attribute("demo.name", "Harness agent + skills")
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
            skills_paths=[SKILLS_DIR],
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
            placeholder=f"Enter a briefing request...",
            max_context_window_tokens=128_000,
            max_output_tokens=16_384,
        )


if __name__ == "__main__":
    asyncio.run(main())
