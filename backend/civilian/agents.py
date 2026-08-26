from __future__ import annotations

import json
import os

SYSTEM_PROMPT = """
You are LAFRE Public Help. Answer only from the supplied Knowledge Base extracts.
Do not show source IDs, KB IDs, file paths, URLs, debug fields or raw citations to civilians.
Return one JSON object with: title, summary, plain_language_answer, important_points, procedures, next_steps, proof_items, needs_police, needs_healthcare, needs_lawyer, service_contacts, suggested_actions.
If the extracts contain police, community office, court, notarial/commissioner, legal aid, council, healthcare or other useful contact/referral details that are relevant to the issue, include them in service_contacts as short public-friendly items.
Do not invent contact details. If contact details are not in the extracts, leave service_contacts empty and let the admin alert flow handle missing resources.
If the extracts do not contain enough information, return mode admin_review and do not invent law.
""".strip()


def build_agent_answer(prompt: str, kb_context: str, user_facts: dict | None = None) -> dict:
    """Optional Strands/Bedrock answer builder. Falls back safely if agent deps are unavailable."""
    if not kb_context.strip():
        return {"mode": "admin_review", "title": "More verified material needed"}
    try:
        from strands import Agent
        from strands.models import BedrockModel
        model = BedrockModel(
            model_id=os.getenv("CIVILIAN_AGENT_MODEL_ID", "us.amazon.nova-lite-v1:0"),
            max_tokens=int(os.getenv("CIVILIAN_AGENT_MAX_TOKENS", "3500")),
            temperature=float(os.getenv("CIVILIAN_AGENT_TEMPERATURE", "0.05")),
        )
        agent = Agent(name="LAFREPublicHelpAgent", model=model, system_prompt=SYSTEM_PROMPT, tools=[])
        message = f"User issue:\n{prompt}\n\nUser facts:\n{json.dumps(user_facts or {}, ensure_ascii=False)}\n\nKnowledge Base extracts:\n{kb_context}"
        result = agent(message)
        raw = result.message.content[0].text if hasattr(result, "message") else str(result)
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end+1])
    except Exception:
        pass
    return {
        "mode": "legal_guidance",
        "title": "Legal guidance prepared",
        "summary": "LAFRE found relevant legal material and prepared a simple guided response.",
        "plain_language_answer": "Based on the available legal material, prepare your facts carefully, keep proof, avoid using force or informal retaliation, and use the safest lawful reporting or review route for the issue.",
        "important_points": ["Keep written proof and dates.", "Do not rely on verbal discussions only.", "Request admin/lawyer review where the document or procedure has legal consequences."],
        "procedures": ["Write down what happened.", "Collect documents and messages.", "Use the recommended document or review route."],
        "next_steps": ["Save this matter.", "Generate a document if needed.", "Submit for review if the issue is high risk or unclear."],
        "proof_items": ["Messages", "Receipts", "Photos", "Witness details", "Any written agreement"],
        "needs_police": any(w in prompt.lower() for w in ["assault", "threat", "violence", "stolen", "theft", "arrest"]),
        "needs_healthcare": any(w in prompt.lower() for w in ["injury", "injured", "assault", "beaten"]),
        "needs_lawyer": True,
        "service_contacts": [],
        "suggested_actions": ["Create document", "Submit for review", "Find lawyer"],
    }
