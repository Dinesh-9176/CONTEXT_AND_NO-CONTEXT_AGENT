"""
JsonFileMemoryService — persistent long-term memory service for ADK.

Extends BaseMemoryService to store extracted facts in a JSON file.
At session end, uses heuristic regex to extract salient facts from
the conversation and persists them to data/memories.json.
"""

import json
import os
import re
from datetime import datetime, timezone

from google.adk.memory import BaseMemoryService
from google.adk.sessions import Session
from google.genai import types

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "memories.json")


class JsonFileMemoryService(BaseMemoryService):

    def __init__(self, memory_file: str | None = None):
        self._memory_file = os.path.normpath(memory_file or MEMORY_FILE)
        os.makedirs(os.path.dirname(self._memory_file), exist_ok=True)

    def _load(self) -> list[dict]:
        if not os.path.exists(self._memory_file):
            return []
        with open(self._memory_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save(self, memories: list[dict]) -> None:
        with open(self._memory_file, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)

    async def add_session_to_memory(self, session: Session) -> None:
        if not session.events:
            return

        conversation_lines = []
        for event in session.events:
            if event.content and event.content.parts:
                role = event.content.role or "unknown"
                for part in event.content.parts:
                    if part.text:
                        conversation_lines.append(f"{role}: {part.text}")

        if not conversation_lines:
            return

        facts = self._extract_facts_heuristic("\n".join(conversation_lines))
        if facts:
            memories = self._load()
            existing = {m["fact"].strip().lower() for m in memories}
            for fact in facts:
                if fact.strip().lower() not in existing:
                    memories.append({
                        "fact": fact.strip(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "auto_extracted",
                    })
                    existing.add(fact.strip().lower())
            self._save(memories)

    def _extract_facts_heuristic(self, conversation_text: str) -> list[str]:
        patterns = [
            (r"my name is (.+?)(?:[\.\,\!\?]|$)", "User's name is {}"),
            (r"i(?:'m| am) called (.+?)(?:[\.\,\!\?]|$)", "User is called {}"),
            (r"i(?:'m| am) ([A-Za-z\s]+)(?:[\.\,\!\?]|$)", "User's name is {}"), # e.g. "i'm dinesh kumar"
            (r"(?:my )?birthday is (.+?)(?:[\.\,\!\?]|$)", "User's birthday is {}"), # e.g. "my birthday is april 30"
            (r"today (.+?) is my birthday(?:[\.\,\!\?]|$)", "User's birthday is {}"), # e.g. "today april 30 is my birthday"
            (r"(?:my )?guide(?:'s)? name(?: is)? (.+?)(?:[\.\,\!\?]|$)", "User's guide is {}"),
            (r"i work (?:at|for) (.+?)(?:[\.\,\!\?]|$)", "User works at {}"),
            (r"i(?:'m| am) working on (.+?)(?:[\.\,\!\?]|$)", "User is working on {}"),
            (r"i(?:'m| am) a (.+?)(?:[\.\,\!\?]|$)", "User is a {}"),
            (r"i live in (.+?)(?:[\.\,\!\?]|$)", "User lives in {}"),
            (r"i prefer (.+?)(?:[\.\,\!\?]|$)", "User prefers {}"),
            (r"i like (.+?)(?:[\.\,\!\?]|$)", "User likes {}"),
            (r"i love (.+?)(?:[\.\,\!\?]|$)", "User loves {}"),
            (r"my favorite (.+?) is (.+?)(?:[\.\,\!\?]|$)", "User's favorite {} is {}"),
            (r"i got selected in (.+?)(?:[\.\,\!\?]|$)", "User got selected in {}"),
        ]

        user_lines = [
            line.split(":", 1)[1].strip()
            for line in conversation_text.split("\n")
            if line.lower().startswith("user:")
        ]
        user_text = " ".join(user_lines).lower() + "."

        facts = []
        for pattern, template in patterns:
            for match in re.finditer(pattern, user_text, re.IGNORECASE):
                groups = match.groups()
                if len(groups) == 1:
                    facts.append(template.format(groups[0].strip()))
                elif len(groups) == 2:
                    facts.append(template.format(groups[0].strip(), groups[1].strip()))
        return facts

    async def search_memory(self, *, app_name: str, user_id: str, query: str) -> list[types.Content]:
        memories = self._load()
        if not memories:
            return []

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
                scored.append((score, mem["fact"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return []

        memory_text = "Relevant memories from past conversations:\n"
        for _, fact in scored[:10]:
            memory_text += f"- {fact}\n"

        return [types.Content(role="user", parts=[types.Part(text=memory_text)])]
