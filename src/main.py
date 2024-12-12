import asyncio
import discord
from discord.ext import commands
import sys
from src.config import config

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

async def main():
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    # Load the cog
    try:
        await bot.load_extension('src.bot_commands')
    except Exception as e:
        print(f"Failed to load bot_commands: {str(e)}")
        sys.exit(1)

    # Start the bot
    try:
        await bot.start(config.bot_token)
    except discord.LoginFailure:
        print("Failed to login. Please check your bot token.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
