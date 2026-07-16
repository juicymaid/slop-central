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
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        
        db_data = {}
        for row in rows:
            key, val_str = row["key"], row["value"]
            if key.startswith("backend_"):
                continue
            try:
                db_data[key] = json.loads(val_str)
            except Exception:
                db_data[key] = val_str
        return AISettings.model_validate(db_data)
    except Exception as e:
        print(f"Error loading AI settings from DB: {e}")
        return AISettings()


def save_ai_settings(settings: AISettings):
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        data = settings.dict() if hasattr(settings, "dict") else settings.model_dump()
        for k, v in data.items():
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (k, json.dumps(v))
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving AI settings to DB: {e}")


@router.get("/ai-settings", response_model=AISettings)
def get_ai_settings():
    return load_ai_settings()


@router.put("/ai-settings", response_model=AISettings)
def update_ai_settings(settings: AISettings):
    save_ai_settings(settings)
    return settings


@router.patch("/ai-settings", response_model=AISettings)
def patch_ai_settings(settings: dict):
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        fields = AISettings.__fields__ if hasattr(AISettings, "__fields__") else AISettings.model_fields
        for k, v in settings.items():
            if k in fields:
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (k, json.dumps(v))
                )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error patching AI settings: {e}")
    return load_ai_settings()


@router.get("/backend-settings")
def get_backend_settings():
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", ("backend_active_id",))
        row = cursor.fetchone()
        active_id = json.loads(row["value"]) if row else "forge"
        
        configs = {}
        cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'backend_config_%'")
        rows = cursor.fetchall()
        conn.close()
        
        for r in rows:
            backend_id = r["key"].replace("backend_config_", "")
            configs[backend_id] = json.loads(r["value"])
            
        return {"activeId": active_id, "configs": configs}
    except Exception as e:
        print(f"Error loading backend settings: {e}")
        return {"activeId": "forge", "configs": {}}


@router.patch("/backend-settings")
def patch_backend_settings(payload: dict):
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if "activeId" in payload:
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("backend_active_id", json.dumps(payload["activeId"]))
            )
            
        if "configs" in payload and isinstance(payload["configs"], dict):
            for backend_id, config in payload["configs"].items():
                cursor.execute("SELECT value FROM settings WHERE key = ?", (f"backend_config_{backend_id}",))
                row = cursor.fetchone()
                existing_config = json.loads(row["value"]) if row else {}
                
                merged_config = {**existing_config, **config}
                
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (f"backend_config_{backend_id}", json.dumps(merged_config))
                )
                
        conn.commit()
        conn.close()
        return get_backend_settings()
    except Exception as e:
        print(f"Error patching backend settings: {e}")
        return {"error": str(e)}

@router.get("/settings/{key}")
def get_setting(key: str):
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row["value"])
        return None
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
        return None


@router.put("/settings/{key}")
def put_setting(key: str, payload: dict):
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(payload))
        )
        conn.commit()
        conn.close()
        return payload
    except Exception as e:
        print(f"Error saving setting {key}: {e}")
        return {"error": str(e)}


@router.patch("/settings/{key}")
def patch_setting(key: str, payload: dict):
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        existing = json.loads(row["value"]) if row else {}
        
        if isinstance(existing, dict) and isinstance(payload, dict):
            merged = {**existing, **payload}
        else:
            merged = payload
            
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(merged))
        )
        conn.commit()
        conn.close()
        return merged
    except Exception as e:
        print(f"Error patching setting {key}: {e}")
        return {"error": str(e)}
