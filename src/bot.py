import os
import openai
import discord
from random import randrange
from src.aclient import client
from discord import app_commands
from src import log, art, personas, responses

logger = log.setup_logger(__name__)

def run_discord_bot():
    @client.event
    async def on_ready():
        await client.send_start_prompt()
        await client.tree.sync()
        logger.info(f'{client.user} läuft!')

    @client.tree.command(name="chat", description="Schreib mit ChatGPT hier auf Königsmine!")
    async def chat(interaction: discord.Interaction, *, message: str):
        if client.is_replying_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **Hoppla: Der Bot ist im Chatmodus. Wenn du Slashcommands nutzen möchtest, wechsle zum normalen Chatmodus mit `/chatmodus`**")
            logger.warning("\x1b[31mDer bot ist im chatmodus.\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({channel})")
        await client.send_message(interaction, message)


    @client.tree.command(name="privat", description="Aktiviere privaten Zugang.")
    async def privat(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not client.isPrivat:
            client.isPrivat = not client.isPrivat
            logger.warning("\x1b[31mAktiviere privaten Zugang.\x1b[0m")
            await interaction.followup.send(
                "> **INFO: Ab jetzt werden die Antworten als persönliche Nachricht gesendet. Wenn du die Antworten wieder Öffentlich haben möchtest, schreibe `/öffentlich` !**")
        else:
            logger.info("Fehler beim Aktivieren des privaten Zugangs. Fehler: Bereits Aktiv!")
            await interaction.followup.send(
                "> **WARNUNG: Der Privatmodus ist bereits aktiviert! Wenn du zum Öffentlichen Modus wechseln möchtest, shreibe `/öffentlich`**")

    @client.tree.command(name="öffentlich", description="Wechsle zu öffentlichen Modus.")
    async def öffentlich(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if client.isPrivat:
            client.isPrivat = not client.isPrivat
            await interaction.followup.send(
                "> **INFO: Der öffentliche Modus wurde aktiviert! Wenn du zurück in den privaten Modus möchtest, schreibe `/privat`**")
            logger.warning("\x1b[31mAktiviere öffentlichen Zugang.\x1b[0m")
        else:
            await interaction.followup.send(
                "> **WARNUNG: Öffentlicher Modus ist bereits aktiviert! Wenn du zurück in den privaten Modus möchtest, schreibe `/privat`**")
            logger.info("Fehler beim Aktivieren des Öffentlichen Zugangs. Fehler: Bereits Aktiv!")


    @client.tree.command(name="chatmodus", description="Aktiviert oder deaktiviert dass der Bot auf alle Nachrichten reagiert.")
    async def chatmodus(interaction: discord.Interaction):
        client.replying_all_discord_channel_id = str(interaction.channel_id)
        await interaction.response.defer(ephemeral=False)
        if client.is_replying_all == "True":
            client.is_replying_all = "False"
            await interaction.followup.send(
                "> **INFO: Ab jetzt hört der Bot wieder auf Slashcommands. Wenn der Bot auf alle Nachrichten reagieren soll, schreibe `/chatmodus`**")
            logger.warning("\x1b[31mAktiviere CM: Normal\x1b[0m")
        elif client.is_replying_all == "False":
            client.is_replying_all = "True"
            await interaction.followup.send(
                "> **INFO: Ab jetzt hört reagiert der Bot auf alle Nachrichten in diesem Chat. Wärenddessen reagiert er nicht auf `/chat`. Wenn du wieder den normalen Chatmodus aktivieren möchtest, schreibe `/chatmodus`**")
            logger.warning("\x1b[31mAktiviere CM: ReplyALL\x1b[0m")


    @client.tree.command(name="chat_modell", description="Wechsle zu einen anderen Chatmodell")
    @app_commands.choices(choices=[
        app_commands.Choice(name="OFFIZIELL GPT-3.5", value="OFFIZIELL"),
        app_commands.Choice(name="OFFIZIELL GPT-4.0", value="OFFIZIELL-GPT4"),
        app_commands.Choice(name="Webseiten ChatGPT-3.5", value="UNOFFIZIELL"),
        app_commands.Choice(name="Webseiten ChatGPT-4.0", value="UNOFFIZIELL-GPT4"),
        app_commands.Choice(name="Bard", value="Bard"),
    ])

    async def chat_modell(interaction: discord.Interaction, choices: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        original_chat_modell = client.chat_modell
        original_openAI_gpt_engine = client.openAI_gpt_engine

        try:
            if choices.value == "OFFIZIELL":
                client.openAI_gpt_engine = "gpt-3.5-turbo"
                client.chat_modell = "OFFIZIELL"
            elif choices.value == "OFFIZIELL-GPT4":
                client.openAI_gpt_engine = "gpt-4"
                client.chat_modell = "OFFIZIELL"
            elif choices.value == "UNOFFIZIELL":
                client.openAI_gpt_engine = "gpt-3.5-turbo"
                client.chat_modell = "UNOFFIZIELL"
            elif choices.value == "UNOFFIZIELL-GPT4":
                client.openAI_gpt_engine = "gpt-4"
                client.chat_modell = "UNOFFIZIELL"
            elif choices.value == "Bard":
                client.chat_modell = "Bard"
            else:
                raise ValueError("Hoppla: Ungültige Auswahl!")

            client.chatbot = client.get_chatbot_modell()
            await interaction.followup.send(f"> **INFO: Chat Modell zu `{client.chat_modell}` Gewechselt!**\n")
            logger.warning(f"\x1b[31Aktiviere Chat Modell {client.chat_modell}\x1b[0m")

        except Exception as e:
            client.chat_modell = original_chat_modell
            client.openAI_gpt_engine = original_openAI_gpt_engine
            client.chatbot = client.get_chatbot_modell()
            await interaction.followup.send(f"> **Hoppla: Das `{choices.value}` Chat Model kann nicht aktiviert werden. Die nötigen Daten sind nicht vorhanden!**\n")
            logger.exception(f"Fehler beim wechseln zu dem {choices.value} Chat Modell - {e}")


    @client.tree.command(name="reset", description="Setzt den Gesamten Chatverlauf zurück.")
    async def reset(interaction: discord.Interaction):
        if client.chat_modell == "OFFIZIELL":
            client.chatbot.reset()
        elif client.chat_modell == "UNOFFIZIELL":
            client.chatbot.reset_chat()
        elif client.chat_modell == "Bard":
            client.chatbot = client.get_chatbot_modell()
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **INFO: Der Verlauf wurde entfernt..**")
        personas.current_persona = "standard"
        logger.warning(
            "\x1b[31mChatverlauf wurde erfolgreich zurückgesetzt.\x1b[0m")

    @client.tree.command(name="hilfe", description="Zeigt das Hilfefenster für den Bot. c:")
    async def hilfe(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":star: **STANDART KOMMANDS** \n
        - `/chat [nachricht]`Schreib mit ChatGPT auf Königsmine!
        - `/imagine [prompt]` Generiert ein Bild mit Dalle2.
        - `/person [auswahl]` Wähle einen optionalen ChatGPT jailbreak!
                `random`: Wählt einen Random jailbreak aus.
                `chatgpt`: Standard ChatGPT Modus.
                `dan`: Dan Mode 11.0
                `sda`: Superior DAN Mode
                `confidant`: Evil Confidant Mode
                `based`: BasedGPT v2
                `oppo`: OPPO REVERSE
                `dev`: Developer Mode v2 

        - `/privat` Aktiviert den Privaten Modus um Antworten nicht mehr öffentlich zu senden.
        - `/öffentlich` Aktiviert den Öffentlichen Modus um Antworten öffentlich zu senden.
        - `/chatmodus` Aktiviert oder deaktiviert dass der Bot auf alle Nachrichten im aktiellen Kanal antwortet. 
        - `/reset` Löscht den Chatverlauf für ChatGPT um einen neuen Chat zu starten.
        - `/chat_model` Ändert das aktuelle Chat Modell.
                `OFFIZIELL`: GPT-3.5 Modell
                `UNOFFIZIELL`: Webseiten ChatGPT
                `Bard`: Google Bard Modell

By *`KnuddelTeddy & ChatGPT`* **c:**""")

        logger.info(
            "\x1b[31mJemand nutzt /hilfe!\x1b[0m")

    @client.tree.command(name="imagine", description="Generiert ein Bild mit Dalle2.")
    async def imagine(interaction: discord.Interaction, *, prompt: str):
        if interaction.user == client.user:
            return

        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /imagine [{prompt}] in ({channel})")

        await interaction.response.defer(thinking=True, ephemeral=client.isPrivat)
        try:
            path = await art.draw(prompt)

            file = discord.File(path, filename="image.png")
            title = f'> **{prompt}** - <@{str(interaction.user.mention)}' + '> \n\n'
            embed = discord.Embed(title=title)
            embed.set_image(url="attachment://image.png")

            await interaction.followup.send(file=file, embed=embed)

        except openai.InvalidRequestError:
            await interaction.followup.send(
                "> **Hoppla: Unangemessene Anfrage! >:c **")
            logger.info(
            f"\x1b[31m{username}\x1b[0m Hat eine unangemessene Anfrage an Dalle2 gesendet!")

        except Exception as e:
            await interaction.followup.send(
                "> **Hoppla: Irgend etwas ist schiefgelaufen...**")
            logger.exception(f"Fehler beim erstellen eines Bildes: {e}")


    @client.tree.command(name="person", description="Wähle einen optionalen ChatGPT jailbreak! Achtung, dadurch kann es passieren das der Bot Englisch antwortet.")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Random", value="random"),
        app_commands.Choice(name="Standard", value="standard"),
        app_commands.Choice(name="Do Anything Now 11.0", value="dan"),
        app_commands.Choice(name="Superior Do Anything", value="sda"),
        app_commands.Choice(name="Evil Confidant", value="confidant"),
        app_commands.Choice(name="BasedGPT v2", value="based"),
        app_commands.Choice(name="OPPO REVERSE", value="oppo"),
        app_commands.Choice(name="Developer Mode v2", value="dev"),
        app_commands.Choice(name="DUDE V3", value="dude_v3"),
        app_commands.Choice(name="AIM", value="aim"),
        app_commands.Choice(name="UCAR", value="ucar"),
        app_commands.Choice(name="Jailbreak", value="jailbreak")
    ])
    async def person(interaction: discord.Interaction, persona: app_commands.Choice[str]):
        if interaction.user == client.user:
            return

        await interaction.response.defer(thinking=True)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '/person [{persona.value}]' ({channel})")

        persona = persona.value

        if persona == personas.current_persona:
            await interaction.followup.send(f"> **WARNUNG: `{persona}` bereits aktiviert!**")

        elif persona == "standard":
            if client.chat_modell == "OFFIZIELL":
                client.chatbot.reset()
            elif client.chat_modell == "UNOFFIZIELL":
                client.chatbot.reset_chat()
            elif client.chat_modell == "Bard":
                client.chat_modell = client.get_chatbot_model()

            personas.current_persona = "standard"
            await interaction.followup.send(
                f"> **INFO: Gewechselt zu `{persona}` jailbreak!**")

        elif persona == "random":
            choices = list(personas.PERSONAS.keys())
            choice = randrange(0, 6)
            chosen_persona = choices[choice]
            personas.current_persona = chosen_persona
            await responses.switch_persona(chosen_persona, client)
            await interaction.followup.send(
                f"> **INFO: Gewechselt zu `{chosen_persona}` jailbreak!**")


        elif persona in personas.PERSONAS:
            try:
                await responses.switch_persona(persona, client)
                personas.current_persona = persona
                await interaction.followup.send(
                f"> **INFO: Gewechselt zu `{persona}` jailbreak!**")
            except Exception as e:
                await interaction.followup.send(
                    "> **Hoppla: Irgendetwas ist schiefgelaufen. Bitte versuch es später erneut. 😿**")
                logger.exception(f"Fehler beim wechseln der Person: {e}")

        else:
            await interaction.followup.send(
                f"> **Hoppla: Kein Jailbreak namens `{persona}` bekannt! :c**")
            logger.info(
                f'{username} hat eine unbekannte Person angefragt: `{persona}`')

    @client.event
    async def on_message(message):
        if client.is_replying_all == "True":
            if message.author == client.user:
                return
            if client.replying_all_discord_channel_id:
                if message.channel.id == int(client.replying_all_discord_channel_id):
                    username = str(message.author)
                    user_message = str(message.content)
                    channel = str(message.channel)
                    logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
                    await client.send_message(message, user_message)
            else:
                logger.exception("replying_all_discord_channel_id nicht gefunden, Bitte nutze den Command `/chatmodus` nocheinmal.")

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    client.run(TOKEN)
