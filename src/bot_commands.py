from typing import Optional, List
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime

from src.config import config
from src.curseforge import CurseForgeAPI
from src.storage import ReleaseStorage

class ModUpdateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cf_api = CurseForgeAPI(config.curseforge_api_key)
        self.storage = ReleaseStorage()
        self.check_updates.start()

    def cog_unload(self):
        self.check_updates.cancel()

    def format_header(self, mod_name: str, version: str) -> str:
        """Format the header message with placeholders."""
        if config.message_header:
            return config.message_header.format(
                mod_name=mod_name,
                version=version
            )
        return f"@everyone {mod_name} version {version} is now available!"

    async def send_message(self, content: str, embed: Optional[discord.Embed] = None) -> None:
        channel_id = config.debug_channel_id if config.debug else config.releases_channel_id
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            message = await channel.send(content=content, embed=embed)
            if config.announce_messages and not config.debug:
                try:
                    await message.publish()
                except discord.errors.Forbidden:
                    print("Failed to publish message - missing permissions")
                except discord.errors.HTTPException:
                    print("Failed to publish message - not in news channel")

    @tasks.loop(minutes=5)
    async def check_updates(self):
        for mod_id in config.mod_ids:
            try:
                latest_file = await self.cf_api.get_latest_file(mod_id)
                if not latest_file:
                    continue

                mod_info = await self.cf_api.get_mod_info(mod_id)
                version = latest_file['version']
                
                if not self.storage.is_version_released(str(mod_id), version):
                    header = self.format_header(mod_info['name'], version)
                    embed = discord.Embed(
                        title=mod_info['name'],
                        description=header,
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    if changelog := latest_file.get('changelog'):
                        embed.add_field(
                            name="Changelog",
                            value=changelog,
                            inline=False
                        )
                    
                    if config.message_footer:
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
            
            except Exception as e:
                print(f"Error checking mod {mod_id}: {str(e)}")
                continue
            
            await asyncio.sleep(2)

    @check_updates.before_loop
    async def before_check_updates(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.is_owner()
    async def force_check(self, ctx):
        await ctx.send("Forcing update check...")
        await self.check_updates()
        await ctx.send("Update check completed.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ModUpdateCog(bot))
