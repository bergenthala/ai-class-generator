"""AI-powered story generation service"""
import os
import httpx
from typing import Optional, Dict, Any
import json


# Hugging Face Inference API endpoint (free tier)
HF_API_BASE = "https://api-inference.huggingface.co/models"
# Using a fast, free model - can be changed to any Hugging Face model
# Using smaller, faster models that work well on free tier
DEFAULT_MODEL = "gpt2"  # Fast and reliable
# Alternative model if primary fails
FALLBACK_MODEL = "distilgpt2"


def get_hf_token() -> Optional[str]:
    """Get Hugging Face API token from environment"""
    return os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")


async def generate_story_text(
    context: str,
    player_class: str,
    action: Optional[str] = None,
    player_stats: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate story text using AI.
    
    Args:
        context: Current story context
        player_class: Player's chosen class
        action: Action the player just took (optional)
        player_stats: Player statistics (optional)
        
    Returns:
        Generated story text
    """
    # Check if we have an API token
    hf_token = get_hf_token()
    
    if not hf_token:
        # Fallback to hardcoded text if no API key
        return get_fallback_text(player_class, action)
    
    try:
        # Build prompt
        prompt = build_story_prompt(context, player_class, action, player_stats)
        
        # Call Hugging Face API
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {hf_token}"}
            
            # Try primary model first
            try:
                response = await client.post(
                    f"{HF_API_BASE}/{DEFAULT_MODEL}",
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 150,
                            "temperature": 0.8,
                            "top_p": 0.9,
                            "return_full_text": False
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                        # Clean up the text
                        return clean_generated_text(generated_text)
            except Exception:
                pass
            
            # Fallback to simpler model if primary fails
            try:
                response = await client.post(
                    f"{HF_API_BASE}/{FALLBACK_MODEL}",
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 100,
                            "temperature": 0.8,
                            "return_full_text": False
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                        return clean_generated_text(generated_text)
            except Exception:
                pass
                
    except Exception as e:
        print(f"Error generating story with AI: {e}")
    
    # Fallback to hardcoded text
    return get_fallback_text(player_class, action)


def build_story_prompt(
    context: str,
    player_class: str,
    action: Optional[str],
    player_stats: Optional[Dict[str, Any]]
) -> str:
    """Build a prompt for story generation"""
    class_descriptions = {
        "warrior": "a brave warrior skilled in combat and strength",
        "priest": "a holy priest dedicated to light, healing, and divine magic",
        "mage": "a powerful mage who wields arcane magic and studies ancient tomes",
        "thief": "a cunning thief who moves in shadows and excels at stealth",
        "wanderer": "a free-spirited wanderer with no class restrictions, forging their own path"
    }
    
    # Build a more narrative prompt
    if action:
        action_stories = {
            "read_book": f"As {class_descriptions.get(player_class, 'an adventurer')}, you open an ancient tome. The pages glow with arcane knowledge as you absorb its secrets. Describe what happens next in the story.",
            "kill_monster": f"As {class_descriptions.get(player_class, 'an adventurer')}, you stand victorious over a fallen foe. The battle was fierce, but your skills prevailed. Continue the narrative.",
            "craft_item": f"As {class_descriptions.get(player_class, 'an adventurer')}, you finish crafting a new item. The materials come together perfectly under your skilled hands. What happens next?",
            "explore": f"As {class_descriptions.get(player_class, 'an adventurer')}, you venture into uncharted territory. New paths and hidden secrets reveal themselves. Describe the discovery.",
            "meditate": f"As {class_descriptions.get(player_class, 'an adventurer')}, you find inner peace through meditation. The world fades away as you focus your mind. What insights do you gain?"
        }
        prompt = action_stories.get(action, f"As {class_descriptions.get(player_class, 'an adventurer')}, you continue your journey. Write a brief, immersive story continuation (2-3 sentences).")
    else:
        # Starting story
        prompt = f"""Write an engaging opening scene for a fantasy game. The player is {class_descriptions.get(player_class, 'an adventurer')} beginning their journey. 

Create a vivid, immersive 2-3 sentence introduction that sets the scene and invites the player into the world. Use descriptive language and create atmosphere."""
    
    return prompt


def clean_generated_text(text: str) -> str:
    """Clean and format generated text"""
    # Remove extra whitespace
    text = " ".join(text.split())
    # Remove quotes if the entire text is quoted
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    # Ensure it ends with punctuation
    if text and text[-1] not in ".!?":
        text += "."
    return text


def get_fallback_text(player_class: str, action: Optional[str] = None) -> str:
    """Fallback hardcoded text when AI is not available"""
    if action:
        action_texts = {
            "read_book": "The knowledge flows into your mind. You feel wiser and more enlightened.",
            "kill_monster": "The battle is won! Your combat prowess grows with each victory.",
            "craft_item": "Your creation is complete! A fine piece of work that showcases your skill.",
            "explore": "You discover new paths and hidden secrets in the world around you.",
            "meditate": "You feel more centered and focused after your meditation."
        }
        return action_texts.get(action, "You continue your journey...")
    
    # Class-specific starting text
    class_texts = {
        "warrior": "You stand at the gates of the training grounds, your sword gleaming in the sunlight. The master trainer approaches: 'Prove your worth, warrior. Your journey begins with combat.'",
        "priest": "You enter the sacred temple, the light of the divine surrounding you. The high priest greets you: 'Welcome, child of light. Knowledge and wisdom await.'",
        "mage": "You step into the arcane library, ancient tomes floating around you. The archmage appears: 'Magic flows through knowledge, young apprentice. Study well.'",
        "thief": "You slip into the shadows of the city, unnoticed by all. A voice whispers: 'Stealth and cunning are your tools. Use them wisely.'",
        "wanderer": "You walk an untrodden path, free from the constraints of tradition. A mysterious figure appears: 'You walk alone, but that is your strength. Forge your own destiny.'"
    }
    return class_texts.get(player_class, "Your adventure begins...")

