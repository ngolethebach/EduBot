import discord

SOURCE_FILE_NAME = "source.json"
SOURCE = {}
DEFAULT_SOURCE = {
    "title": "Chatbot Wikipedia",
    "url": "https://en.wikipedia.org/wiki/Chatbot"
}

class ModalBotSetting(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Source Adding Form")
    
    title_field = discord.ui.TextInput(
        label="Title",
        default=""
    )

    source_filed = discord.ui.TextInput(
        label="URL/Link Source",
        default=""
    )

    async def on_submit(self, interaction):
        pass