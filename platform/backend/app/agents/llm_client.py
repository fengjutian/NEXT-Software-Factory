"""LLM client — unified interface for Claude and OpenAI APIs."""

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import get_settings


class LLMError(Exception):
    """LLM API call error."""

    def __init__(self, message: str, status_code: int | None = None, retry_after: float | None = None):
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(message)


class LLMClient:
    """Unified LLM client supporting Claude (Anthropic) and GPT (OpenAI)."""

    def __init__(self):
        settings = get_settings()
        self.provider = settings.llm_provider
        self.model = settings.llm_model

        if self.provider == "claude":
            self._client = AsyncAnthropic(api_key=settings.llm_api_key)
        elif self.provider == "openai":
            self._client = AsyncOpenAI(api_key=settings.llm_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 16000,
    ) -> str:
        """Send a completion request and return the text response.

        Raises:
            LLMError: On API errors.
        """
        try:
            if self.provider == "claude":
                return await self._complete_claude(system_prompt, user_prompt, temperature, max_tokens)
            else:
                return await self._complete_openai(system_prompt, user_prompt, temperature, max_tokens)
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"LLM 调用失败: {str(e)}") from e

    async def _complete_claude(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Call Claude API."""
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            # Extract text from the first content block
            content = response.content
            if content and len(content) > 0:
                return content[0].text
            return ""
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower():
                raise LLMError("速率限制", status_code=429, retry_after=10.0)
            if "500" in error_str or "server_error" in error_str.lower():
                raise LLMError("服务端错误", status_code=500)
            if "401" in error_str or "403" in error_str:
                raise LLMError("LLM API Key 无效", status_code=401)
            raise LLMError(f"Claude API 错误: {error_str[:200]}")

    async def _complete_openai(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Call OpenAI API."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower():
                raise LLMError("速率限制", status_code=429, retry_after=10.0)
            if "500" in error_str or "server_error" in error_str.lower():
                raise LLMError("服务端错误", status_code=500)
            raise LLMError(f"OpenAI API 错误: {error_str[:200]}")
