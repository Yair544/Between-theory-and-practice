"""
Anthropic (Claude) provider.

Notes on the request shape, because the choices are not arbitrary:

* Streaming. `max_tokens` is large enough that a non-streaming request risks an
  HTTP timeout, and the SDK refuses requests it estimates will run long. We
  stream and collect with `get_final_message()`, which gives timeout safety
  without having to handle individual events.
* Adaptive thinking. Incident analysis is exactly the multi-step reasoning case
  adaptive thinking exists for. Effort is left at "high"; "max" produced longer
  reasoning without better hypotheses in our testing (see docs/PROMPTS.md).
* Structured output. The response has to slot into a typed schema, so we ask for
  a JSON schema rather than parsing prose. This removes a whole class of
  "the model wrote a nice paragraph instead of the object" failures.
"""

from __future__ import annotations

import time

from .base import LLMError, LLMResult


class AnthropicClient:
    provider = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        try:
            import anthropic  # imported lazily so the package stays optional
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise LLMError(
                "The 'anthropic' package is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self._sdk = anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        json_schema: dict | None = None,
    ) -> LLMResult:
        output_config: dict = {"effort": "high"}
        if json_schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": json_schema}

        started = time.perf_counter()
        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                thinking={"type": "adaptive"},
                output_config=output_config,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                message = stream.get_final_message()
        except self._sdk.AuthenticationError as exc:
            raise LLMError(
                "Anthropic rejected the API key. Check ANTHROPIC_API_KEY in .env."
            ) from exc
        except self._sdk.RateLimitError as exc:
            raise LLMError(
                "Anthropic rate limit reached. Wait a minute and try again."
            ) from exc
        except self._sdk.NotFoundError as exc:
            raise LLMError(
                f"Model '{self.model}' was not found. Check ANTHROPIC_MODEL in .env."
            ) from exc
        except self._sdk.APIConnectionError as exc:
            raise LLMError(
                "Could not reach the Anthropic API. Check the network connection."
            ) from exc
        except self._sdk.APIStatusError as exc:
            raise LLMError(f"Anthropic API error ({exc.status_code}): {exc.message}") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)
        warnings: list[str] = []

        # A refusal is a successful HTTP response with no usable content, so it
        # has to be checked before reading the body.
        if message.stop_reason == "refusal":
            raise LLMError(
                "The model declined to analyse this input for safety reasons. "
                "Remove any content that could read as an attack write-up and retry."
            )
        if message.stop_reason == "max_tokens":
            warnings.append(
                "The response hit the output-token limit and may be truncated. "
                "Raise MAX_OUTPUT_TOKENS in .env or shorten the input."
            )

        text = "".join(block.text for block in message.content if block.type == "text")

        return LLMResult(
            text=text,
            provider=self.provider,
            model=self.model,
            duration_ms=duration_ms,
            input_tokens=getattr(message.usage, "input_tokens", 0) or 0,
            output_tokens=getattr(message.usage, "output_tokens", 0) or 0,
            warnings=warnings,
        )
