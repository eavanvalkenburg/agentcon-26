from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from agent_framework import Agent, Executor, WorkflowBuilder, WorkflowContext, handler
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from typing_extensions import Never

load_dotenv()

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


@dataclass
class BriefingState:
    topic: str
    research: str = ""
    draft: str = ""
    review: str = ""


class ResearchExecutor(Executor):
    def __init__(self, agent: Agent, id: str = "researcher") -> None:
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle(
        self, topic: str, ctx: WorkflowContext[BriefingState, str]
    ) -> None:
        response = await self.agent.run(
            f"Research this briefing topic and return concise notes: {topic}"
        )
        await ctx.send_message(BriefingState(topic=topic, research=response.text))


class WriterExecutor(Executor):
    def __init__(self, agent: Agent, id: str = "writer") -> None:
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle(
        self, state: BriefingState, ctx: WorkflowContext[BriefingState, str]
    ) -> None:
        response = await self.agent.run(
            "Write the briefing from these research notes.\n\n"
            f"Topic: {state.topic}\n\nResearch notes:\n{state.research}"
        )
        state.draft = response.text
        await ctx.send_message(state)


class ReviewerExecutor(Executor):
    def __init__(self, agent: Agent, id: str = "reviewer") -> None:
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle(
        self, state: BriefingState, ctx: WorkflowContext[BriefingState, str]
    ) -> None:
        response = await self.agent.run(
            "Review this briefing draft (using the provided research) and suggest concrete improvements.\n\n"
            f"Topic: {state.topic}\n\nDraft:\n{state.draft}\n\nResearch: \n{state.research}"
        )
        state.review = response.text
        await ctx.send_message(state)


class FinalWriterExecutor(Executor):
    def __init__(self, agent: Agent, id: str = "final_writer") -> None:
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle(
        self, state: BriefingState, ctx: WorkflowContext[Never, str]
    ) -> None:
        response = await self.agent.run(
            "Use this feedback and the original research and your draft to create a final version:"
            f"Topic: {state.topic}\n\nFeedback: \n{state.review}\n\nDraft:\n{state.draft}\n\nResearch: \n{state.research}"
        )
        await ctx.yield_output(
            f"# Graph workflow briefing\n\n##Final: \n{response.text}\n\n## Research\n{state.research}"
        )


async def main() -> None:
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["FOUNDRY_MODEL"],
        credential=AzureCliCredential(),
    )

    researcher_agent = Agent(
        client=client, name="researcher", instructions=RESEARCHER_INSTRUCTIONS
    )
    writer_agent = Agent(client=client, name="writer", instructions=WRITER_INSTRUCTIONS)
    reviewer_agent = Agent(
        client=client, name="reviewer", instructions=REVIEWER_INSTRUCTIONS
    )

    researcher = ResearchExecutor(researcher_agent)
    writer = WriterExecutor(writer_agent)
    reviewer = ReviewerExecutor(reviewer_agent)
    final_writer = FinalWriterExecutor(writer_agent)

    workflow = (
        WorkflowBuilder(
            name="Briefing graph",
            description="Explicit researcher -> writer -> reviewer -> final writer graph workflow.",
            start_executor=researcher,
        )
        .add_edge(researcher, writer)
        .add_edge(writer, reviewer)
        .add_edge(reviewer, final_writer)
        .build()
    )
    events = await workflow.run(DEFAULT_TOPIC)
    outputs = events.get_outputs()
    print(outputs[-1] if outputs else "No graph workflow output was produced.")


if __name__ == "__main__":
    asyncio.run(main())
