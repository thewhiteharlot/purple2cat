import time
from platform import python_version

from telethon import version

from ..utils import admin_cmd, edit_or_reply, sudo_cmd
from . import ALIVE_NAME, CMD_HELP, StartTime, catdef, catversion, mention, reply_id

DEFAULTUSER = ALIVE_NAME or "cat"
CAT_IMG = Config.ALIVE_PIC
CUSTOM_ALIVE_TEXT = Config.CUSTOM_ALIVE_TEXT or "✮ FUNCIONANDO NORMALMENTE ✮"
EMOJI = Config.CUSTOM_ALIVE_EMOJI or "  ✥ "


@bot.on(admin_cmd(outgoing=True, pattern="alive$"))
@bot.on(sudo_cmd(pattern="alive$", allow_sudo=True))
async def amireallyalive(alive):
    if alive.fwd_from:
        return
    reply_to_id = await reply_id(alive)
    uptime = await catdef.get_readable_time((time.time() - StartTime))
    _, check_sgnirts = check_data_base_heal_th()
    if CAT_IMG:
        cat_caption = f"**{CUSTOM_ALIVE_TEXT}**\n\n"
        cat_caption += f"**{EMOJI} Database :** `{check_sgnirts}`\n"
        cat_caption += f"**{EMOJI} Versão Telethon:** `{version.__version__}\n`"
        cat_caption += f"**{EMOJI} Versão Catuserbot :** `{catversion}`\n"
        cat_caption += f"**{EMOJI} Versão Python :** `{python_version()}\n`"
        cat_caption += f"**{EMOJI} Uptime :** `{uptime}\n`"
        cat_caption += f"**{EMOJI} Dono:** {mention}\n"
        await alive.client.send_file(
            alive.chat_id, CAT_IMG, caption=cat_caption, reply_to=reply_to_id
        )
        await alive.delete()
    else:
        await edit_or_reply(
            alive,
            f"**{CUSTOM_ALIVE_TEXT}**\n\n"
            f"**{EMOJI} Database :** `{check_sgnirts}`\n"
            f"**{EMOJI} Versão Telethon :** `{version.__version__}\n`"
            f"**{EMOJI} Versão Catuserbot :** `{catversion}`\n"
            f"**{EMOJI} Versão Python :** `{python_version()}\n`"
            f"**{EMOJI} Uptime :** `{uptime}\n`"
            f"**{EMOJI} Dono:** {mention}\n",
        )


@bot.on(admin_cmd(outgoing=True, pattern="ialive$"))
@bot.on(sudo_cmd(pattern="ialive$", allow_sudo=True))
async def amireallyalive(alive):
    if alive.fwd_from:
        return
    tgbotusername = Config.TG_BOT_USER_NAME_BF_HER
    reply_to_id = await reply_id(alive)
    cat_caption = f"**Catuserbot esta instalado e funcionando**\n"
    cat_caption += f"**  -Versao Telethon:** `{version.__version__}\n`"
    cat_caption += f"**  -Versao Catuserbot :** `{catversion}`\n"
    cat_caption += f"**  -Versao Python :** `{python_version()}\n`"
    cat_caption += f"**  -Dono:** {mention}\n"
    results = await bot.inline_query(tgbotusername, cat_caption)  # pylint:disable=E0602
    await results[0].click(alive.chat_id, reply_to=reply_to_id, hide_via=True)
    await alive.delete()


# UniBorg Telegram UseRBot
# Copyright (C) 2020 @UniBorg
# This code is licensed under
# the "you can't use this for anything - public or private,
# unless you know the two prime factors to the number below" license
# 543935563961418342898620676239017231876605452284544942043082635399903451854594062955
# വിവരണം അടിച്ചുമാറ്റിക്കൊണ്ട് പോകുന്നവർ
# ക്രെഡിറ്റ് വെച്ചാൽ സന്തോഷമേ ഉള്ളു..!
# uniborg


def check_data_base_heal_th():
    # https://stackoverflow.com/a/41961968
    is_database_working = False
    output = "Nenhum banco de dados está definido"
    if not Config.DB_URI:
        return is_database_working, output
    from userbot.plugins.sql_helper import SESSION

    try:
        # to check database we will execute raw query
        SESSION.execute("SELECT 1")
    except Exception as e:
        output = f"❌ {str(e)}"
        is_database_working = False
    else:
        output = "OK"
        is_database_working = True
    return is_database_working, output


CMD_HELP.update(
    {
        "alive": "**Plugin :** `alive`\
      \n\n  •  **Syntax : **`.alive` \
      \n  •  **Função : **__status of bot will be showed__\
      \n\n  •  **Syntax : **`.ialive` \
      \n  •  **Função : **__inline status of bot will be shown.__\
      \nSet `ALIVE_PIC` var for media in alive message"
    }
)
