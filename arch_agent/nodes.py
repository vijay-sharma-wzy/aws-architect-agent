"""
LangGraph node functions for the AWS Architecture Agent.

Nodes:
  architect  — Claude designs the architecture and calls render_architecture
  critic     — Claude reviews the rendered architecture for AWS best practices
  explainer  — Claude writes a plain-English summary of the final design
"""

import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import ToolNode

from arch_agent.state import ArchState
from arch_agent.tools import render_architecture

### Model setup 

_llm = ChatAnthropic(model="claude-opus-4-6", temperature=0)
_architect_llm = _llm.bind_tools([render_architecture])

TOOLS = [render_architecture]
tool_node = ToolNode(TOOLS)

### System prompts 

ARCHITECT_SYSTEM = """You are an expert AWS solutions architect.

Given a user's requirements, design a well-architected AWS solution and call the
`render_architecture` tool EXACTLY ONCE with a complete JSON spec.

Rules:
- Choose only services that are necessary for the requirements
- Use realistic, descriptive labels for each node
- Group related services into logical clusters (e.g. VPC, Data Layer, Frontend)
- Include edges that show data/request flow with brief labels
- Always include observability (CloudWatch) and security (IAM/Cognito/WAF) where appropriate
- Output valid JSON — double-check your spec before calling the tool
"""

CRITIC_SYSTEM = """You are a senior AWS architect reviewing a proposed architecture.

Evaluate the architecture against the AWS Well-Architected Framework pillars:
  1. Operational Excellence
  2. Security
  3. Reliability
  4. Performance Efficiency
  5. Cost Optimization

Respond with ONLY one of:
  APPROVED: <one sentence reason>
  REVISE: <specific, actionable list of changes needed>

Be strict but fair. Approve if the architecture is solid even if not perfect.
Do not request changes for minor style preferences.
"""

EXPLAINER_SYSTEM = """You are a technical writer specialising in cloud architecture.

Write a clear, concise explanation of the AWS architecture for a technical audience.
Cover: what the architecture does, key service choices and why, data flow, and
any notable design decisions. Use markdown with headers and bullet points.
Keep it under 400 words.
"""


### Node functions

def architect(state: ArchState) -> dict:
    """
    Claude designs the architecture.
    On first call: builds messages from the raw user prompt.
    On revision: starts fresh with the original prompt + critique — avoids
    sending orphaned tool_result blocks that cause Anthropic 400 errors.
    """
    revision_count = state.get("revision_count", 0)
    critique = state.get("critique", "")

    if revision_count > 0 and critique:
        # Revision: build a fresh context for Claude (not using accumulated state messages
        # to avoid orphaned tool_result blocks). Return only the new messages to append.
        user_content = (
            f"Original requirement: {state['prompt']}\n\n"
            f"Your previous architecture was reviewed and needs changes:\n{critique}\n\n"
            f"Please redesign the architecture addressing the feedback and call render_architecture again."
        )
        send_messages = [
            SystemMessage(content=ARCHITECT_SYSTEM),
            HumanMessage(content=user_content),
        ]
    else:
        # First call
        send_messages = [
            SystemMessage(content=ARCHITECT_SYSTEM),
            HumanMessage(content=state["prompt"]),
        ]

    response = _architect_llm.invoke(send_messages)
    # Return only new messages — add_messages reducer appends them to state
    return {"messages": send_messages + [response]}


def critic(state: ArchState) -> dict:
    """
    Reviews the architecture. Extracts the diagram path from the last ToolMessage,
    then asks Claude to evaluate the spec.
    """
    messages = state["messages"]

    # Pull the rendered diagram path and arch spec from the last ToolMessage
    diagram_path = ""
    arch_spec = {}
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            diagram_path = msg.content  # the PNG path returned by render_architecture
            break

    # Extract the spec from the last AIMessage tool call args
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            raw = msg.tool_calls[0]["args"].get("spec", "{}")
            try:
                arch_spec = json.loads(raw)
            except json.JSONDecodeError:
                arch_spec = {}
            break

    critique_prompt = HumanMessage(
        content=(
            f"Review this AWS architecture spec:\n\n"
            f"```json\n{json.dumps(arch_spec, indent=2)}\n```\n\n"
            f"Diagram has been rendered to: {diagram_path}"
        )
    )

    critic_messages = [SystemMessage(content=CRITIC_SYSTEM), critique_prompt]
    response = _llm.invoke(critic_messages)

    return {
        "messages": messages,
        "critique": response.content,
        "diagram_path": diagram_path,
        "arch_spec": arch_spec,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def explainer(state: ArchState) -> dict:
    """
    Writes a plain-English markdown summary of the final architecture.
    """
    arch_spec = state.get("arch_spec", {})

    explain_prompt = HumanMessage(
        content=(
            f"Original requirement: {state['prompt']}\n\n"
            f"Final architecture spec:\n```json\n{json.dumps(arch_spec, indent=2)}\n```"
        )
    )

    exp_messages = [SystemMessage(content=EXPLAINER_SYSTEM), explain_prompt]
    response = _llm.invoke(exp_messages)

    return {"explanation": response.content}
