from typing import Dict, List, Optional, Any
import aiohttp
import asyncio
from datetime import datetime
import logging
from markdownify import markdownify as md
import re

class CurseForgeAPI:
    BASE_URL = "https://api.curseforge.com/v1"
    GAME_ID_ARK_SA = 828326  # Game ID for ARK: Survival Ascended

    def __init__(self, api_key: str):
        logging.debug("Initializing CurseForgeAPI with api_key.")
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "x-api-key": self.api_key
        }
        # Rate limiting
        self.request_delay = 1.0  # Delay between requests in seconds
        self.last_request_time = 0.0

    def extract_version(self, filename: str) -> str:
        """Extract version number from filename."""
        match = re.search(r'windowsserver\s+(\d+)\.zip', filename.lower())
        if match:
            return match.group(1)
        return filename

    async def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a rate-limited request to the CurseForge API."""
        logging.debug(f"Making request to endpoint: {endpoint}")
        # Implement rate limiting
        current_time = datetime.now().timestamp()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            logging.debug(f"Rate limiting in effect. Sleeping for {sleep_time} seconds.")
            await asyncio.sleep(sleep_time)

        url = f"{self.BASE_URL}{endpoint}"
        logging.debug(f"Request URL: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                self.last_request_time = datetime.now().timestamp()
                logging.debug(f"Received response with status code: {response.status}")

                if response.status == 429:  # Too Many Requests
                    retry_after = float(response.headers.get('Retry-After', '5'))
                    logging.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint)

                response.raise_for_status()
                json_response = await response.json()
                logging.debug(f"Response JSON: {json_response}")
                return json_response

    async def get_mod_info(self, mod_id: int) -> Dict[str, Any]:
        """Get information about a specific mod."""
        logging.debug(f"Fetching mod info for mod_id: {mod_id}")
        response = await self._make_request(f"/mods/{mod_id}")
        mod_info = response['data']
        logging.debug(f"Mod info: {mod_info}")
        return mod_info

    async def get_mod_files(self, mod_id: int) -> List[Dict[str, Any]]:
        """Get all files for a specific mod."""
        logging.debug(f"Fetching mod files for mod_id: {mod_id}")
        response = await self._make_request(
            f"/mods/{mod_id}/files"
            f"?gameId={self.GAME_ID_ARK_SA}"
            "&orderBy=dateCreated&sortOrder=desc"
        )
        mod_files = response['data']
        logging.debug(f"Mod files: {mod_files}")
        return mod_files
    
    async def get_file_changelog(self, mod_id: int, file_id: int) -> str:
        """Get the changelog for a specific file."""
        logging.debug(f"Fetching changelog for mod_id: {mod_id}, file_id: {file_id}")
        response = await self._make_request(f"/mods/{mod_id}/files/{file_id}/changelog")
        logging.debug(f"Response: {response}")
        changelog = response['data']
        logging.debug(f"Changelog: {changelog}")
        return self.format_changelog(changelog)

    async def get_latest_file(self, mod_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest file for a specific mod."""
        logging.debug(f"Getting the latest file for mod_id: {mod_id}")
        files = await self.get_mod_files(mod_id)
        if not files:
            logging.warning(f"No files found for mod_id: {mod_id}")
            return None

        latest_file = files[0]
        logging.debug(f"Latest file info: {latest_file}")
        latest_file['version'] = self.extract_version(latest_file['displayName'])
        changelog = await self.get_file_changelog(mod_id, latest_file['id'])
        latest_file['changelog'] = changelog
        logging.debug(f"Latest file with changelog and version: {latest_file}")
        return latest_file

    def format_changelog(self, changelog: str) -> str:
        """Format the changelog using markdownify for reliable HTML to Markdown conversion."""
        if isinstance(changelog, dict):
            changelog = changelog.get('data', '')
            
        markdown = md(changelog, 
                     heading_style="atx",
                     bullets="-",
                     strip=['script', 'style'],
                     code_language="python",
                     escape_asterisks=False)
        
        changelog = markdown.replace(u'\xa0', u' ')

        logging.debug(f"Formatted changelog: {changelog}")
        return changelog
