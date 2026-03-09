from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ArchState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # append-only via add_messages reducer
    prompt: str                   # original user prompt
    arch_spec: dict               # parsed JSON spec: {nodes, edges, groups}
    diagram_path: str             # absolute path to rendered PNG
    critique: str                 # feedback from critic node
    revision_count: int           # tracks how many revision loops have run
    explanation: str              # plain-English summary from explainer node
