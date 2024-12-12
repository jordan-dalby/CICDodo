from typing import List
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        # Discord settings
        self.bot_token: str = os.getenv('BOT_TOKEN', '')
        self.debug_channel_id: int = int(os.getenv('DEBUG_CHANNEL_ID', '0'))
        self.releases_channel_id: int = int(os.getenv('RELEASES_CHANNEL_ID', '0'))
        
        # CurseForge settings
        self.curseforge_api_key: str = os.getenv('CURSEFORGE_API_KEY', '')
        self.mod_ids: List[int] = [
            int(mod_id.strip()) 
            for mod_id in os.getenv('MOD_IDS', '').split(',')
            if mod_id.strip()
        ]
        
        # Message templates
        self.message_tag: str = os.getenv('MESSAGE_TAG', '')
        self.message_header: str = os.getenv('MESSAGE_HEADER', '')
        self.message_footer: str = os.getenv('MESSAGE_FOOTER', '')
        
        # Feature flags
        self.announce_messages: bool = os.getenv('ANNOUNCE_MESSAGES', 'false').lower() == 'true'
        self.debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    def validate(self) -> List[str]:
        """Validate the configuration and return a list of error messages."""
        errors = []
        
        if not self.bot_token:
            errors.append("BOT_TOKEN is required")
        if not self.debug_channel_id:
            errors.append("DEBUG_CHANNEL_ID is required")
        if not self.releases_channel_id:
            errors.append("RELEASES_CHANNEL_ID is required")
        if not self.curseforge_api_key:
            errors.append("CURSEFORGE_API_KEY is required")
        if not self.mod_ids:
            errors.append("At least one MOD_ID is required")
            
        return errors

config = Config()
