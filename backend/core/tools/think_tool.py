"""
core/tools/think_tool.py — Think Tool Executor
===============================================
Internal reasoning scratchpad.
Content is returned to the LLM but NOT shown to the user.
Enables chain-of-thought before complex decisions.
"""

import json


async def execute_think(args: dict) -> str:
    thought = args.get("thought", "")
    # Just echo back — the value is the LLM reading its own reasoning
    # before choosing the next action
    return json.dumps({
        "thought_recorded": True,
        "length_chars": len(thought),
        "note": "Internal reasoning captured. Continue with next action.",
    })
