import asyncio
import discord
from discord.ext import commands
import sys
import logging

from src.config import config

# Set up intents
logging.debug("Setting up Discord intents")
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
logging.debug("Initializing Discord bot")
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    logging.info('------')
    
    # Send startup message to debug channel
    debug_channel = bot.get_channel(config.debug_channel_id)
    if debug_channel:
        await debug_channel.send(f"Bot has started - logged in as {bot.user.name}")
    else:
        logging.error(f"Could not find debug channel with ID {config.debug_channel_id}")

async def main():
    logging.debug("Starting main application")
    
    # Validate configuration
    logging.debug("Validating configuration")
    errors = config.validate()
    if errors:
        logging.error("Configuration validation failed")
        print("Configuration errors:")
        for error in errors:
            logging.error(f"Configuration error: {error}")
            print(f"- {error}")
        sys.exit(1)
    logging.info("Configuration validation successful")

    # Load the cog
    try:
        logging.debug("Loading bot_commands extension")
        await bot.load_extension('src.bot_commands')
        logging.info("Successfully loaded bot_commands extension")
    except Exception as e:
        logging.error(f"Failed to load bot_commands: {str(e)}", exc_info=True)
        print(f"Failed to load bot_commands: {str(e)}")
        sys.exit(1)

    # Start the bot
    try:
        logging.info("Starting Discord bot")
        await bot.start(config.bot_token)
    except discord.LoginFailure:
        logging.error("Failed to login - invalid bot token")
        print("Failed to login. Please check your bot token.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logging.info("Application starting")
    asyncio.run(main())
