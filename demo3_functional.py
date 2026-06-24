from __future__ import annotations

import asyncio
import os
import sys
import warnings

warnings.filterwarnings("ignore", message=".*experimental.*", category=Warning)

from agent_framework import Agent, workflow
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import configure_otel_providers, get_tracer
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()
configure_otel_providers()
sys.stdout.reconfigure(encoding="utf-8")
tracer = get_tracer("agent-framework-demo")

# Demo topic: Reinforcement learning for AI Agents.
DEFAULT_TOPIC = "Reinforcement learning for AI Agents."

RESEARCHER_INSTRUCTIONS = """\
You are the researcher for a briefing team.
Find the key facts, audience needs, risks, and demo angles for the requested topic.
Return concise notes with useful evidence and practical implications.
"""

WRITER_INSTRUCTIONS = """\
You are the writer for a briefing team.
Turn research notes into a short, presenter-ready briefing with a title, three takeaways,
a recommended demo narrative, and one audience engagement question.
"""

REVIEWER_INSTRUCTIONS = """\
You are the reviewer for a briefing team.
Review the draft for clarity, credibility, demo value, and audience fit.
Return a concise verdict plus concrete improvements.
"""


async def main() -> None:
    with tracer.start_as_current_span("Demo 3 - Functional workflow") as span:
        span.set_attribute("demo.number", 3)
        span.set_attribute("demo.name", "Functional workflow")
        client = FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        )

        researcher = Agent(
            client=client, name="researcher", instructions=RESEARCHER_INSTRUCTIONS
        )
        writer = Agent(client=client, name="writer", instructions=WRITER_INSTRUCTIONS)
        reviewer = Agent(
            client=client, name="reviewer", instructions=REVIEWER_INSTRUCTIONS
        )

        @workflow
        async def briefing_workflow(requested_topic: str) -> str:
            research = (
                await researcher.run(
                    f"Research this briefing topic and return concise notes: {requested_topic}"
                )
            ).text
            draft = (
                await writer.run(
                    "Write the briefing from these research notes.\n\n"
                    f"Topic: {requested_topic}\n\nResearch notes:\n{research}"
                )
            ).text
            review = (
                await reviewer.run(
                    "Review this briefing draft (using the provided research) and suggest concrete improvements.\n\n"
                    f"Topic: {requested_topic}\n\nDraft:\n{draft}\n\nResearch: \n{research}"
                )
            ).text
            final = (
                await writer.run(
                    messages="Use this feedback and the original research and your draft to create a final version:"
                    f"Topic: {requested_topic}\n\nFeedback: \n{review}\n\nDraft:\n{draft}\n\nResearch: \n{research}"
                )
            ).text
            return f"# Functional workflow briefing\n\n##Final: \n{final}\n\n## Research\n{research}"

        result = await briefing_workflow.run(DEFAULT_TOPIC)
        print(result.get_outputs()[0])


if __name__ == "__main__":
    asyncio.run(main())
