import asyncio
import re
import os
from telethon.sync import TelegramClient

# Suas credenciais da API do Telegram (para uma conta de usuário)
api_id = 'SEU API ID'
api_hash = 'SEU API HASH'

# Nome do canal do qual você quer baixar os vídeos (use o username ou ID)
channel_id = -0000000

# Mensagem que contém os tópicos e vídeos
message_content = '''
= 1. Comece por aqui
#F0001 #F0002 #F0003 #F0004 #F0005
...
'''

# Função para exibir o progresso do download
def progress_callback(current, total):
    percent_complete = (current / total) * 100
    print(f"Progresso: {percent_complete:.2f}% ({current} de {total} bytes)", end="\r")


# Função para extrair tópicos e vídeos
def parse_message(content):
    sections = re.split(r"= \d+\.\s*", content)  # Divida os tópicos pelo número do capítulo
    topics_videos = {}
    
    for section in sections:
        if not section.strip():
            continue
        
        lines = section.strip().split('\n')
        topic_name = lines[0].strip()  # O nome do tópico é a primeira linha
        video_ids = re.findall(r"(#F\d+)", section)  # Encontre todos os #FXXXX
        
        topics_videos[topic_name] = video_ids

    return topics_videos

# Função para baixar vídeos com limitação de concorrência
async def download_video(client, message, video_id, topic_path, semaphore):
    async with semaphore:  # Limita o número de tarefas simultâneas
        # Extrair o nome original do arquivo
        original_name = message.file.name if message.file and message.file.name else "unknown"
        
        # Formatar o nome do arquivo como "ID - Nome original"
        file_name = f"{video_id} - {original_name}"
        
        # Definir o caminho completo onde o arquivo será salvo
        file_path = os.path.join(topic_path, file_name)
        
        # Baixar o vídeo com o callback para mostrar o progresso
        await client.download_media(message, file=file_path, progress_callback=progress_callback)
        print(f'\nVídeo {video_id} baixado com sucesso em {file_path}')


# Função para baixar vídeos
async def download_videos(client, topics_videos, channel, max_concurrent_downloads=5):
    # Cria uma pasta para organizar os vídeos
    if not os.path.exists('videos'):
        os.makedirs('videos')

    # Limita o número de downloads simultâneos
    semaphore = asyncio.Semaphore(max_concurrent_downloads)

    tasks = []  # Lista de tarefas assíncronas

    for topic, videos in topics_videos.items():
        # Cria uma subpasta para cada tópico
        topic_path = os.path.join('videos', topic)
        if not os.path.exists(topic_path):
            os.makedirs(topic_path)

        for video_id in videos:
            print(f'Baixando vídeo {video_id} do tópico {topic}')
            async for message in client.iter_messages(channel, search=video_id):
                if message.video:  # Se a mensagem contém um vídeo
                    # Extrair o nome original do arquivo
                    original_name = message.file.name if message.file and message.file.name else "unkown"
                    
                    # Cria uma tarefa para o download do vídeo
                    task = asyncio.create_task(download_video(client, message, video_id, topic_path, semaphore))
                    tasks.append(task)
                    
                    file_name = f"{video_id} - {original_name}.mp4"
                    file_path = os.path.join(topic_path, file_name)

                    await client.download_media(message, file=file_path, progress_callback=progress_callback)
                    print(f'Vídeo {video_id} baixado com sucesso em {file_path}')
                    break

async def main():
    # Conectar ao cliente do Telegram (conta de usuário)
    async with TelegramClient('telegramDown', api_id, api_hash) as client:
        try:
            # Obter o canal (por ID ou username)
            channel = await client.get_entity('LINK DO SEU CANAL INSTAGRAM')
            print(f"Usuário tem acesso ao canal: {channel.title}")
       
            # Extrair os vídeos e tópicos da mensagem
            topics_videos = parse_message(message_content)

            # Baixar os vídeos organizados por tópicos
            await download_videos(client, topics_videos, channel)

        except Exception as e:
                    print(f'Erro ao acessar o canal: {e}')


if __name__ == "__main__":
    # Executa o cliente assíncrono
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())