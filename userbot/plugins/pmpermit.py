import asyncio

from telethon import events, functions

from ..utils import admin_cmd
from . import (
    ALIVE_NAME,
    CMD_HELP,
    PM_START,
    PMMENU,
    PMMESSAGE_CACHE,
    check,
    get_user_from_event,
    parse_pre,
    set_key,
)
from .sql_helper import pmpermit_sql as pmpermit_sql

PM_WARNS = {}
PREV_REPLY_MESSAGE = {}
CACHE = {}
PMPERMIT_PIC = Config.PMPERMIT_PIC
DEFAULTUSER = str(ALIVE_NAME) if ALIVE_NAME else "cat"
USER_BOT_WARN_ZERO = "Spam detectado! Você foi bloqueado automaticamente.. **Aguarde Verificação.** "


if Config.PRIVATE_GROUP_ID is not None:

    @bot.on(admin_cmd(outgoing=True))
    async def you_dm_niqq(event):
        if event.fwd_from:
            return
        chat = await event.get_chat()
        if event.text.startswith((".block", ".disapprove", ".a", ".da", ".approve")):
            return
        if (
            event.is_private
            and not pmpermit_sql.is_approved(chat.id)
            and chat.id not in PM_WARNS
        ):
            pmpermit_sql.approve(chat.id, "outgoing")

    @bot.on(admin_cmd(pattern="(a|approve)(?: |$)(.*)"))
    async def approve_p_m(event):
        if event.is_private:
            user = await event.get_chat()
            reason = event.pattern_match.group(1)
        else:
            user, reason = await get_user_from_event(event, secondgroup=True)
            if not user:
                return await edit_delete(event, "`Não foi possível buscar usuário`", 5)
            if not reason:
                reason = "Não mencionado"
        if not pmpermit_sql.is_approved(user.id):
            if user.id in PM_WARNS:
                del PM_WARNS[user.id]
            if user.id in PREV_REPLY_MESSAGE:
                await PREV_REPLY_MESSAGE[user.id].delete()
                del PREV_REPLY_MESSAGE[user.id]
            if user.id in PM_START:
                PM_START.remove(user.id)
            pmpermit_sql.approve(user.id, reason)
            await edit_delete(
                event,
                f"`PV Aprovado `[{user.first_name}](tg://user?id={user.id})",
                5,
            )
            if user.id in PMMESSAGE_CACHE:
                try:
                    await event.client.delete_messages(
                        user.id, PMMESSAGE_CACHE[user.id]
                    )
                except:
                    pass
        else:
            await edit_delete(
                event,
                f"[{user.first_name}](tg://user?id={user.id}) `já está na lista de aprovados`",
                5,
            )

    @bot.on(admin_cmd(pattern="(da|disapprove)(?: |$)(.*)"))
    async def disapprove_p_m(event):
        if event.is_private:
            user = await event.get_chat()
        else:
            user, reason = await get_user_from_event(event, secondgroup=True)
            if not user:
                return await edit_delete(event, "`Não foi possível buscar usuário`", 5)
            if reason == "all":
                return
        if user.id in PM_START:
            PM_START.remove(user.id)
        if pmpermit_sql.is_approved(user.id):
            pmpermit_sql.disapprove(user.id)
            await edit_or_reply(
                event,
                f"`PV Reprovado` [{user.first_name}](tg://user?id={user.id})",
            )
        else:
            await edit_or_reply(
                event,
                f"[{user.first_name}](tg://user?id={user.id}) `ainda não foi aprovado`",
                5,
            )

    @bot.on(admin_cmd(pattern="block(?: |$)(.*)"))
    async def block_p_m(event):
        if event.is_private:
            user = await event.get_chat()
        else:
            user, reason = await get_user_from_event(event)
            if not user:
                return await edit_delete(event, "`Não foi possível buscar usuário`", 5)
        if user.id in PM_START:
            PM_START.remove(user.id)
        await event.edit(
            f"`Você está bloqueado. Você não podera me enviar mensagens até que eu aprove...`[{user.first_name}](tg://user?id={user.id})"
        )
        await event.client(functions.contacts.BlockRequest(user.id))

    @bot.on(admin_cmd(pattern="unblock(?: |$)(.*)"))
    async def unblock_pm(event):
        if event.is_private:
            user = await event.get_chat()
        else:
            user, reason = await get_user_from_event(event)
            if not user:
                return await edit_delete(event, "`Não foi possível buscar usuário`", 5)
        await event.client(functions.contacts.UnblockRequest(user.id))
        await event.edit(
            f"`Você está desbloqueado. Você pode me enviar mensagens a partir de agora...`[{user.first_name}](tg://user?id={user.id})"
        )

    @bot.on(admin_cmd(pattern="listapproved$"))
    async def approve_p_m(event):
        approved_users = pmpermit_sql.get_all_approved()
        APPROVED_PMs = "Lista de aprovados para PV\n"
        if len(approved_users) > 0:
            for sender in approved_users:
                if sender.reason:
                    APPROVED_PMs += f"👉 [{sender.chat_id}](tg://user?id={sender.chat_id}) for {sender.reason}\n"
                else:
                    APPROVED_PMs += (
                        f"👉 [{sender.chat_id}](tg://user?id={sender.chat_id})\n"
                    )
        else:
            APPROVED_PMs = "`Você ainda não aprovou ninguém`"
        await edit_or_reply(
            event,
            APPROVED_PMs,
            file_name="approvedpms.txt",
            caption="`Lista de aprovados para PV`",
        )

    @bot.on(admin_cmd(pattern="(disapprove all|da all)$"))
    async def disapprove_p_m(event):
        if event.fwd_from:
            return
        result = "`Ok, lista de aprovados resetada.`"
        pmpermit_sql.disapprove_all()
        await edit_delete(event, result, parse_mode=parse_pre, time=10)

    @bot.on(events.NewMessage(incoming=True))
    async def on_new_private_message(event):
        if event.sender_id == event.client.uid:
            return
        if Config.PRIVATE_GROUP_ID is None:
            return
        if not event.is_private:
            return
        chat_id = event.sender_id
        if chat_id in CACHE:
            sender = CACHE[chat_id]
        else:
            sender = await event.get_chat()
            CACHE[chat_id] = sender
        if sender.bot or sender.verified:
            return
        if not pmpermit_sql.is_approved(chat_id):
            await do_pm_permit_action(chat_id, event, sender)

    async def do_pm_permit_action(chat_id, event, sender):
        if chat_id not in PM_WARNS:
            PM_WARNS.update({chat_id: 0})
        if PM_WARNS[chat_id] == Config.MAX_FLOOD_IN_P_M_s:
            r = await event.reply(USER_BOT_WARN_ZERO)
            await asyncio.sleep(1)
            await event.client(functions.contacts.BlockRequest(chat_id))
            if chat_id in PREV_REPLY_MESSAGE:
                await PREV_REPLY_MESSAGE[chat_id].delete()
            if chat_id in PM_START:
                PM_START.remove(chat_id)
            PREV_REPLY_MESSAGE[chat_id] = r
            the_message = f"#BLOCKED_PMs\
                            \n[User](tg://user?id={chat_id}) : {chat_id}\
                            \nMensagens: {PM_WARNS[chat_id]}"
            try:
                await event.client.send_message(
                    entity=Config.PRIVATE_GROUP_ID,
                    message=the_message,
                )
                return
            except BaseException:
                return
        me = await event.client.get_me()
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        my_mention = f"[{me.first_name}](tg://user?id={me.id})"
        first = sender.first_name
        last = sender.last_name
        fullname = f"{first} {last}" if last else first
        username = f"@{sender.username}" if sender.username else mention
        userid = sender.id
        my_first = me.first_name
        my_last = me.last_name
        my_fullname = f"{my_first} {my_last}" if my_last else my_first
        my_username = f"@{me.username}" if me.username else my_mention
        totalwarns = Config.MAX_FLOOD_IN_P_M_s + 1
        warns = PM_WARNS[chat_id] + 1
        if PMMENU:
            if Config.CUSTOM_PMPERMIT_TEXT:
                USER_BOT_NO_WARN = (
                    Config.CUSTOM_PMPERMIT_TEXT.format(
                        mention=mention,
                        first=first,
                        last=last,
                        fullname=fullname,
                        username=username,
                        userid=userid,
                        my_first=my_first,
                        my_last=my_last,
                        my_fullname=my_fullname,
                        my_username=my_username,
                        my_mention=my_mention,
                        totalwarns=totalwarns,
                        warns=warns,
                    )
                    + "\n\n"
                    + "**Agora por favor envie tudo oque precisa dizer em apenas uma mensagem e aguarde até que eu possa ler.**"
                )
            else:

                USER_BOT_NO_WARN = (
                    f"Oi {mention}, Eu ainda não aprovei você para me enviar mensagens no PV. "
                    f"Basta dizer o motivo do contato e esperar até ser aprovado.\
                                    \n\nVocê tem {warns}/{totalwarns} avisos até ser bloqueado automaticamente\
                                    \n\n**Agora por favor envie tudo oque precisa dizer em apenas uma mensagem e aguarde até que eu possa ler.**"
                )
        else:
            if Config.CUSTOM_PMPERMIT_TEXT:
                USER_BOT_NO_WARN = Config.CUSTOM_PMPERMIT_TEXT.format(
                    mention=mention,
                    first=first,
                    last=last,
                    fullname=fullname,
                    username=username,
                    userid=userid,
                    my_first=my_first,
                    my_last=my_last,
                    my_fullname=my_fullname,
                    my_username=my_username,
                    my_mention=my_mention,
                    totalwarns=totalwarns,
                    warns=warns,
                )
            else:
                USER_BOT_NO_WARN = (
                    f"Oi {mention}, Eu ainda não aprovei você para me enviar mensagens no PV.."
                    f"Basta dizer o motivo do contato e esperar até ser aprovado.\
                                    \n\nVocê tem {warns}/{totalwarns} avisos até ser bloqueado automaticamente"
                )
        if PMPERMIT_PIC:
            r = await event.reply(USER_BOT_NO_WARN, file=PMPERMIT_PIC)
        else:
            r = await event.reply(USER_BOT_NO_WARN)
        PM_WARNS[chat_id] += 1
        if chat_id in PREV_REPLY_MESSAGE:
            await PREV_REPLY_MESSAGE[chat_id].delete()
        PREV_REPLY_MESSAGE[chat_id] = r
        return None


CMD_HELP.update(
    {
        "pmpermit": "**Plugin : **`pmpermit`\
        \n\n  •  **Syntax : **`.approve or .a`\
        \n  •  **Função : **__Aprova a pessoa mencionada/respondida ao PV.__\
        \n\n  •  **Syntax : **`.disapprove or .da`\
        \n  •  **Função : **__Reprova a pessoa mencionada/respondida ao PV.__\
        \n\n  •  **Syntax : **`.block`\
        \n  •  **Função : **__Bloquea a pessoa.__\
        \n\n  •  **Syntax : **`.unblock`\
        \n  •  **Função : **__Desbloquea a pessoa.__\
        \n\n  •  **Syntax : **`.listapproved`\
        \n  •  **Função : **__Mostra a lista de aprovados.__\
        \n\n  •  **Syntax : **`.disapprove all or da all`\
        \n  •  **Função : **__Reseta a lista de aprovados.__\
        \n\n  •  Variáveis disponíveis para formatação `CUSTOM_PMPERMIT_TEXT` :\
        \n`{mention}`, `{first}`, `{last} `, `{fullname}`, `{userid}`, `{username}`, `{my_first}`, `{my_fullname}`, `{my_last}`, `{my_mention}`, `{my_username}`,`{warns}` , `{totalwarns}`.\
"
    }
)
