import json
import os
from fastapi import APIRouter, Query, Body
import random

from ollama import ChatResponse
from ollama import chat

import utils  
from routes import comments
from routes.ai_settings import load_ai_settings

router = APIRouter()

all_chats = {}

@router.get("/chat/{chat_id}")
def get_chat(chat_id: str):

    load_chats()  # Ensure chats are loaded before accessing

    chat = all_chats.get(chat_id, {})
    if chat:
        return chat
    
    # Try to load as a character first
    from routes.posts import load_characters
    characters = load_characters()
    char = None
    for c in characters:
        if c.id == chat_id:
            char = c
            break

    if char:
        # Character-based chat
        chat = {
            "chat_id": chat_id,
            "messages": [],
            "character": {
                "character_name": char.name,
                "short_description": char.description[:200] if char.description else "",
                "avatar": char.avatar,
                "character_id": char.id,
            },
            "is_character_chat": True,
        }
        all_chats[chat_id] = chat
        save_chats()
        return chat
    
    # Fallback: Legacy image-based chat
    chat = {
        "chat_id": chat_id,
        "messages": [],
    }

    image = utils.images_data.get(int(chat_id))  # Ensure the image exists
    if not image:
        return {"error": "Image not found"}
    
    description = image.get("description", "")
    if not description:
        print(f"Warning: No description found for image ID {image.get('Id')}. Generating a new one.")
        description = comments.get_image_description(image.get("Id"))

    character = comments.get_character_description(
        image.get("Path").replace("/files", utils.api_file_root),
        image.get("Prompt", "[No tags]"),
        description
    )

    chat["original_image_description"] = description
    chat["image_prompt"] = image.get("Prompt", "[No tags]")
    chat["character"] = character

    all_chats[chat_id] = chat

    save_chats()


    return chat

@router.post("/chat/{chat_id}/message")
def add_message(chat_id: str, message: str, image_request: object = Body(...)):
    if chat_id not in all_chats:
        raise ValueError(f"Chat with ID {chat_id} does not exist.")
    
    _chat = all_chats[chat_id]
    _chat["messages"].append({
        "isUser": True,
        "text": message,
        "timestamp": utils.get_current_timestamp()
    })

    character = _chat.get("character", {})
    is_character_chat = _chat.get("is_character_chat", False)

    settings = load_ai_settings()

    if is_character_chat:
        # Character-based chat uses character description directly
        from routes.posts import load_characters
        characters = load_characters()
        char = None
        for c in characters:
            if c.id == chat_id:
                char = c
                break

        char_name = character.get("character_name", "Character")
        char_desc = char.description if char else character.get("short_description", "")

        system_content = (
            comments.ollama_jailbreak
            + f"You are now fully roleplaying as {char_name}. {char_desc}."
            " Stay in character at all times, respond naturally and immersively as if you are truly this character."
            " Do not write thoughts or actions in brackets, only write dialogue."
            " Do not break character or refer to yourself as an AI."
            " You can also send images in the chat by including an 'image_prompt' field in your response."
            " If user says [something in brackets], you should include that in your image_prompt field."
            " If you don't want to send an image, just leave the 'image_prompt' field empty or null."
            " The image_prompt should be a list of tags separated by commas, describing the image you want to generate."
        )
    else:
        # Legacy image-based chat
        prompt = comments.clean_prompt(_chat.get('image_prompt', ''))
        char_name = character.get('character_name', 'Character')
        system_content = (
            comments.ollama_jailbreak
            + f"You are now fully roleplaying as {char_name}, {character.get('short_description', '')}."
            f" Your personality traits: {character.get('personality_traits', '')}."
            f" You enjoy: {character.get('likes', '')}."
            f" Your fetishes: {character.get('fetishes', '')}."
            f" You dislike: {character.get('dislikes', '')}."
            f" Your current mood: {character.get('current_mood', '')}."
            f" You are currently {character.get('current_activity', '')} in the image."
            f" You have just posted an image of yourself online and are now chatting with a user who is responding to your post."
            f" The image you posted is described as: {_chat.get('original_image_description', '')}."
            " Stay in character at all times, respond naturally and immersively as if you are truly this character."
            " Do not write thoughts or actions in brackets, only write dialogue."
            " Do not break character or refer to yourself as an AI."
            " You can also send images in the chat by including an 'image_prompt' field in your response."
            " If user says [something in brackets], you should include that in your image_prompt field."
            "If you don't want to send an image, just leave the 'image_prompt' field empty or null. Note generating images may take a while so don't generate them if not needed."
            "The image_prompt should be a list of tags seperated by commas, describing the image you want to generate."
            f"for example the prompt of the image you posted is: {prompt}"
        )

    _messages = [
        {
            "role": "system",
            "content": system_content,
        }
    ]
    
    for msg in _chat["messages"]:
        if "text" in msg and msg["text"] is not None:
            content = msg["text"]
            if msg.get("image_prompt"):
                content += f"\n[{char_name} Sends an image with prompt: {msg['image_prompt']}]"
                
            _messages.append({
                "role": "user" if msg.get("isUser", False) else "assistant",
                "content": content
            })

    options = {}
    if settings.override_temperature:
        options["temperature"] = settings.temperature

    _client = comments.laptopClient if settings.use_laptop else comments.OllamaClient
    response: ChatResponse = _client.chat(
        model=settings.default_model,
        messages=_messages,
        format={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "image_prompt": {"type": "string"},
            },
            "required": ["text", "image_prompt"],
        },
        options=options
    )

    input_tokens = getattr(response, "prompt_eval_count", 0)
    output_tokens = getattr(response, "eval_count", 0)
    eval_duration_ns = getattr(response, "eval_duration", 0)
    tokens_per_sec = output_tokens / (eval_duration_ns / 1e9) if eval_duration_ns else 0
    print(f"Usage stats: {input_tokens} input tokens | {output_tokens} output tokens | {tokens_per_sec:.2f} tokens/s")

    data = json.loads(response["message"]["content"])


    if "text" not in data:
        raise ValueError("Response does not contain 'text' field.")
    
    #save the response message

    _chat["messages"].append({
        "isUser": False,
        "text": data["text"],
        "image_prompt": data.get("image_prompt", ""),
        "timestamp": utils.get_current_timestamp(),
    })

    print(f"Chat {chat_id} updated with new message: {data['text']}")


    save_chats()
    load_chats()
    return {"status": "Message added successfully", "chat_id": chat_id, "message": data["text"], "image_prompt": data.get("image_prompt", "")}

# get the latest image file in /files and add the url to the chat message
@router.post("/chat/{chat_id}/{message_index}/image")
def add_image_to_message(chat_id: str, message_index: int):
    # Validate chat and message index
    if chat_id not in all_chats:
        return {"error": f"Chat with ID {chat_id} does not exist."}
    messages = all_chats[chat_id].get("messages", [])
    if not (0 <= message_index < len(messages)):
        return {"error": f"Message index {message_index} out of range."}

    # Find the latest image file in /files (recursive)
    files_root = os.path.join(utils.api_file_root, "automatic", "txt2img-images")
    latest_file = None
    latest_mtime = 0
    for root, _, files in os.walk(files_root):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                file_path = os.path.join(root, file)
                mtime = os.path.getmtime(file_path)
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_file = file_path

    if not latest_file:
        return {"error": "No image files found."}

    # Build the URL
    rel_path = os.path.relpath(latest_file, utils.api_file_root).replace("\\", "/")
    image_url = f"http://127.0.0.1:8000/files/{rel_path}"

    # Add image to the message
    messages[message_index]["image"] = image_url

    save_chats()
    return {
        "status": "Image added to message",
        "chat_id": chat_id,
        "message_index": message_index,
        "image": image_url,
    }



@router.get("/chats")
def get_all_chats():
    load_chats()
    return list(all_chats.values())


def save_chats():
    if not all_chats:
        raise ValueError("No chats to save.")
    
    with open("chats.json", "w", encoding="utf-8") as f:
        json.dump(all_chats, f, indent=2)

def load_chats():
    global all_chats
    if not os.path.exists("chats.json"):
        return  # No chats to load

    with open("chats.json", "r", encoding="utf-8") as f:
        all_chats = json.load(f)


load_chats()