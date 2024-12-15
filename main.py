import cohere
import os
import discord
import modal
from discord.ext import commands
from discord import app_commands
import sys


from dotenv import load_dotenv
load_dotenv()

from request_queue import llm_complete_request, init_request_queue


COHERE_API_KEY = os.environ["COHERE_API_KEY"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

co = cohere.Client(COHERE_API_KEY)


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents().all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        await init_request_queue()
        synced = await self.tree.sync()
        try:
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print(f'Slash CMDs: {str(len(synced))} Commands')
            print('------')
        except Exception as e:
            print(e)

        print('------')

    async def on_message(self, message):
        # Do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        is_dm = isinstance(message.channel, discord.channel.DMChannel)
        at_mention = f'<@{self.user.id}>'
        context_id = str(message.channel)
        if is_dm:
            context_id = str(message.channel)

        if message.content.startswith(at_mention) or is_dm:
            stripped_message = str(message.content).replace(at_mention, '').strip()
            async with message.channel.typing():
                await message.add_reaction('🤔')
                complete_response = await llm_complete_request(stripped_message, context_id)
                # await message.reply(complete_response, mention_author=True)
                if len(complete_response) < 1500:
                    await message.reply(complete_response, mention_author=True)
                else:
                    await message.reply(complete_response[:1500], mention_author=True)
                    await message.reply(complete_response[1500:], mention_author=True)


client = MyClient()


#
# Command used for testing
#
@client.tree.command(name="addsource")
@app_commands.checks.has_role("boss")
@app_commands.checks.cooldown(1, 5.0)
async def addsource(interaction: discord.Interaction):
    await interaction.response.send_modal(modal.ModalBotSetting())

@addsource.error
async def test_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(content=f"Failed! You can only run this command 3 times every 15 seconds. {str(error)}", ephemeral=True)
    elif isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message(content=f"Failed! You don't have the proper permissions. {str(error)}", ephemeral=True)
    else:
        await interaction.response.send_message(content={str(error)}, ephemeral=True)




def restart_bot(): 
  os.execv(sys.executable, ['python'] + sys.argv)

@client.tree.command(name= 'restart')
async def restart(interaction: discord.Interaction):
  await interaction.response.send_message(content="Restarting bot...")
  restart_bot()



client.run(DISCORD_TOKEN)

