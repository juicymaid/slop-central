import os
import json
import sqlite3
import shutil

DB_FILE = "pinthesis.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Images table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        prompt TEXT,
        tagger_prompt TEXT,
        description TEXT,
        width INTEGER,
        height INTEGER,
        file_size INTEGER,
        model_hash TEXT,
        negative_prompt TEXT,
        sampler TEXT,
        clicks INTEGER DEFAULT 0,
        shows INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        dislikes INTEGER DEFAULT 0,
        rating REAL DEFAULT 0.0,
        phash TEXT,
        last_viewed REAL,
        last_shown REAL,
        metadata TEXT
    )
    """)

    # Alter table to add columns to existing installations
    try:
        cursor.execute("ALTER TABLE images ADD COLUMN last_viewed REAL")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE images ADD COLUMN last_shown REAL")
    except sqlite3.OperationalError:
        pass
    
    # Boards table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS boards (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        images TEXT
    )
    """)
    
    # Trash table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trash (
        image_id INTEGER PRIMARY KEY,
        trashed_at REAL
    )
    """)
    
    # Embeddings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        image_id INTEGER PRIMARY KEY,
        vector TEXT,
        norm REAL
    )
    """)
    
    # TrueSkill Ratings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trueskill_ratings (
        image_id INTEGER PRIMARY KEY,
        mu REAL,
        sigma REAL
    )
    """)
    
    # Comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        image_id INTEGER PRIMARY KEY,
        comments TEXT
    )
    """)
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        data TEXT
    )
    """)
    
    # Descriptions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS descriptions (
        image_id INTEGER PRIMARY KEY,
        description TEXT,
        op_user TEXT
    )
    """)
    
    # Chats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        messages TEXT
    )
    """)
    
    # Assistant chats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assistant_chats (
        session_id TEXT PRIMARY KEY,
        messages TEXT
    )
    """)
    
    # Comics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        data TEXT
    )
    """)
    
    # Stories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY,
        data TEXT
    )
    """)
    
    # Hentai status table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hentai_status (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def migrate_json_to_sqlite():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Migrate Trash
    if os.path.exists("trash.json"):
        print("Migrating trash.json...")
        with open("trash.json", "r", encoding="utf-8") as f:
            trash_data = json.load(f)
        for k, v in trash_data.items():
            cursor.execute(
                "INSERT OR REPLACE INTO trash (image_id, trashed_at) VALUES (?, ?)",
                (int(k), v.get("TrashedAt", v.get("trashed_at", 0)) if isinstance(v, dict) else v)
            )
        conn.commit()
        shutil.move("trash.json", "trash.json.bak")
        
    # 2. Migrate Images (includes likes, clicks, shows, phashes if JSONs exist, otherwise fallback)
    if os.path.exists("images.json"):
        print("Migrating images.json...")
        with open("images.json", "r", encoding="utf-8") as f:
            images = json.load(f)
            
        # Pre-load secondary image stats to merge them into the images table
        likes_data = {}
        if os.path.exists("likes.json"):
            with open("likes.json", "r", encoding="utf-8") as lf:
                likes_data = json.load(lf)
        clicks_data = {}
        if os.path.exists("clicks.json"):
            with open("clicks.json", "r", encoding="utf-8") as cf:
                clicks_data = json.load(cf)
        shows_data = {}
        if os.path.exists("shows.json"):
            with open("shows.json", "r", encoding="utf-8") as sf:
                shows_data = json.load(sf)
        hashes_data = {}
        if os.path.exists("hashes.json"):
            with open("hashes.json", "r", encoding="utf-8") as hf:
                hashes_data = json.load(hf)
                
        for img in images:
            img_id = img.get("Id")
            if img_id is None:
                continue
            
            # Merge stats
            likes = likes_data.get(str(img_id), {})
            img_likes = likes.get("Likes", img.get("Likes", 0))
            img_dislikes = likes.get("Dislikes", img.get("Dislikes", 0))
            img_rating = likes.get("Rating", img.get("Rating", 0.0))
            img_clicks = clicks_data.get(str(img_id), img.get("Clicks", 0))
            img_shows = shows_data.get(str(img_id), img.get("Shows", 0))
            img_phash = hashes_data.get(str(img_id), img.get("pHash"))
            
            # Columns to extract
            path = img.get("Path")
            prompt = str(img.get("Prompt") or "")
            tagger_prompt = str(img.get("taggerPrompt") or "")
            description = str(img.get("description") or "")
            width = img.get("Width")
            height = img.get("Height")
            file_size = img.get("FileSize")
            model_hash = str(img.get("ModelHash")) if img.get("ModelHash") is not None else None
            negative_prompt = str(img.get("NegativePrompt")) if img.get("NegativePrompt") is not None else None
            sampler = str(img.get("Sampler")) if img.get("Sampler") is not None else None
            img_phash = str(img_phash) if img_phash is not None else None
            
            # Clean runtime metadata
            _runtime_fields = {"tags_set", "pHash", "Likes", "Dislikes", "Rating", "Clicks", "Shows", "Id", "Path", "Prompt", "taggerPrompt", "description", "Width", "Height", "FileSize", "ModelHash", "NegativePrompt", "Sampler"}
            clean_metadata = {k: v for k, v in img.items() if k not in _runtime_fields and not k.startswith("_")}
            metadata_str = json.dumps(clean_metadata)
            
            cursor.execute("""
            INSERT OR REPLACE INTO images (
                id, path, prompt, tagger_prompt, description, width, height, file_size, 
                model_hash, negative_prompt, sampler, clicks, shows, likes, dislikes, 
                rating, phash, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                img_id, path, prompt, tagger_prompt, description, width, height, file_size,
                model_hash, negative_prompt, sampler, img_clicks, img_shows, img_likes, img_dislikes,
                img_rating, img_phash, metadata_str
            ))
            
        conn.commit()
        shutil.move("images.json", "images.json.bak")
        for fn in ["likes.json", "clicks.json", "shows.json", "hashes.json"]:
            if os.path.exists(fn):
                shutil.move(fn, f"{fn}.bak")
                
    # 3. Migrate Boards
    if os.path.exists("boards.json"):
        print("Migrating boards.json...")
        with open("boards.json", "r", encoding="utf-8") as f:
            boards_data = json.load(f)
        for k, v in boards_data.items():
            board_id = int(k)
            name = v.get("name")
            images_list = v.get("images", [])
            cursor.execute(
                "INSERT OR REPLACE INTO boards (id, name, images) VALUES (?, ?, ?)",
                (board_id, name, json.dumps(images_list))
            )
        conn.commit()
        shutil.move("boards.json", "boards.json.bak")
        
    # 4. Migrate Embeddings
    if os.path.exists("embeddings.json"):
        print("Migrating embeddings.json...")
        with open("embeddings.json", "r", encoding="utf-8") as f:
            emb_data = json.load(f)
        for k, v in emb_data.items():
            cursor.execute(
                "INSERT OR REPLACE INTO embeddings (image_id, vector, norm) VALUES (?, ?, ?)",
                (int(k), json.dumps(v["vec"]), v.get("norm", 1.0))
            )
        conn.commit()
        shutil.move("embeddings.json", "embeddings.json.bak")
        
    # 5. Migrate Ratings
    if os.path.exists("ratings.json"):
        print("Migrating ratings.json...")
        with open("ratings.json", "r", encoding="utf-8") as f:
            ratings = json.load(f)
        for k, v in ratings.items():
            cursor.execute(
                "INSERT OR REPLACE INTO trueskill_ratings (image_id, mu, sigma) VALUES (?, ?, ?)",
                (int(k), v.get("mu"), v.get("sigma"))
            )
        conn.commit()
        shutil.move("ratings.json", "ratings.json.bak")
        
    # 6. Migrate Comments
    if os.path.exists("comments.json"):
        print("Migrating comments.json...")
        with open("comments.json", "r", encoding="utf-8") as f:
            comments = json.load(f)
        for k, v in comments.items():
            cursor.execute(
                "INSERT OR REPLACE INTO comments (image_id, comments) VALUES (?, ?)",
                (int(k), json.dumps(v))
            )
        conn.commit()
        shutil.move("comments.json", "comments.json.bak")
        
    # 7. Migrate Users
    if os.path.exists("users.json"):
        print("Migrating users.json...")
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
        for k, v in users.items():
            cursor.execute(
                "INSERT OR REPLACE INTO users (username, data) VALUES (?, ?)",
                (k, json.dumps(v))
            )
        conn.commit()
        shutil.move("users.json", "users.json.bak")
        
    # 8. Migrate Descriptions
    if os.path.exists("descriptions.json"):
        print("Migrating descriptions.json...")
        with open("descriptions.json", "r", encoding="utf-8") as f:
            descriptions = json.load(f)
        for k, v in descriptions.items():
            cursor.execute(
                "INSERT OR REPLACE INTO descriptions (image_id, description, op_user) VALUES (?, ?, ?)",
                (int(k), v.get("description", v) if isinstance(v, dict) else v, v.get("op_user") if isinstance(v, dict) else None)
            )
        conn.commit()
        shutil.move("descriptions.json", "descriptions.json.bak")
        
    # 9. Migrate Chats
    if os.path.exists("chats.json"):
        print("Migrating chats.json...")
        with open("chats.json", "r", encoding="utf-8") as f:
            chats = json.load(f)
        for k, v in chats.items():
            cursor.execute(
                "INSERT OR REPLACE INTO chats (chat_id, messages) VALUES (?, ?)",
                (k, json.dumps(v.get("messages", v) if isinstance(v, dict) else v))
            )
        conn.commit()
        shutil.move("chats.json", "chats.json.bak")
        
    # 10. Migrate Assistant Chats
    if os.path.exists("assistant_chats.json"):
        print("Migrating assistant_chats.json...")
        with open("assistant_chats.json", "r", encoding="utf-8") as f:
            achats = json.load(f)
        for k, v in achats.items():
            cursor.execute(
                "INSERT OR REPLACE INTO assistant_chats (session_id, messages) VALUES (?, ?)",
                (k, json.dumps(v))
            )
        conn.commit()
        shutil.move("assistant_chats.json", "assistant_chats.json.bak")
        
    # 11. Migrate Comics
    if os.path.exists("comics.json"):
        print("Migrating comics.json...")
        with open("comics.json", "r", encoding="utf-8") as f:
            comics = json.load(f)
        for item in comics:
            title = item.get("title", "")
            cursor.execute(
                "INSERT INTO comics (title, data) VALUES (?, ?)",
                (title, json.dumps(item))
            )
        conn.commit()
        shutil.move("comics.json", "comics.json.bak")
        
    # 12. Migrate Stories
    if os.path.exists("stories.json"):
        print("Migrating stories.json...")
        with open("stories.json", "r", encoding="utf-8") as f:
            stories = json.load(f)
        for k, v in stories.items():
            cursor.execute(
                "INSERT OR REPLACE INTO stories (id, data) VALUES (?, ?)",
                (int(k), json.dumps(v))
            )
        conn.commit()
        shutil.move("stories.json", "stories.json.bak")
        
    # 13. Migrate Hentai Status
    if os.path.exists("hentai_status.json"):
        print("Migrating hentai_status.json...")
        with open("hentai_status.json", "r", encoding="utf-8") as f:
            hstatus = json.load(f)
        for k, v in hstatus.items():
            cursor.execute(
                "INSERT OR REPLACE INTO hentai_status (key, value) VALUES (?, ?)",
                (k, json.dumps(v))
            )
        conn.commit()
        shutil.move("hentai_status.json", "hentai_status.json.bak")
        
    # 14. Migrate AI Settings
    ai_settings_file = "storage/ai_settings.json"
    if os.path.exists(ai_settings_file):
        print("Migrating ai_settings.json...")
        try:
            with open(ai_settings_file, "r", encoding="utf-8") as f:
                ai_data = json.load(f)
            for k, v in ai_data.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (k, json.dumps(v))
                )
            conn.commit()
            shutil.move(ai_settings_file, ai_settings_file + ".bak")
        except Exception as e:
            print(f"Error migrating ai_settings: {e}")

    # 15. Migrate Backend Settings
    backend_settings_file = "storage/backendSettings.json"
    if os.path.exists(backend_settings_file):
        print("Migrating backendSettings.json...")
        try:
            with open(backend_settings_file, "r", encoding="utf-8") as f:
                b_data = json.load(f)
            if "activeId" in b_data:
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("backend_active_id", json.dumps(b_data["activeId"]))
                )
            if "configs" in b_data and isinstance(b_data["configs"], dict):
                for backend_id, config in b_data["configs"].items():
                    cursor.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        (f"backend_config_{backend_id}", json.dumps(config))
                    )
            conn.commit()
            shutil.move(backend_settings_file, backend_settings_file + ".bak")
        except Exception as e:
            print(f"Error migrating backendSettings: {e}")
        
    # 16. Migrate Default Styles
    default_styles_file = "storage/defaultStyles.json"
    if os.path.exists(default_styles_file):
        print("Migrating defaultStyles.json...")
        try:
            with open(default_styles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("default_styles", json.dumps(data))
            )
            conn.commit()
            shutil.move(default_styles_file, default_styles_file + ".bak")
        except Exception as e:
            print(f"Error migrating defaultStyles: {e}")

    # 17. Migrate Current Request
    current_request_file = "storage/currentRequest.json"
    if os.path.exists(current_request_file):
        print("Migrating currentRequest.json...")
        try:
            with open(current_request_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("current_request", json.dumps(data))
            )
            conn.commit()
            shutil.move(current_request_file, current_request_file + ".bak")
        except Exception as e:
            print(f"Error migrating currentRequest: {e}")

    # 18. Migrate Current Model
    current_model_file = "storage/currentModel.json"
    if os.path.exists(current_model_file):
        print("Migrating currentModel.json...")
        try:
            with open(current_model_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("current_model", json.dumps(data))
            )
            conn.commit()
            shutil.move(current_model_file, current_model_file + ".bak")
        except Exception as e:
            print(f"Error migrating currentModel: {e}")
        
    conn.close()
    print("Migration to SQLite completed successfully.")

if __name__ == "__main__":
    migrate_json_to_sqlite()
