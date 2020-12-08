# Thanks to @AvinashReddy3108 for this plugin
# Instadl by @Jisan7509

import asyncio
import os
import time
from datetime import datetime
from html import unescape
from pathlib import Path

from googleapiclient.discovery import build
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.types import DocumentAttributeAudio
from youtube_dl import YoutubeDL
from youtube_dl.utils import (
    ContentTooShortError,
    DownloadError,
    ExtractorError,
    GeoRestrictedError,
    MaxDownloadsReached,
    PostProcessingError,
    UnavailableVideoError,
    XAttrMetadataError,
)

from ..utils import admin_cmd, edit_or_reply, sudo_cmd
from . import CMD_HELP, hmention, progress, reply_id


@bot.on(admin_cmd(pattern="yt(a|v) (.*)", outgoing=True))
@bot.on(sudo_cmd(pattern="yt(a|v) (.*)", allow_sudo=True))
async def download_video(v_url):
    """ For .ytdl command, download media from YouTube and many other sites. """
    url = v_url.pattern_match.group(2)
    ytype = v_url.pattern_match.group(1).lower()
    v_url = await edit_or_reply(v_url, "`Preparando para baixar...`")
    reply_to_id = await reply_id(v_url)
    if ytype == "a":
        opts = {
            "format": "bestaudio",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "outtmpl": "%(id)s.mp3",
            "quiet": True,
            "logtostderr": False,
        }
        video = False
        song = True
    elif ytype == "v":
        opts = {
            "format": "best",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
            ],
            "outtmpl": "%(id)s.mp4",
            "logtostderr": False,
            "quiet": True,
        }
        song = False
        video = True
    try:
        await v_url.edit("`Buscando dados, por favor aguarde ..`")
        with YoutubeDL(opts) as ytdl:
            ytdl_data = ytdl.extract_info(url)
    except DownloadError as DE:
        await v_url.edit(f"`{str(DE)}`")
        return
    except ContentTooShortError:
        await v_url.edit("`O conteúdo do download era muito pequeno.`")
        return
    except GeoRestrictedError:
        await v_url.edit(
            "`O vídeo não está disponível em sua localização/localização do servidor..`"
        )
        return
    except MaxDownloadsReached:
        await v_url.edit("`O limite máximo de downloads foi atingido.`")
        return
    except PostProcessingError:
        await v_url.edit("`Ocorreu um erro durante o pós-processamento.`")
        return
    except UnavailableVideoError:
        await v_url.edit("`A mídia não está disponível no formato solicitado.`")
        return
    except XAttrMetadataError as XAME:
        await v_url.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
        return
    except ExtractorError:
        await v_url.edit("`Ocorreu um erro durante a extração de informações.`")
        return
    except Exception as e:
        await v_url.edit(f"{str(type(e)): {str(e)}}")
        return
    c_time = time.time()
    catthumb = Path(f"{ytdl_data['id']}.jpg")
    if not os.path.exists(catthumb):
        catthumb = Path(f"{ytdl_data['id']}.webp")
    elif not os.path.exists(catthumb):
        catthumb = None
    if song:
        await v_url.edit(
            f"`Preparando para fazer upload da música:`\
        \n**{ytdl_data['title']}**\
        \nby *{ytdl_data['uploader']}*"
        )
        await v_url.client.send_file(
            v_url.chat_id,
            f"{ytdl_data['id']}.mp3",
            supports_streaming=True,
            thumb=catthumb,
            reply_to=reply_to_id,
            attributes=[
                DocumentAttributeAudio(
                    duration=int(ytdl_data["duration"]),
                    title=str(ytdl_data["title"]),
                    performer=str(ytdl_data["uploader"]),
                )
            ],
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(
                    d, t, v_url, c_time, "A enviar", f"{ytdl_data['title']}.mp3"
                )
            ),
        )
        os.remove(f"{ytdl_data['id']}.mp3")
    elif video:
        await v_url.edit(
            f"`Preparando para enviar vídeo:`\
        \n**{ytdl_data['title']}**\
        \nby *{ytdl_data['uploader']}*"
        )
        await v_url.client.send_file(
            v_url.chat_id,
            f"{ytdl_data['id']}.mp4",
            reply_to=reply_to_id,
            supports_streaming=True,
            caption=ytdl_data["title"],
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(
                    d, t, v_url, c_time, "A enviar", f"{ytdl_data['title']}.mp4"
                )
            ),
        )
        os.remove(f"{ytdl_data['id']}.mp4")
    if catthumb:
        os.remove(catthumb)
    await v_url.delete()


@bot.on(admin_cmd(pattern="yts (.*)"))
@bot.on(sudo_cmd(pattern="yts (.*)", allow_sudo=True))
async def yt_search(video_q):
    """ For .yts command, do a YouTube search from Telegram. """
    query = video_q.pattern_match.group(1)
    result = ""
    if not Config.YOUTUBE_API_KEY:
        await edit_or_reply(
            video_q,
            "`Erro: chave de API do YouTube ausente!.`",
        )
        return
    video_q = await edit_or_reply(video_q, "```Processando...```")
    full_response = await youtube_search(query)
    videos_json = full_response[1]
    for video in videos_json:
        title = f"{unescape(video['snippet']['title'])}"
        link = f"https://youtu.be/{video['id']['videoId']}"
        result += f"{title}\n{link}\n\n"
    reply_text = f"**Pesquisa:**\n`{query}`\n\n**Resultados:**\n\n{result}"
    await video_q.edit(reply_text)


async def youtube_search(
    query, order="relevance", token=None, location=None, location_radius=None
):
    """ Do a YouTube search. """
    youtube = build(
        "youtube", "v3", developerKey=Config.YOUTUBE_API_KEY, cache_discovery=False
    )
    search_response = (
        youtube.search()
        .list(
            q=query,
            type="video",
            pageToken=token,
            order=order,
            part="id,snippet",
            maxResults=10,
            location=location,
            locationRadius=location_radius,
        )
        .execute()
    )
    videos = [
        search_result
        for search_result in search_response.get("items", [])
        if search_result["id"]["kind"] == "youtube#video"
    ]

    try:
        nexttok = search_response["nextPageToken"]
        return (nexttok, videos)
    except HttpError:
        nexttok = "last_page"
        return (nexttok, videos)
    except KeyError:
        nexttok = "KeyError, try again."
        return (nexttok, videos)


@bot.on(admin_cmd(pattern="insta (.*)"))
@bot.on(sudo_cmd(pattern="insta (.*)", allow_sudo=True))
async def kakashi(event):
    if event.fwd_from:
        return
    chat = "@allsaverbot"
    link = event.pattern_match.group(1)
    if "www.instagram.com" not in link:
        await edit_or_reply(
            event, "` Eu preciso de um link do Instagram para baixar o vídeo...`(*_*)"
        )
    else:
        start = datetime.now()
        catevent = await edit_or_reply(event, "**Baixando...**")
    async with event.client.conversation(chat) as conv:
        try:
            msg_start = await conv.send_message("/start")
            response = await conv.get_response()
            msg = await conv.send_message(link)
            details = await conv.get_response()
            await conv.get_response()
            await conv.get_response()
            video = await conv.get_response()
            await event.client.send_read_acknowledge(conv.chat_id)
        except YouBlockedUserError:
            await catevent.edit("**Erro:** `unblock` @allsaverbot `e tente novamente!`")
            return
        await catevent.delete()
        cat = await event.client.send_file(
            event.chat_id,
            video,
        )
        end = datetime.now()
        ms = (end - start).seconds
        await cat.edit(
            f"<b><i>➥ Vídeo enviado em {ms} segundos.</i></b>\n<b><i>➥ Enviado por :- {hmention}</i></b>",
            parse_mode="html",
        )
    await event.client.delete_messages(
        conv.chat_id, [msg_start.id, response.id, msg.id, details.id, video.id]
    )


CMD_HELP.update(
    {
        "ytdl": "**Plugin :** `ytdl`\
    \n\n  •  **Syntax :** `.yta link`\
    \n  •  **Função : **__Baixa o áudio do link fornecido (suporta todos os sites que suportam youtube-dl)__\
    \n\n  •  **Syntax : **`.ytv link`\
    \n  •  **Função : **__Baixa o vídeo do link fornecido (suporta todos os sites que suportam youtube-dl)__\
    \n\n  •  **Syntax : **`.yts query`\
    \n  •  **Função : **__Busca os resultados do YouTube, você precisa do token de API.__\
    \n\n  •  **Syntax : **`.insta` <link>\
    \n  •  **Função : **__Baixa o vídeo do link do instagram fornecido__\
    "
    }
)
