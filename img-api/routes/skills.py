"""
Skills system for the Airi assistant.

Loads .md skill files from the img-api/skills/ directory using progressive disclosure:
- Discovery: Only name + description are loaded at startup (fast).
- Activation: Full SKILL.md content is read on-demand when trigger keywords match.
- Injection: Matched skill content is prepended to the system context for the LLM.
"""
import os
import re
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")

# ── Skill data classes ─────────────────────────────────────────────────────────
class SkillMeta(BaseModel):
    name: str
    description: str
    trigger_keywords: list[str] = []
    file_path: str


class SkillDetail(SkillMeta):
    content: str   # Full markdown body (loaded on demand)


# ── Skill parsing ──────────────────────────────────────────────────────────────
def _parse_skill_file(file_path: str) -> Optional[SkillMeta]:
    """
    Parse a skill .md file.  Returns SkillMeta (header only) on success.

    Expected format:
    ---
    name: skill_name
    description: one-line description
    trigger_keywords:
      - keyword1
      - keyword2
    ---
    # Full body here …
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        print(f"[Skills] Failed to read {file_path}: {e}")
        return None

    # Extract YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not fm_match:
        print(f"[Skills] No frontmatter found in {file_path}")
        return None

    fm_text = fm_match.group(1)

    def _extract(key: str, text: str) -> Optional[str]:
        m = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
        return m.group(1).strip() if m else None

    def _extract_list(key: str, text: str) -> list[str]:
        """Extract a YAML list block for the given key."""
        m = re.search(rf"^{key}:\s*\n((?:[ \t]+-[^\n]*\n?)+)", text, re.MULTILINE)
        if not m:
            return []
        block = m.group(1)
        return [
            re.sub(r"^[ \t]+-\s*", "", line).strip()
            for line in block.splitlines()
            if line.strip().startswith("-")
        ]

    name = _extract("name", fm_text)
    description = _extract("description", fm_text)
    if not name or not description:
        print(f"[Skills] Missing name or description in {file_path}")
        return None

    keywords = _extract_list("trigger_keywords", fm_text)

    return SkillMeta(
        name=name,
        description=description,
        trigger_keywords=keywords,
        file_path=file_path,
    )


def _load_skill_body(file_path: str) -> str:
    """Load the full markdown body (after frontmatter) for activation."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
        # Strip frontmatter
        body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw, flags=re.DOTALL)
        return body.strip()
    except Exception as e:
        print(f"[Skills] Failed to load body for {file_path}: {e}")
        return ""


# ── Skill registry (discovery at startup) ─────────────────────────────────────
_skills: list[SkillMeta] = []


def load_skills():
    """Scan the skills directory and populate the registry (name + description only)."""
    global _skills
    _skills = []

    skills_path = os.path.abspath(SKILLS_DIR)
    if not os.path.isdir(skills_path):
        print(f"[Skills] Skills directory not found: {skills_path}")
        return

    for fname in sorted(os.listdir(skills_path)):
        if not fname.endswith(".md"):
            continue
        full = os.path.join(skills_path, fname)
        meta = _parse_skill_file(full)
        if meta:
            _skills.append(meta)

    print(f"[Skills] Loaded {len(_skills)} skill(s): {[s.name for s in _skills]}")


load_skills()


# ── Skill activation ───────────────────────────────────────────────────────────
def get_relevant_skills(user_message: str) -> list[SkillDetail]:
    """
    Progressive disclosure — only activate skills whose trigger keywords appear
    in the user's message.  Returns full SkillDetail (with body) for each match.
    """
    if not user_message:
        return []

    msg_lower = user_message.lower()
    matched: list[SkillDetail] = []

    for skill in _skills:
        if not skill.trigger_keywords:
            continue
        if any(kw.lower() in msg_lower for kw in skill.trigger_keywords):
            body = _load_skill_body(skill.file_path)
            matched.append(
                SkillDetail(
                    name=skill.name,
                    description=skill.description,
                    trigger_keywords=skill.trigger_keywords,
                    file_path=skill.file_path,
                    content=body,
                )
            )

    return matched


def build_skills_context(skills: list[SkillDetail]) -> str:
    """Format activated skills into a context block for system injection."""
    if not skills:
        return ""

    parts = ["## Active Skills\n"]
    for s in skills:
        parts.append(f"### {s.name.replace('_', ' ').title()}\n")
        parts.append(s.content)
        parts.append("\n")

    return "\n".join(parts)


# ── REST endpoints ─────────────────────────────────────────────────────────────
@router.get("/skills")
def list_skills():
    """Return skill discovery information (name + description only)."""
    return [
        {
            "name": s.name,
            "description": s.description,
            "trigger_keywords": s.trigger_keywords,
        }
        for s in _skills
    ]


@router.post("/skills/reload")
def reload_skills():
    """Hot-reload skills from disk."""
    load_skills()
    return {"status": "ok", "count": len(_skills)}


@router.get("/skills/{skill_name}")
def get_skill(skill_name: str):
    """Return the full content of a specific skill."""
    for s in _skills:
        if s.name == skill_name:
            body = _load_skill_body(s.file_path)
            return {
                "name": s.name,
                "description": s.description,
                "trigger_keywords": s.trigger_keywords,
                "content": body,
            }
    return {"error": f"Skill '{skill_name}' not found"}, 404
