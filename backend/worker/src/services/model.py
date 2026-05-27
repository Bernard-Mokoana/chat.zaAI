import asyncio
from src.model.gptj import GPT

async def query_model(gpt_client: GPT, prompt: str, timeout: float) -> str:
    # Runs the GPT model query in a thread with a timeout guard.
    # Raises: asyncio.TimeoutError: if the model exceeds the allowed duration.
    # Exception: propagates any model-level error upward
    return await asyncio.wait_for(
        asyncio.to_thread(gpt_client.query, prompt),
        timeout=timeout,
    )