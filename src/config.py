from typing import List
import os
from dotenv import load_dotenv
import logging

class Config:
    def __init__(self):
        load_dotenv()
        
        # Set up logging configuration
        valid_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        if log_level not in valid_levels:
            print(f"Invalid LOG_LEVEL '{log_level}', defaulting to INFO")
            log_level = 'INFO'
        
        # Configure logging
        logging.basicConfig(
            level=valid_levels[log_level],
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info(f"Logging level set to {log_level}")
        
        # Discord settings
        self.bot_token: str = os.getenv('BOT_TOKEN', '')
        self.debug_channel_id: int = int(os.getenv('DEBUG_CHANNEL_ID', '0'))
        
        # Parse releases channel IDs
        self.releases_channel_ids: List[int] = [
            int(channel_id.strip()) 
            for channel_id in os.getenv('RELEASES_CHANNEL_IDS', '').split(',')
            if channel_id.strip()
        ]
        logging.debug(f"Loaded Discord settings - debug_channel_id: {self.debug_channel_id}, releases_channel_ids: {self.releases_channel_ids}")
        
        # CurseForge settings
        raw_key = os.getenv('CURSEFORGE_API_KEY', '')
        logging.debug(f"Raw Curseforge API Key from env: {raw_key}")
        self.curseforge_api_key: str = raw_key.replace("'", "").replace('"', '')
        self.mod_ids: List[int] = [
            int(mod_id.strip()) 
            for mod_id in os.getenv('MOD_IDS', '').split(',')
            if mod_id.strip()
        ]
        logging.debug(f"Loaded CurseForge settings - mod_ids: {self.mod_ids}")
        
        # Message templates
        self.message_tag: str = os.getenv('MESSAGE_TAG', '')
        self.message_header: str = os.getenv('MESSAGE_HEADER', '')
        self.message_footer: str = os.getenv('MESSAGE_FOOTER', '')
        logging.debug("Loaded message templates")
        
        # Feature flags
        self.announce_messages: bool = os.getenv('ANNOUNCE_MESSAGES', 'false').lower() == 'true'
        self.debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
        self.show_logo: bool = os.getenv('SHOW_LOGO', 'true').lower() == 'true'
        self.add_reactions: bool = os.getenv('ADD_REACTIONS', 'true').lower() == 'true'
        logging.debug(f"Loaded feature flags - announce_messages: {self.announce_messages}, debug: {self.debug}, show_logo: {self.show_logo}, add_reactions: {self.add_reactions}")
    
    def validate(self) -> List[str]:
        """Validate the configuration and return a list of error messages."""
        logging.debug("Validating configuration")
        errors = []
        
        if not self.bot_token:
            errors.append("BOT_TOKEN is required")
        if not self.debug_channel_id:
            errors.append("DEBUG_CHANNEL_ID is required")
        if not self.releases_channel_ids:
            errors.append("RELEASES_CHANNEL_IDS is required")
        if not self.curseforge_api_key:
            errors.append("CURSEFORGE_API_KEY is required")
        if not self.mod_ids:
            errors.append("At least one MOD_ID is required")

        logging.debug(f"Curseforge API Key: {self.curseforge_api_key}")
        
        # Warn if number of channels doesn't match mods
        if len(self.mod_ids) > len(self.releases_channel_ids):
            logging.warning(
                f"Fewer release channels ({len(self.releases_channel_ids)}) "
                f"than mods ({len(self.mod_ids)}). "
                "Extra mods will use the first channel."
            )
            
        if errors:
            logging.error(f"Configuration validation failed with errors: {errors}")
        else:
            logging.debug("Configuration validation successful")
        return errors

config = Config()
