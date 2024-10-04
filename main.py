import os
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, errors
from telethon.tl.types import PeerChannel

# Configuração do logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Obter as variáveis do arquivo .env
API_ID = os.getenv("API_ID")  # Seu API ID
API_HASH = os.getenv("API_HASH")  # Seu API Hash
PHONE_NUMBER = os.getenv("PHONE_NUMBER")  # Seu número de telefone com o código do país
CHANNEL_ORIGEM = os.getenv("CHANNEL_ORIGEM")
CHANNEL_DESTINO = os.getenv("CHANNEL_DESTINO")
LAST_ID_FILE = (
    "last_message_id.txt"  # Nome do arquivo para armazenar o último ID enviado
)

# Tipos permitidos de mensagens para encaminhamento
TIPOS_PERMITIDOS = [
    "photo",  # Fotos
    "document",  # Documentos (ex: PDFs)
    "video",  # Vídeos
    "audio",  # Áudios (não mensagem de voz)
    "voice",  # Mensagens de voz
    "text",  # Mensagens de texto simples
]

# Crie uma sessão com sua conta de usuário
client = TelegramClient("session_name", API_ID, API_HASH)


async def get_entity(client, channel_identifier):
    """Função para obter a entidade correta com base no ID ou @username."""

    try:
        if channel_identifier.startswith("-100"):
            return PeerChannel(int(channel_identifier))
        else:
            return await client.get_entity(channel_identifier)
    except Exception as e:
        logging.error(f"Erro ao resolver a entidade para {channel_identifier}: {e}")
        raise


def ler_ultimo_id():
    """Lê o último ID salvo no arquivo."""

    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as file:
            try:
                return int(file.read().strip())
            except ValueError:
                logging.warning("Arquivo de ID inválido, começando do início.")
    return 0


def salvar_ultimo_id(ultimo_id):
    """Salva o último ID enviado no arquivo."""

    with open(LAST_ID_FILE, "w") as file:
        file.write(str(ultimo_id))


async def encaminhar_mensagens():
    """Função para buscar e encaminhar mensagens do canal de origem para o destino."""

    origem = await get_entity(client, CHANNEL_ORIGEM)
    destino = await get_entity(client, CHANNEL_DESTINO)

    ultimo_id = ler_ultimo_id()
    mensagens_enviadas = 0
    logging.info(f"Iniciando o encaminhamento a partir da mensagem ID {ultimo_id + 1}.")

    async for message in client.iter_messages(origem, min_id=ultimo_id, reverse=True):
        try:
            if TIPOS_PERMITIDOS:
                if "photo" in TIPOS_PERMITIDOS and message.photo:
                    await encaminhar_arquivo(message, destino, "foto")
                elif "document" in TIPOS_PERMITIDOS and message.document:
                    await encaminhar_arquivo(message, destino, "documento")
                elif "video" in TIPOS_PERMITIDOS and message.video:
                    await encaminhar_arquivo(message, destino, "vídeo")
                elif "audio" in TIPOS_PERMITIDOS and message.audio:
                    await encaminhar_arquivo(message, destino, "áudio")
                elif "voice" in TIPOS_PERMITIDOS and message.voice:
                    await encaminhar_arquivo(message, destino, "mensagem de voz")
                elif "text" in TIPOS_PERMITIDOS and message.text:
                    await encaminhar_texto(message, destino)
                elif "sticker" in TIPOS_PERMITIDOS and message.sticker:
                    await encaminhar_arquivo(message, destino, "sticker")
                elif "animation" in TIPOS_PERMITIDOS and message.animation:
                    await encaminhar_arquivo(message, destino, "animação (GIF)")
                elif "contact" in TIPOS_PERMITIDOS and message.contact:
                    await encaminhar_contato(message, destino)
                elif "poll" in TIPOS_PERMITIDOS and message.poll:
                    await encaminhar_enquete(message, destino)
                else:
                    logging.info(
                        f"Mensagem {message.id} ignorada, não corresponde aos tipos permitidos."
                    )
            else:
                await encaminhar_arquivo(message, destino)
                logging.info(f"Encaminhado mensagem genérica: {message.id}")

            # Salva o ID da última mensagem enviada
            salvar_ultimo_id(message.id)
            mensagens_enviadas += 1
            await asyncio.sleep(5)

            # Aguarda 15 segundos após enviar 100 mensagens
            if mensagens_enviadas >= 100:
                await asyncio.sleep(15)
                mensagens_enviadas = 0

        except Exception as e:
            logging.error(f"Erro ao enviar mensagem {message.id}: {e}")
            break  # Se ocorrer qualquer erro, interrompe o script


async def encaminhar_arquivo(message, destino, tipo=None):
    """Encaminha a mensagem com o tipo especificado."""

    caption = getattr(message, "message", "")
    await client.send_file(destino, message.media, caption=caption)
    logging.info(
        f"Encaminhado {tipo or 'mensagem genérica'}: {message.id} com legenda: {caption}"
    )


async def encaminhar_texto(message, destino):
    """Encaminha uma mensagem de texto."""

    await client.send_message(destino, message.text)
    logging.info(f"Encaminhado texto: {message.id} com messagem: {message.text}")


async def encaminhar_contato(message, destino):
    """Encaminha um contato."""

    await client.send_message(destino, message.contact)
    logging.info(f"Encaminhado contato: {message.id}")


async def encaminhar_enquete(message, destino):
    """Encaminha uma enquete."""

    await client.send_poll(
        destino, question=message.poll.question, options=message.poll.options
    )
    logging.info(f"Encaminhado enquete: {message.id}")


async def main():
    await client.start(phone=PHONE_NUMBER)
    await encaminhar_mensagens()

    logging.info("Mensagens encaminhadas com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
