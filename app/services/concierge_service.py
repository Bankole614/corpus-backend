"""
Concierge / Design Brief Builder service.

Design intent (see PRD section 6.1):
- This is a guided conversation, not an open-ended chatbot. The system prompt
  actively steers toward specific missing information (meaning/intent, style,
  placement, size) rather than just being generically helpful.
- The model self-reports readiness via `ready_for_brief` so the client knows
  when to offer "generate my brief" instead of continuing to chat.
- The brief output is intentionally NOT a design/image — it's a structured
  summary an artist can work from. This service must never be extended to
  generate actual tattoo artwork (see PRD non-goals — AI-as-generator was a
  deliberate exclusion, not an oversight).
"""

import json

from google.genai import types

from app.core.config import settings
from app.core.llm_client import get_client
from app.models.concierge import BriefRequest, ChatMessage, ConciergeChatRequest, TattooBrief

_CHAT_SYSTEM_PROMPT = """You are the Corpus concierge — a warm, patient guide helping someone think \
through a tattoo idea before they ever talk to an artist. The person may be a first-timer and anxious \
about permanence, so be encouraging but never pushy toward a decision.

Your job across the conversation is to draw out, through natural conversation (not an interrogation):
1. The meaning or story behind what they want (why this, why now)
2. Style leanings (e.g. fine line, bold/traditional, blackwork, illustrative, geometric — don't assume, ask)
3. Placement thoughts (where on the body, and whether they've considered visibility/pain/sizing tradeoffs)
4. Rough size expectations

Ask ONE focused question at a time — don't dump a checklist on them. Follow their energy: if they're \
unsure about something, help them think it through rather than rushing past it. If they mention a phrase \
or symbol from a specific language or culture, gently note that Corpus has a separate verification tool \
for that, don't try to verify it yourself in this conversation.

You do not generate or describe actual visual designs — that's the artist's job. You help them articulate \
intent clearly enough that an artist can take it from here.

Respond with ONLY a valid JSON object matching exactly this schema:
{
  "reply": string,
  "ready_for_brief": boolean
}

Set "ready_for_brief" to true only once you have a reasonable sense of meaning, style direction, and \
placement — it doesn't need to be exhaustive, just enough for a useful brief. Default to false while \
real ambiguity remains.
"""

_BRIEF_SYSTEM_PROMPT = """You are generating a structured tattoo brief from a conversation between a \
user and the Corpus concierge. This brief will be shown to the user and optionally shared with a tattoo \
artist. Be concrete and grounded ONLY in what was actually discussed — do not invent details, meanings, \
or style preferences the user didn't express or clearly imply.

Respond with ONLY a valid JSON object matching exactly this schema:
{
  "concept_summary": string,
  "suggested_styles": [string, ...],
  "historical_or_cultural_context": string or null,
  "placement_notes": string or null,
  "risks_or_considerations": [string, ...],
  "open_questions": [string, ...]
}

- "risks_or_considerations" should flag anything genuinely worth flagging (e.g. fine detail that may not \
hold up at small size, a placement with higher pain/healing complexity, a symbol/text element that should \
go through the separate verification tool).
- "open_questions" are things still worth discussing with an artist directly — not things you're unsure \
about from the conversation.
- If the conversation didn't cover something (e.g. placement was never discussed), leave that field null \
or empty rather than guessing.
"""


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _messages_to_gemini_contents(messages: list[ChatMessage]) -> list[types.Content]:
    contents: list[types.Content] = []
    for m in messages:
        role = "model" if m.role == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=m.content)],
            )
        )
    return contents


class ConciergeError(Exception):
    pass


async def continue_chat(req: ConciergeChatRequest) -> dict:
    try:
        client = get_client()
    except RuntimeError as e:
        raise ConciergeError(str(e)) from e

    contents = _messages_to_gemini_contents(req.messages)

    try:
        response = await client.aio.models.generate_content(
            model=settings.concierge_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_CHAT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
    except Exception as e:
        raise ConciergeError(f"Gemini API request failed: {e}") from e

    raw_text = _clean_json_text(response.text or "")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ConciergeError(f"Model did not return valid JSON: {e}\nRaw output: {raw_text}") from e

    return {
        "reply": parsed.get("reply", ""),
        "ready_for_brief": bool(parsed.get("ready_for_brief", False)),
    }


async def generate_brief(req: BriefRequest) -> TattooBrief:
    try:
        client = get_client()
    except RuntimeError as e:
        raise ConciergeError(str(e)) from e

    contents = _messages_to_gemini_contents(req.messages)

    try:
        response = await client.aio.models.generate_content(
            model=settings.concierge_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_BRIEF_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )
    except Exception as e:
        raise ConciergeError(f"Gemini API request failed: {e}") from e

    raw_text = _clean_json_text(response.text or "")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ConciergeError(f"Model did not return valid JSON: {e}\nRaw output: {raw_text}") from e

    return TattooBrief(
        concept_summary=parsed.get("concept_summary", ""),
        suggested_styles=parsed.get("suggested_styles", []),
        historical_or_cultural_context=parsed.get("historical_or_cultural_context"),
        placement_notes=parsed.get("placement_notes"),
        risks_or_considerations=parsed.get("risks_or_considerations", []),
        open_questions=parsed.get("open_questions", []),
    )

