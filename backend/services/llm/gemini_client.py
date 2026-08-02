"""
Google Gemini provider.

Notes on the request shape, because the choices are not arbitrary:

* `system_instruction` rather than prepending the system prompt to the user
  turn. Gemini treats it as a separate channel, and the seven rules in
  ANALYSIS_SYSTEM carry more weight there than they do as prose the model reads
  alongside the evidence.
* `response_json_schema` when a schema is supplied, falling back to plain
  `application/json` if the API rejects the schema. Gemini accepts a subset of
  JSON Schema, and our schema is written for Anthropic's validator - rather than
  maintain two schemas that can drift apart, we try the strict path once and
  degrade to mime-type-only, which the tolerant parser in base.py already
  handles. The degradation is reported as a warning, not hidden.
* Thinking is capped rather than left dynamic. This one is not a preference,
  it is a bug fix. On Gemini 2.5 the reasoning tokens are billed against the
  same `max_output_tokens` budget as the answer, so a request that thinks hard
  starves its own response. We measured a 2000-token challenge call spending
  1805 on thinking and 165 on the answer - close enough to the ceiling that
  whether the JSON came back complete was a coin flip. Reserving a fixed share
  of the budget for the answer makes the failure impossible rather than rare.
"""

from __future__ import annotations

import time

from .base import LLMError, LLMResult

# Finish reasons that mean "there is no usable answer in this response".
# Checked before reading .text, because a blocked response still returns 200.
_BLOCKED = {
    "SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION", "IMAGE_SAFETY",
}

# Google answers an invalid key with 400, not 401, so the status code alone
# cannot tell an auth failure apart from a malformed request.
_AUTH_HINTS = ("api key not valid", "api_key_invalid", "invalid authentication")

# Deliberately says nothing about which prefix is "correct". Google has issued
# at least two API key formats (the older `AIza...` and the newer `AQ....`),
# both valid, and an earlier version of this file asserted the newer one was an
# OAuth token and would be rejected. It was wrong, and it sent a user hunting
# for a problem with their key that did not exist. Let the API decide what it
# accepts; our job is to report what it said.
_KEY_ADVICE = (
    "Google rejected the API key. Check GEMINI_API_KEY in .env - that it is "
    "present, complete, and belongs to a project with the Gemini API enabled. "
    "Create or inspect keys at https://aistudio.google.com/apikey"
)

# Share of max_output_tokens the answer is guaranteed. Gemini 2.5 counts
# reasoning against the same budget, so without this the model can think its
# own response into truncation.
_ANSWER_RESERVE = 0.5
_MIN_THINKING_BUDGET = 512


def _is_auth_failure(message: str) -> bool:
    lowered = (message or "").lower()
    return any(hint in lowered for hint in _AUTH_HINTS)


class GeminiClient:
    provider = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise LLMError(
                "The 'google-genai' package is not installed. "
                "Run: pip install -r requirements.txt"
            ) from exc

        self._genai = genai
        self._types = types
        self._errors = errors
        self._client = genai.Client(api_key=api_key)
        self.model = model

    def _config(self, system: str, max_tokens: int, json_schema: dict | None, strict: bool):
        config: dict = {
            "system_instruction": system,
            "max_output_tokens": max_tokens,
            # Leave the answer at least half the budget. Without this the model
            # can spend the whole allowance reasoning and return a JSON object
            # cut off mid-string.
            "thinking_config": self._types.ThinkingConfig(
                thinking_budget=max(
                    _MIN_THINKING_BUDGET, int(max_tokens * (1 - _ANSWER_RESERVE))
                )
            ),
        }
        if json_schema is not None:
            config["response_mime_type"] = "application/json"
            if strict:
                config["response_json_schema"] = json_schema
        return self._types.GenerateContentConfig(**config)

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        json_schema: dict | None = None,
    ) -> LLMResult:
        warnings: list[str] = []
        started = time.perf_counter()

        def call(strict: bool):
            return self._client.models.generate_content(
                model=self.model,
                contents=user,
                config=self._config(system, max_tokens, json_schema, strict),
            )

        try:
            try:
                response = call(strict=json_schema is not None)
            except self._errors.ClientError as exc:
                # A 400 with a schema attached is usually the schema itself, so
                # retry once without it rather than failing over a validator
                # difference. A bad key also returns 400, and retrying that just
                # burns a second round trip - so check the message first.
                retryable = (
                    json_schema is not None
                    and exc.code == 400
                    and not _is_auth_failure(exc.message)
                )
                if retryable:
                    warnings.append(
                        "Gemini rejected the strict JSON schema; retried with "
                        "JSON mime-type only. Output was parsed leniently."
                    )
                    response = call(strict=False)
                else:
                    raise
        except self._errors.ClientError as exc:
            code = getattr(exc, "code", None)
            if code in (401, 403) or _is_auth_failure(exc.message):
                raise LLMError(_KEY_ADVICE) from exc
            if code == 404:
                raise LLMError(
                    f"Model '{self.model}' was not found. Check GEMINI_MODEL in .env."
                ) from exc
            if code == 429:
                raise LLMError(
                    "Gemini rate limit or quota exhausted. Wait and try again, or "
                    "check the quota on your API key."
                ) from exc
            raise LLMError(f"Gemini API error ({code}): {exc.message}") from exc
        except self._errors.ServerError as exc:
            raise LLMError(
                f"Gemini is unavailable ({getattr(exc, 'code', '5xx')}). Try again shortly."
            ) from exc
        except Exception as exc:  # noqa: BLE001 - network stack, not the API
            raise LLMError(f"Could not reach the Gemini API: {exc}") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)

        # A blocked or truncated response is a successful HTTP call with no
        # usable content, so finish_reason has to be checked before .text.
        candidate = (response.candidates or [None])[0]
        finish = getattr(getattr(candidate, "finish_reason", None), "name", None)

        if finish in _BLOCKED:
            raise LLMError(
                f"Gemini declined to analyse this input (finish_reason={finish}). "
                "Remove content that could read as an attack write-up and retry."
            )
        if finish == "MAX_TOKENS":
            warnings.append(
                "The response hit the output-token limit and may be truncated. "
                "Raise MAX_OUTPUT_TOKENS in .env or shorten the input."
            )

        usage = response.usage_metadata
        thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0
        answer_tokens = getattr(usage, "candidates_token_count", 0) or 0

        # Truncation on a thinking model does not always arrive as MAX_TOKENS -
        # we have seen finish_reason STOP on a response cut mid-string. If
        # reasoning took most of the budget, say so, because the symptom
        # otherwise looks like the model simply answering badly.
        if thinking_tokens and thinking_tokens > max_tokens * 0.75:
            warnings.append(
                f"Reasoning used {thinking_tokens} of the {max_tokens}-token output "
                "budget, leaving little room for the answer. Raise MAX_OUTPUT_TOKENS "
                "in .env if the result looks cut short."
            )

        return LLMResult(
            text=response.text or "",
            provider=self.provider,
            model=self.model,
            duration_ms=duration_ms,
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=answer_tokens,
            thinking_tokens=thinking_tokens,
            warnings=warnings,
        )
