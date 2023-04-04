from src import personas
from asgiref.sync import sync_to_async

async def official_handle_response(message, client) -> str:
    return await sync_to_async(client.chatbot.ask)(message)

async def unofficial_handle_response(message, client) -> str:
    async for response in client.chatbot.ask(message):
        responseMessage = response["message"]
    return responseMessage

async def bard_handle_response(message, client) -> str:
    response = await sync_to_async(client.chatbot.ask)(message)
    responseMessage = response["content"]
    return responseMessage

async def switch_persona(persona, client) -> None:
    if client.chat_modell ==  "UNOFFIZIELL":
        client.chatbot.reset_chat()
        async for response in client.chatbot.ask(personas.PERSONAS.get(persona)):
            pass
    elif client.chat_modell == "OFFIZIELL":
        client.chatbot.reset()
        await sync_to_async(client.chatbot.ask)(personas.PERSONAS.get(persona))
    elif client.chat_modell == "Bard":
        client.chatbot = client.get_chatbot_modell()
        await sync_to_async(client.chatbot.ask)(personas.PERSONAS.get(persona))
