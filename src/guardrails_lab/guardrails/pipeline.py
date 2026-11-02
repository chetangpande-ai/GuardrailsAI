import json
import os
from dataclasses import dataclass
from typing import Callable

from pydantic import ValidationError

from guardrails_lab.guardrails.checks import has_injection_signal, redact_simple_pii
from guardrails_lab.guardrails.schemas import MovieReview


@dataclass(frozen=True)
class PipelineOutcome:
    action: str
    reason: str
    payload: dict[str, object] | None = None


def mock_movie_generator(_: str) -> str:
    return json.dumps(
        {
            "title": "Inception",
            "sentiment": "positive",
            "key_points": [
                "Inventive concept",
                "Contact reviews@example.com for feedback",
            ],
        }
    )


def groq_movie_generator(prompt: str) -> str:
    """Call Groq only when explicitly requested and configured."""
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Set GROQ_API_KEY in .env before using the Groq demo.")

    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError(
            'Install the optional Groq dependency with "uv sync --extra groq".'
        ) from exc

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Return only a JSON object with title, sentiment "
                    "(positive, negative, or mixed), and 2-3 key_points."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty response.")
    return content


def answer_movie_review(
    prompt: str,
    *,
    generator: Callable[[str], str] = mock_movie_generator,
) -> PipelineOutcome:
    if has_injection_signal(prompt):
        return PipelineOutcome("BLOCK", "Potential instruction-override signal")

    try:
        review = MovieReview.model_validate_json(generator(prompt))
    except (ValidationError, ValueError, TypeError):
        return PipelineOutcome("RETRY", "Invalid model JSON/schema; no answer released")

    safe_review = review.model_copy(
        update={
            "title": redact_simple_pii(review.title),
            "key_points": [redact_simple_pii(point) for point in review.key_points],
        }
    )
    return PipelineOutcome(
        "ALLOW",
        "Schema checked and baseline PII redaction applied",
        safe_review.model_dump(),
    )
