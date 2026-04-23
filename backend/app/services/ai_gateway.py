import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIGatewayError(Exception):
    """Raised when AI Gateway is unavailable after all retries."""


class AIGatewayClient:
    """
    Client for internal AI Gateway (InHouse/Qwen3.5-122B).
    External LLMs are forbidden per NFR-08 / ADR-002 v2.0.
    """

    def __init__(self) -> None:
        self._base_url = settings.AI_GATEWAY_URL.rstrip("/")
        self._model = settings.AI_GATEWAY_MODEL
        self._headers = {
            "Authorization": f"Bearer {settings.AI_GATEWAY_API_KEY}",
            "Content-Type": "application/json",
        }

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=False,
    )
    async def _call(self, messages: list[dict], max_tokens: int = 2048) -> str:
        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        async with httpx.AsyncClient(timeout=settings.AI_GATEWAY_TIMEOUT) as client:
            resp = await client.post(
                f"{self._base_url}/v1/chat/completions",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
        context: dict | None = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            result = await self._call(messages, max_tokens=max_tokens)
            logger.info(
                "ai_gateway_call_ok",
                extra={"model": self._model, "context": context or {}},
            )
            return result
        except Exception as exc:
            logger.error("ai_gateway_failed", extra={"error": str(exc)})
            raise AIGatewayError(f"AI Gateway unavailable after 3 retries: {exc}") from exc


ai_client = AIGatewayClient()
