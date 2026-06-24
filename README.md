# Microsoft Agent Framework demo

This demo shows Microsoft Agent Framework features in small, runnable demos.
Later demos use the same briefing scenario: preparing a briefing about
reinforcement learning for AI agents. Each runnable
sample is intentionally self-contained so it can be opened and shown during a demo
without jumping through helper files.

1. A simple Foundry-backed agent with weather, time, web search, and local DevUI.
2. A Foundry-backed agent with Hyperlight CodeAct, exposed through local DevUI.
3. A small functional workflow with researcher, writer, reviewer, and final writer stages.
4. A full graph workflow with the same stages as explicit workflow nodes.
5. A harness agent for the same scenario, using a Textual console, plan/execute modes, and task-specific skills.
6. A simple DevUI agent with FIDES prompt-injection-defense setup.
7. A locally hosted Responses endpoint plus an Agent Framework client that calls it.

## Setup

Install dependencies from the latest GitHub Agent Framework packages and create the venv.
Hyperlight currently requires Python `<3.14`, so this project pins `3.13` in `.python-version`.

```powershell
uv sync
```

Configure Foundry access in `.env`:

```text
FOUNDRY_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project-name
FOUNDRY_MODEL=your-model-deployment-name
# Optional for demo 6; defaults to FOUNDRY_MODEL when omitted.
FOUNDRY_QUARANTINE_MODEL=your-smaller-model-deployment-name
```

Authenticate with Azure:

```powershell
az login
```

Start the local Aspire dashboard for OpenTelemetry traces and metrics:

```powershell
docker run --rm -d --name agent-framework-aspire-dashboard `
  -p 18888:18888 `
  -p 4317:18889 `
  -e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true `
  mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

All demos call `configure_otel_providers()` and read OpenTelemetry settings from your environment.
Open the dashboard at `http://localhost:18888`.
Demos 1, 2, 6, and 7 also emit app logs through OpenTelemetry because they do not use the command line for their main input/output flow.

The DevUI demos run locally without a separate DevUI auth token. Demo 1 uses port `8090`; demo 2 uses port `8091`; demo 6 uses port `8092`. The model still authenticates to Azure through `AzureCliCredential`.

## Run the demo

```powershell
uv run python demo1_simple_agent.py
uv run python demo2_codeact.py
uv run python demo3_functional.py
uv run python demo4_graph.py
uv run python demo5_harness.py
uv run python demo6_fides_agent.py
uv run python demo7_hosting.py
uv run python demo7b_call_hosted_agent.py
```

In the harness console, use `/plan` and `/execute` to switch modes, `/help` for commands, and `/quit` to exit.
For demo 7, start `demo7_hosting.py` in one terminal, then run `demo7b_call_hosted_agent.py` in another terminal.

## Code tour

- `demo1_simple_agent.py` has the Foundry client, weather tool, time tool, web search tool, agent, and DevUI startup in one file.
- `demo2_codeact.py` adds `HyperlightCodeActProvider` with sandbox-only `compute` and `fetch_data` tools, then serves the agent through DevUI.
- `demo3_functional.py` has the Foundry client, three agents, and the research -> draft -> review -> final functional workflow in one file.
- `demo4_graph.py` has the Foundry client, three agents, graph executors, and the same research -> draft -> review -> final graph in one file.
- `demo5_harness.py` has the Foundry client, harness agent setup, and file-based skills from `skills\`, then runs the shared upstream harness console.
- `demo6_fides_agent.py` serves a simple FIDES-protected agent in DevUI with untrusted external notes, a privileged publish tool, and user-visible policy approval when that tool is called from untrusted context.
- `demo7_hosting.py` serves a Foundry-backed agent through `AgentFrameworkHost` and `ResponsesChannel` at `POST /responses`.
- `demo7b_call_hosted_agent.py` uses an Agent Framework `Agent` backed by `OpenAIChatClient` to call that local Responses endpoint.
- `console\` is vendored from the latest `microsoft/agent-framework` harness console sample and is used by the harness demo.
- `skills\` contains file-based harness skills for briefing research, writing, and review, each in its own folder with `SKILL.md` and reference resources.
