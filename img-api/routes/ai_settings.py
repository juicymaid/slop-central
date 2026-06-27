"""
Global AI generation settings.
Stored in storage/ai_settings.json and used by comments, posts, assistant, and chats routes.
"""
import json
import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

SETTINGS_FILE = "storage/ai_settings.json"


class AISettings(BaseModel):
    default_model: str = "hf.co/DavidAU/gemma-4-E4B-it-The-DECKARD-Expresso-Universe-HERETIC-UNCENSORED-Thinking-GGUF:Q8_0"
    default_vision_model: str = "huihui_ai/qwen3.5-abliterated:2B"
    default_assistant_model: str = "hf.co/DavidAU/gemma-4-E4B-it-The-DECKARD-Expresso-Universe-HERETIC-UNCENSORED-Thinking-GGUF:Q8_0"
    model_is_vision: bool = False
    use_thinking: bool = False
    # manage_vram: True = automatically unload SD/LM models when switching tasks.
    # False = do not touch VRAM (e.g. when using a remote inference endpoint).
    # NOTE: replaces the old `use_laptop` field (inverted meaning).
    manage_vram: bool = False
    override_temperature: bool = False
    temperature: float = 0.7
    autocomplete_enabled: bool = False
    autocomplete_model: str = ""

    # ── backwards-compat: accept old `use_laptop` from saved JSON ───────────
    @classmethod
    def model_validate(cls, obj, **kwargs):
        if isinstance(obj, dict) and "use_laptop" in obj and "manage_vram" not in obj:
            # Old setting: use_laptop=True meant "laptop mode, don't manage VRAM"
            obj = dict(obj)
            obj["manage_vram"] = not obj.pop("use_laptop")
        return super().model_validate(obj, **kwargs)


def load_ai_settings() -> AISettings:
    if not os.path.exists(SETTINGS_FILE):
        return AISettings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return AISettings.model_validate(data)
    except Exception:
        return AISettings()


def save_ai_settings(settings: AISettings):
    os.makedirs("storage", exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            settings.dict() if hasattr(settings, "dict") else settings.model_dump(),
            f,
            indent=4,
        )


@router.get("/ai-settings", response_model=AISettings)
def get_ai_settings():
    return load_ai_settings()


@router.put("/ai-settings", response_model=AISettings)
def update_ai_settings(settings: AISettings):
    save_ai_settings(settings)
    return settings
