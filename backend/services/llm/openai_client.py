"""
OpenAI provider.

This exists so the project can answer one of the brief's explicit requirements:
"comparing multiple prompts or models". Running the same prompt through a second
vendor is the cheapest way to tell "the model believes this" apart from "this is
what the evidence supports" — when two independent models disagree about the
root cause on identical input, the disagreement is the finding.
"""

from __future__ import annotations

import time

from .base import LLMError, LLMResult


class OpenAIClient:
    provider = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        try:
            import openai  # imported lazily so the package stays optional
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise LLMError(
                "The 'openai' package is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self._sdk = openai
        self._client = openai.OpenAI(api_key=api_key)
        self.model = model

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        json_schema: dict | None = None,
    ) -> LLMResult:
        started = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_schema else None,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except self._sdk.AuthenticationError as exc:
            raise LLMError("OpenAI rejected the API key. Check OPENAI_API_KEY in .env.") from exc
        except self._sdk.RateLimitError as exc:
            raise LLMError("OpenAI rate limit reached. Wait a minute and try again.") from exc
        except self._sdk.APIConnectionError as exc:
            raise LLMError("Could not reach the OpenAI API. Check the network connection.") from exc
        except self._sdk.APIStatusError as exc:
            raise LLMError(f"OpenAI API error ({exc.status_code}).") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)
        choice = response.choices[0]
        warnings: list[str] = []
        if choice.finish_reason == "length":
            warnings.append(
                "The response hit the output-token limit and may be truncated. "
                "Raise MAX_OUTPUT_TOKENS in .env or shorten the input."
            )

        usage = response.usage
        return LLMResult(
            text=choice.message.content or "",
            provider=self.provider,
            model=self.model,
            duration_ms=duration_ms,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            warnings=warnings,
        )
