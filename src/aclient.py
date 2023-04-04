import os
import discord
from typing import Union
from src import log, responses
from dotenv import load_dotenv
from discord import app_commands
from Bard import Chatbot as BardChatbot
from revChatGPT.V3 import Chatbot
from revChatGPT.V1 import AsyncChatbot

logger = log.setup_logger(__name__)
load_dotenv()

class aclient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.listening, name="/chat | /help")
        self.isPrivate = False
        self.is_replying_all = os.getenv("REPLYING_ALL")
        self.replying_all_discord_channel_id = os.getenv("REPLYING_ALL_DISCORD_CHANNEL_ID")
        self.openAI_email = os.getenv("OPENAI_EMAIL")
        self.openAI_password = os.getenv("OPENAI_PASSWORD")
        self.openAI_API_key = os.getenv("OPENAI_API_KEY")
        self.openAI_gpt_engine = os.getenv("GPT_ENGINE")
        self.chatgpt_session_token = os.getenv("SESSION_TOKEN")
        self.chatgpt_access_token = os.getenv("ACCESS_TOKEN")
        self.chatgpt_paid = os.getenv("UNOFFICIAL_PAID")
        self.bard_session_id = os.getenv("BARD_SESSION_ID")
        self.chat_model = os.getenv("CHAT_MODEL")
        self.chatbot = self.get_chatbot_model()

    def get_chatbot_model(self) -> Union[AsyncChatbot, Chatbot]:
        if self.chat_model == "UNOFFIZIELL":
            return AsyncChatbot(config={"email": self.openAI_email, "password": self.openAI_password, "access_token": self.chatgpt_access_token, "model": self.openAI_gpt_engine, "paid": self.chatgpt_paid})
        elif self.chat_model == "OFFFIZIELL":
            return Chatbot(api_key=self.openAI_API_key, engine=self.openAI_gpt_engine)
        elif self.chat_model == "Bard":
            return BardChatbot(session_id=self.bard_session_id)

    async def send_message(self, message, user_message):
        if self.is_replying_all == "False":
            author = message.user.id
            await message.response.defer(ephemeral=self.isPrivate)
        else:
            author = message.author.id
        try:
            response = (f'> **{user_message}** - <@{str(author)}' + '> \n\n')
            if self.chat_model == "OFFFIZIELL":
                response = f"{response}{await responses.official_handle_response(user_message, self)}"
            elif self.chat_model == "UNOFFFIZIELL":
                response = f"{response}{await responses.unofficial_handle_response(user_message, self)}"
            elif self.chat_model == "Bard":
                response = f"{response}{await responses.bard_handle_response(user_message, self)}"
            char_limit = 1900
            if len(response) > char_limit:
                if "```" in response:
                    parts = response.split("```")

                    for i in range(len(parts)):
                        if i%2 == 0:
                            if self.is_replying_all == "True":
                                await message.channel.send(parts[i])
                            else:
                                await message.followup.send(parts[i])
                        else: 
                            code_block = parts[i].split("\n")
                            formatted_code_block = ""
                            for line in code_block:
                                while len(line) > char_limit:
                                    formatted_code_block += line[:char_limit] + "\n"
                                    line = line[char_limit:]
                                formatted_code_block += line + "\n"

                            if (len(formatted_code_block) > char_limit+100):
                                code_block_chunks = [formatted_code_block[i:i+char_limit]
                                                    for i in range(0, len(formatted_code_block), char_limit)]
                                for chunk in code_block_chunks:
                                    if self.is_replying_all == "True":
                                        await message.channel.send(f"```{chunk}```")
                                    else:
                                        await message.followup.send(f"```{chunk}```")
                            elif self.is_replying_all == "True":
                                await message.channel.send(f"```{formatted_code_block}```")
                            else:
                                await message.followup.send(f"```{formatted_code_block}```")
                else:
                    response_chunks = [response[i:i+char_limit]
                                    for i in range(0, len(response), char_limit)]
                    for chunk in response_chunks:
                        if self.is_replying_all == "True":
                            await message.channel.send(chunk)
                        else:
                            await message.followup.send(chunk)
            elif self.is_replying_all == "True":
                await message.channel.send(response)
            else:
                await message.followup.send(response)
        except Exception as e:
            if self.is_replying_all == "True":
                await message.channel.send("> **Hoppla: Etwas ist schiefgelaufen. Versuche es später erneut!**")
            else:
                await message.followup.send("> **Eoppla: Etwas ist schiefgelaufen. Versuche es später erneut!**")
            logger.exception(f"Fehler beim Senden einer Nachricht: {e}")

    async def send_start_prompt(self):
        import os.path

        config_dir = os.path.abspath(f"{__file__}/../../")
        prompt_name = 'starting-prompt.txt'
        prompt_path = os.path.join(config_dir, prompt_name)
        discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
        try:
            if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    prompt = f.read()
                    if (discord_channel_id):
                        logger.info(f"Sende einen Startprompt in der Größe: {len(prompt)}")
                        response = ""
                        if self.chat_model == "OFFIZIELL":
                            response = f"{response}{await responses.official_handle_response(prompt, self)}"
                        elif self.chat_model == "UNOFFIZIELL":
                            response = f"{response}{await responses.unofficial_handle_response(prompt, self)}"
                        elif self.chat_model == "Bard":
                            response = f"{response}{await responses.bard_handle_response(prompt, self)}"
                        channel = self.get_channel(int(discord_channel_id))
                        await channel.send(response)
                        logger.info(f"Startprompt Antwort:{response}")
                    else:
                        logger.info("Kein Kanal ausgewählt. Überspringe das senden eines Startprompts.")
            else:
                logger.info(f"Kein {prompt_name}. Überspringe das senden eines Startprompts.")
        except Exception as e:
            logger.exception(f"Fehler beim Senden eines Startprompts: {e}")


client = aclient()
