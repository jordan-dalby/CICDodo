from typing import Optional
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
import logging

from src.config import config
from src.curseforge import CurseForgeAPI
from src.storage import ReleaseStorage

class ModUpdateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        logging.debug("Initializing ModUpdateCog")
        self.bot = bot
        self.cf_api = CurseForgeAPI(config.curseforge_api_key)
        self.storage = ReleaseStorage()
        self.check_updates.start()
        logging.debug("ModUpdateCog initialization complete")

    def cog_unload(self):
        logging.debug("Unloading ModUpdateCog")
        self.check_updates.cancel()

    def format_header(self, mod_name: str, version: str) -> str:
        """Format the header message with placeholders."""
        logging.debug(f"Formatting header for mod: {mod_name}, version: {version}")
        if config.message_header:
            header = config.message_header.format(
                mod_name=mod_name,
                version=version
            )
        else:
            header = f"@everyone {mod_name} version {version} is now available!"
        logging.debug(f"Formatted header: {header}")
        return header

    async def send_message(self, content: str, embed: Optional[discord.Embed] = None) -> None:
        channel_id = config.debug_channel_id if config.debug else config.releases_channel_id
        logging.debug(f"Sending message to channel ID: {channel_id}")
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            message = await channel.send(content=content, embed=embed)
            logging.debug("Message sent successfully")
            
            # Add reactions to the message
            reactions = ['👍', '❤️']
            for reaction in reactions:
                try:
                    await message.add_reaction(reaction)
                    logging.debug(f"Added reaction {reaction} to message")
                except discord.errors.Forbidden:
                    logging.error("Failed to add reaction - missing permissions")
                except discord.errors.HTTPException:
                    logging.error(f"Failed to add reaction {reaction}")
            
            if config.announce_messages and not config.debug:
                logging.debug("Attempting to publish message")
                try:
                    await message.publish()
                    logging.debug("Message published successfully")
                except discord.errors.Forbidden:
                    logging.error("Failed to publish message - missing permissions")
                except discord.errors.HTTPException:
                    logging.error("Failed to publish message - not in news channel")
        else:
            logging.error(f"Channel not found with ID: {channel_id}")

    @tasks.loop(minutes=5)
    async def check_updates(self):
        logging.debug("Starting update check loop")
        for mod_id in config.mod_ids:
            logging.debug(f"Checking updates for mod ID: {mod_id}")
            try:
                latest_file = await self.cf_api.get_latest_file(mod_id)
                if not latest_file:
                    logging.warning(f"No latest file found for mod ID: {mod_id}")
                    continue

                mod_info = await self.cf_api.get_mod_info(mod_id)
                version = latest_file['version']
                logging.debug(f"Found version {version} for mod {mod_info['name']}")
                
                if not self.storage.is_version_released(str(mod_id), version):
                    logging.info(f"New version {version} found for mod {mod_info['name']}")
                    header = self.format_header(mod_info['name'], version)
                    embed = discord.Embed(
                        title=mod_info['name'],
                        description=header,
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    if config.show_logo and 'logo' in mod_info and mod_info['logo'] and 'url' in mod_info['logo']:
                        logging.debug("Adding mod logo to embed")
                        embed.set_thumbnail(url=mod_info['logo']['url'])
                    
                    if changelog := latest_file.get('changelog'):
                        logging.debug("Adding changelog to embed")
                        embed.add_field(
                            name="Changelog",
                            value=changelog,
                            inline=False
                        )
                    
                    if config.message_footer:
                        logging.debug("Adding footer to embed")
                        footer_text = config.message_footer.format(
                            mod_name=mod_info['name'],
                            version=version
                        )
                        embed.add_field(
                            name=footer_text,
                            value="",
                            inline=False
                        )
                    
                    await self.send_message(
                        content=config.message_tag,
                        embed=embed
                    )
                    
                    self.storage.mark_version_released(str(mod_id), version)
                    logging.info(f"Successfully processed and announced version {version} for mod {mod_info['name']}")
                else:
                    logging.debug(f"Version {version} of mod {mod_info['name']} already released")
            
            except Exception as e:
                logging.error(f"Error checking mod {mod_id}: {str(e)}", exc_info=True)
                continue
            
            await asyncio.sleep(2)
        logging.debug("Completed update check loop")

    @check_updates.before_loop
    async def before_check_updates(self):
        logging.debug("Waiting for bot to be ready before starting update checks")
        await self.bot.wait_until_ready()
        logging.debug("Bot ready, update checks can now begin")

    @commands.command()
    @commands.is_owner()
    async def force_check(self, ctx):
        logging.info("Force check command received")
        await ctx.send("Forcing update check...")
        await self.check_updates()
        logging.info("Force check completed")
        await ctx.send("Update check completed.")

async def setup(bot: commands.Bot):
    logging.debug("Setting up ModUpdateCog")
    await bot.add_cog(ModUpdateCog(bot))
    logging.debug("ModUpdateCog setup complete")
