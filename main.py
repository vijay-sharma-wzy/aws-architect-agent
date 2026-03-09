"""
CLI entrypoint
"""

import sys
import asyncio
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()

from arch_agent.graph import app as agent_graph


async def run(prompt: str):
    print(f"\n Prompt: {prompt}\n")
    print("Running architecture agent...\n")

    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "prompt": prompt,
        "arch_spec": {},
        "diagram_path": "",
        "critique": "",
        "revision_count": 0,
        "explanation": "",
    }

    # The event loop pauses HERE while waiting for the Anthropic API response.
    # If there were other coroutines scheduled (e.g. a second agent_graph.ainvoke()
    # running a different prompt in parallel), the event loop would run those now
    # instead of sitting idle. Example:
    #
    #   result1, result2 = await asyncio.gather(
    #       agent_graph.ainvoke(state_for_prompt_1),
    #       agent_graph.ainvoke(state_for_prompt_2),  # runs concurrently with the first
    #   )
    #
    # Both API calls would be in-flight at the same time, cutting total wait time roughly in half.
    result = await agent_graph.ainvoke(initial_state)

    print("=" * 60)
    print("DIAGRAM:", result.get("diagram_path", "N/A"))
    print("=" * 60)
    print("\nCRITIQUE:", result.get("critique", "N/A"))
    print("=" * 60)
    print("\nEXPLANATION:\n")
    print(result.get("explanation", "N/A"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<your architecture prompt>\"")
        print("Example: python main.py \"Design a serverless e-commerce backend\"")
        sys.exit(1)
    prompt = " ".join(sys.argv[1:])
    asyncio.run(run(prompt))
