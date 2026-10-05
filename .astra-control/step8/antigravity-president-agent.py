#!/usr/bin/env python3
import argparse
import asyncio
import inspect
import json
import os
from pathlib import Path

from google.antigravity import Agent, LocalAgentConfig

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["decision", "move_id", "note"],
    "properties": {
        "decision": {"type": "string", "enum": ["PLAY", "PASS"]},
        "move_id": {"type": ["string", "null"]},
        "note": {"type": "string", "maxLength": 400},
    },
}

SYSTEM_INSTRUCTIONS = """
You are ANTIGRAVITY, a bounded GAMEZEL President-of-Formulas occupant.
The game engine has already produced the authoritative legal move list.
Choose only PLAY or PASS. A PLAY must use exactly one supplied move_id.
Never invent cards, targets, support, formulas, calculations, or verdicts.
Do not use tools, shell, filesystem, web, deployment, editing, credentials,
external requests, or side effects. Do not expose chain-of-thought.
Return only the response required by response_schema.
""".strip()


def jsonable(value):
    if value is None:
        return None
    if isinstance(value, (dict, list, str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return json.loads(json.dumps(value, default=str))


async def main(prompt: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured for ANTIGRAVITY")

    kwargs = dict(
        system_instructions=SYSTEM_INSTRUCTIONS,
        tools=[],
        workspaces=[],
        response_schema=RESPONSE_SCHEMA,
        api_key=api_key,
    )
    model = os.environ.get("ANTIGRAVITY_MODEL")
    if model:
        kwargs["model"] = model

    config = LocalAgentConfig(**kwargs)
    async with Agent(config) as agent:
        response = agent.chat(prompt)
        if inspect.isawaitable(response):
            response = await response
        resolved = response.resolve()
        if inspect.isawaitable(resolved):
            await resolved

        structured = getattr(response, "structured_output", None)
        if structured is not None:
            value = structured() if callable(structured) else structured
            if inspect.isawaitable(value):
                value = await value
            print(json.dumps(jsonable(value), ensure_ascii=False))
            return

        text_value = getattr(response, "text", None)
        if callable(text_value):
            text_value = text_value()
        if inspect.isawaitable(text_value):
            text_value = await text_value
        if not text_value:
            raise RuntimeError("Antigravity returned no structured_output or text")
        print(str(text_value))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-file", required=True)
    args = parser.parse_args()
    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    asyncio.run(main(prompt))
