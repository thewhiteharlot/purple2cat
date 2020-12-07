"""
Plug-in para baixar mídia de canal do Telegram para userbot.
usage: .geta channel_username [will  get all media from channel, tho there is limit of 3000 there to prevent API limits.]
       .getc number_of_messsages channel_username
By: @Zero_cool7870
"""
import os
import subprocess

from .. import CMD_HELP
from ..utils import admin_cmd, edit_or_reply, sudo_cmd

location = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "temp")


@bot.on(admin_cmd(pattern=r"getc(?: |$)(.*)"))
@bot.on(sudo_cmd(pattern="getc(?: |$)(.*)", allow_sudo=True))
async def get_media(event):
    if event.fwd_from:
        return
    tempdir = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "temp")
    try:
        os.makedirs(tempdir)
    except BaseException:
        pass
    catty = event.pattern_match.group(1)
    limit = int(catty.split(" ")[0])
    channel_username = str(catty.split(" ")[1])
    event = await edit_or_reply(event, "Baixando mídia deste canal.")
    msgs = await event.client.get_messages(channel_username, limit=int(limit))
    with open("log.txt", "w") as f:
        f.write(str(msgs))
    i = 0
    for msg in msgs:
        if msg.media is not None:
            await event.client.download_media(msg, tempdir)
            i += 1
            await event.edit(
                f"Baixando mídia deste canal B.\n **BAIXADO: **`{i}`"
            )
    ps = subprocess.Popen(("ls", tempdir), stdout=subprocess.PIPE)
    output = subprocess.check_output(("wc", "-l"), stdin=ps.stdout)
    ps.wait()
    output = str(output)
    output = output.replace("b'", " ")
    output = output.replace("\\n'", " ")
    await event.edit(f"Baixado com sucesso {output} número de arquivos de mídia")


@bot.on(admin_cmd(pattern="geta(?: |$)(.*)"))
@bot.on(sudo_cmd(pattern="geta(?: |$)(.*)", allow_sudo=True))
async def get_media(event):
    if event.fwd_from:
        return
    tempdir = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "temp")
    try:
        os.makedirs(tempdir)
    except BaseException:
        pass
    channel_username = event.pattern_match.group(1)
    event = await edit_or_reply(event, "Baixando todas as mídias deste canal.")
    msgs = await event.client.get_messages(channel_username, limit=3000)
    with open("log.txt", "w") as f:
        f.write(str(msgs))
    i = 0
    for msg in msgs:
        if msg.media is not None:
            await event.client.download_media(msg, tempdir)
            i += 1
            await event.edit(
                f"Baixando mídia deste canal.\n **BAIXADO: **`{i}`"
            )
    ps = subprocess.Popen(("ls", tempdir), stdout=subprocess.PIPE)
    output = subprocess.check_output(("wc", "-l"), stdin=ps.stdout)
    ps.wait()
    output = str(output)
    output = output.replace("b'", "")
    output = output.replace("\\n'", "")
    await event.edit(f"Baixado com sucesso {output} número de arquivos de mídia")


CMD_HELP.update(
    {
        "channel_download": f"""**Plugin : **`channel_download`

**Plug-in para baixar mídia de canal do Telegram para userbot.**

  • **Syntax : **`.geta channel_username` 
  • **Função : **__Irá baixar todas as mídias do canal para o servidor do bot, mas há um limite de 3000 para evitar limites de API.__
  
  • **Syntax : **`.getc number channel_username` 
  • **Função : **__Irá baixar o último número determinado de mídia do canal para o seu servidor de bot .__
  
**Observação : **__Os arquivos de mídia baixados estarão em__ `.ls {location}`"""
    }
)
