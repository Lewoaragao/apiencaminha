import os
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

# Configuração do logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Obter as variáveis do arquivo .env
API_ID = os.getenv('API_ID')   # Seu API ID
API_HASH = os.getenv('API_HASH') # Seu API Hash
PHONE_NUMBER = os.getenv('PHONE_NUMBER')  # Seu número de telefone com o código do país
CHANNEL_ORIGEM = os.getenv('CHANNEL_ORIGEM')
CHANNEL_DESTINO = os.getenv('CHANNEL_DESTINO')

# Crie uma sessão com sua conta de usuário
client = TelegramClient('session_name', API_ID, API_HASH)

async def encaminhar_mensagens():
    # Obtém o canal de origem e destino
    origem = await client.get_entity(CHANNEL_ORIGEM)
    destino = await client.get_entity(CHANNEL_DESTINO)

    # Busca as mensagens do canal de origem
    async for message in client.iter_messages(origem):
        try:
            # Verifica se a mensagem contém uma foto
            if message.photo:
                caption = getattr(message, 'caption', '')
                await client.send_file(destino, message.photo, caption=caption)
                logging.info(f"Encaminhado foto: {message.id} para {CHANNEL_DESTINO} com legenda: {caption}")

            # Verifica se a mensagem contém um documento (PDF)
            elif message.document and message.document.mime_type == 'application/pdf':
                caption = getattr(message, 'caption', '')
                await client.send_file(destino, message.document, caption=caption)
                logging.info(f"Encaminhado PDF: {message.id} para {CHANNEL_DESTINO} com legenda: {caption}")

            else:
                logging.warning(f"Mensagem {message.id} não é uma foto ou PDF.")
            
            # Adiciona um delay de 10 segundos entre envios
            await asyncio.sleep(10)  # Delay de 10 segundos entre cada envio

        except Exception as e:
            logging.error(f"Erro ao enviar mensagem {message.id}: {e}")

async def main():
    await client.start(phone=PHONE_NUMBER)
    await encaminhar_mensagens()

if __name__ == '__main__':
    asyncio.run(main())
