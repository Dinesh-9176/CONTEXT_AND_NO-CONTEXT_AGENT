"""
Custom tools for the context agent — memory management.
"""

import json
import os
from datetime import datetime, timezone

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "memories.json")


def _load_memories() -> list[dict]:
    path = os.path.normpath(MEMORY_FILE)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_memories(memories: list[dict]) -> None:
    path = os.path.normpath(MEMORY_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)


def remember_fact(fact: str) -> dict:
    """Save a fact to long-term memory so it can be recalled in future conversations.

    Use this tool when the user shares personal information, preferences,
    goals, project details, or anything worth remembering across sessions.

    Args:
        fact: A clean, concise fact to remember. Example: "User's name is Dinesh"

    Returns:
        A confirmation dict with the saved fact.
    """
    fact = fact.strip()

    if len(fact) < 5:
        return {"status": "rejected", "reason": "Fact is too short."}

    trivial_patterns = [
        "user said", "user asked", "user is online", "user is talking",
        "user greeted", "user wants to chat", "user is here", "first time",
        "greeted the agent", "has greeted"
    ]
    fact_lower = fact.lower()
    for pattern in trivial_patterns:
        if pattern in fact_lower:
            return {"status": "rejected", "reason": f"Too trivial: '{pattern}'"}

    memories = _load_memories()
    for existing in memories:
        if existing.get("fact", "").strip().lower() == fact_lower:
            return {"status": "already_known", "fact": fact}

    memories.append({
        "fact": fact,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "explicit",
    })
    _save_memories(memories)
    return {"status": "saved", "fact": fact, "total_memories": len(memories)}


def recall_memories(query: str) -> dict:
    """Search long-term memory for facts relevant to a query.

    Use this tool when the user asks about something from a past conversation,
    or when you need context about the user's preferences, name, projects, etc.

    Args:
        query: The search query — what you're trying to recall.

    Returns:
        A dict with matching memories, or an empty list if nothing found.
    """
    memories = _load_memories()
    if not memories:
        return {"matches": [], "message": "No memories stored yet."}

    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored = []
    for mem in memories:
        fact_lower = mem["fact"].lower()
        overlap = query_words & set(fact_lower.split())
        score = len(overlap)
        if query_lower in fact_lower:
            score += 3
        if score > 0:
            scored.append({"fact": mem["fact"], "timestamp": mem["timestamp"], "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:10]

    if not top:
        return {"matches": [], "message": f"No memories found matching '{query}'."}

    return {"matches": [m["fact"] for m in top], "count": len(top)}
