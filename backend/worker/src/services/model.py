import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from src.model.gptj import GPT

logger = logging.getLogger(__name__)

_MODEL_QUERY_MAX_WORKERS = 4
_model_executor = ThreadPoolExecutor(
    max_workers=_MODEL_QUERY_MAX_WORKERS,
    thread_name_prefix="gpt-query",
)


async def query_model(gpt_client: GPT, prompt: str, timeout: float) -> str:
    loop = asyncio.get_running_loop()
    query_future = loop.run_in_executor(_model_executor, gpt_client.query, prompt)

    try:
        return await asyncio.wait_for(asyncio.shield(query_future), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(
            "Model query exceeded %.1fs timeout; it will keep running "
            "in the background until it finishes on its own.",
            timeout,
        )
        loop.create_task(_log_when_finished(query_future, timeout))
        raise


async def _log_when_finished(query_future: "asyncio.Future[str]", timeout: float) -> None:
    loop = asyncio.get_running_loop()
    waited_from = loop.time()

    try:
        await query_future
        elapsed = loop.time() - waited_from
        logger.info(
            "Orphaned model query finished ~%.1fs after its %.1fs timeout.",
            elapsed,
            timeout,
        )
    except Exception:
        logger.exception("Orphaned model query failed after its timeout.")