# Userbot module to help you manage a group

# Copyright (C) 2019 The Raphielscape Company LLC.
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

from asyncio import sleep

from telethon import functions
from telethon.errors import (
    BadRequestError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
)
from telethon.errors.rpcerrorlist import UserAdminInvalidError, UserIdInvalidError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChatAdminRights, ChatBannedRights, MessageMediaPhoto

from ..utils import admin_cmd, edit_or_reply, errors_handler, sudo_cmd
from . import BOTLOG, BOTLOG_CHATID, CMD_HELP, LOGS, get_user_from_event
from .sql_helper.mute_sql import is_muted, mute, unmute

# =================== CONSTANT ===================

PP_TOO_SMOL = "`A imagem é muito pequena`"
PP_ERROR = "`Falha ao processar a imagem`"
NO_ADMIN = "`Eu não sou um admin!`"
NO_PERM = "`Eu não tenho permissões suficientes!`"
CHAT_PP_CHANGED = "`Imagem do bate-papo alterada`"
INVALID_MEDIA = "`Extensão Inválida`"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)
UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)

# ================================================


@bot.on(admin_cmd(pattern="setgpic$"))
@bot.on(sudo_cmd(pattern="setgpic$", allow_sudo=True))
@errors_handler
async def set_group_photo(gpic):
    if gpic.fwd_from:
        return
    if not gpic.is_group:
        await edit_or_reply(gpic, "`Não acho que seja um grupo.`")
        return
    replymsg = await gpic.get_reply_message()
    chat = await gpic.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    photo = None
    if not admin and not creator:
        await edit_or_reply(gpic, NO_ADMIN)
        return
    if replymsg and replymsg.media:
        if isinstance(replymsg.media, MessageMediaPhoto):
            photo = await gpic.client.download_media(message=replymsg.photo)
        elif "image" in replymsg.media.document.mime_type.split("/"):
            photo = await gpic.client.download_file(replymsg.media.document)
        else:
            await edit_or_reply(gpic, INVALID_MEDIA)
    sandy = None
    if photo:
        try:
            await gpic.client(
                EditPhotoRequest(gpic.chat_id, await gpic.client.upload_file(photo))
            )
            await edit_or_reply(gpic, CHAT_PP_CHANGED)
            sandy = True
        except PhotoCropSizeSmallError:
            await edit_or_reply(gpic, PP_TOO_SMOL)
        except ImageProcessFailedError:
            await edit_or_reply(gpic, PP_ERROR)
        except Exception as e:
            await edit_or_reply(gpic, f"**Erro: **`{str(e)}`")
        if BOTLOG and sandy:
            await gpic.client.send_message(
                BOTLOG_CHATID,
                "#GROUPPIC\n"
                f"Foto do perfil do grupo alterada "
                f"CHAT: {gpic.chat.title}(`{gpic.chat_id}`)",
            )


@bot.on(admin_cmd(pattern="promote(?: |$)(.*)", command="promote"))
@bot.on(sudo_cmd(pattern="promote(?: |$)(.*)", command="promote", allow_sudo=True))
@errors_handler
async def promote(promt):
    if promt.fwd_from:
        return
    chat = await promt.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    if not admin and not creator:
        await edit_or_reply(promt, NO_ADMIN)
        return
    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )
    catevent = await edit_or_reply(promt, "`Promovendo...`")
    user, rank = await get_user_from_event(promt)
    if not rank:
        rank = "Admin"
    if not user:
        return
    try:
        await promt.client(EditAdminRequest(promt.chat_id, user.id, new_rights, rank))
        await catevent.edit("`Promovido com sucesso!`")
    except BadRequestError:
        await catevent.edit(NO_PERM)
        return
    if BOTLOG:
        await promt.client.send_message(
            BOTLOG_CHATID,
            "#PROMOTE\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {promt.chat.title}(`{promt.chat_id}`)",
        )


@bot.on(admin_cmd(pattern="demote(?: |$)(.*)", command="demote"))
@bot.on(sudo_cmd(pattern="demote(?: |$)(.*)", command="demote", allow_sudo=True))
@errors_handler
async def demote(dmod):
    if dmod.fwd_from:
        return
    chat = await dmod.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    if not admin and not creator:
        await edit_or_reply(dmod, NO_ADMIN)
        return
    catevent = await edit_or_reply(dmod, "`Rebaixando...`")
    rank = "admeme"
    user = await get_user_from_event(dmod)
    user = user[0]
    if not user:
        return
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    try:
        await dmod.client(EditAdminRequest(dmod.chat_id, user.id, newrights, rank))
    except BadRequestError:
        await catevent.edit(NO_PERM)
        return
    await catevent.edit("`Rebaixado com sucesso! Mais sorte da próxima vez`")
    if BOTLOG:
        await dmod.client.send_message(
            BOTLOG_CHATID,
            "#DEMOTE\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {dmod.chat.title}(`{dmod.chat_id}`)",
        )


@bot.on(admin_cmd(pattern="ban(?: |$)(.*)", command="ban"))
@bot.on(sudo_cmd(pattern="ban(?: |$)(.*)", command="ban", allow_sudo=True))
@errors_handler
async def ban(bon):
    if bon.fwd_from:
        return
    chat = await bon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    if not admin and not creator:
        await edit_or_reply(bon, NO_ADMIN)
        return
    user, reason = await get_user_from_event(bon)
    if not user:
        return
    catevent = await edit_or_reply(bon, "`Acabando com a praga!`")
    try:
        await bon.client(EditBannedRequest(bon.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        await catevent.edit(NO_PERM)
        return
    try:
        reply = await bon.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        await catevent.edit(
            "`Eu não tenho direitos de detonação de mensagens! Mas ele ainda está banido!`"
        )
        return
    if reason:
        await catevent.edit(f"`{str(user.id)}` está banido !!\nMotivo: {reason}")
    else:
        await catevent.edit(f"`{str(user.id)}` está banido !!")
    if BOTLOG:
        await bon.client.send_message(
            BOTLOG_CHATID,
            "#BAN\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {bon.chat.title}(`{bon.chat_id}`)",
        )


@bot.on(admin_cmd(pattern="unban(?: |$)(.*)", command="unban"))
@bot.on(sudo_cmd(pattern="unban(?: |$)(.*)", command="unban", allow_sudo=True))
@errors_handler
async def nothanos(unbon):
    if unbon.fwd_from:
        return
    chat = await unbon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    if not admin and not creator:
        await edit_or_reply(unbon, NO_ADMIN)
        return
    catevent = await edit_or_reply(unbon, "`Desbanindo...`")
    user = await get_user_from_event(unbon)
    user = user[0]
    if not user:
        return
    try:
        await unbon.client(EditBannedRequest(unbon.chat_id, user.id, UNBAN_RIGHTS))
        await catevent.edit("```Desbanido com sucesso. Teve outra chance.```")
        if BOTLOG:
            await unbon.client.send_message(
                BOTLOG_CHATID,
                "#UNBAN\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {unbon.chat.title}(`{unbon.chat_id}`)",
            )
    except UserIdInvalidError:
        await catevent.edit("`Ops alguma coisa não saiu como planejado!`")


@bot.on(admin_cmd(incoming=True))
async def watcher(event):
    if is_muted(event.sender_id, event.chat_id):
        try:
            await event.delete()
        except Exception as e:
            LOGS.info(str(e))


@bot.on(admin_cmd(pattern="mute(?: |$)(.*)", command="mute"))
@bot.on(sudo_cmd(pattern="mute(?: |$)(.*)", command="mute", allow_sudo=True))
async def startmute(event):
    if event.fwd_from:
        return
    if event.is_private:
        await event.edit("Podem ocorrer problemas inesperados ou erros!")
        await sleep(3)
        await event.get_reply_message()
        userid = event.chat_id
        replied_user = await event.client(GetFullUserRequest(userid))
        chat_id = event.chat_id
        if is_muted(userid, chat_id):
            return await event.edit(
                "Este usuário já está silenciado neste chat."
            )
        try:
            mute(userid, chat_id)
        except Exception as e:
            await event.edit("Ocorreu um erro!\nErro é " + str(e))
        else:
            await event.edit("Essa pessoa foi silenciada com sucesso.\n**｀-´)⊃━☆ﾟ.*･｡ﾟ **")
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#PM_MUTE\n"
                f"USER: [{replied_user.user.first_name}](tg://user?id={userid})\n"
                f"CHAT: {event.chat.title}(`{event.chat_id}`)",
            )
    else:
        chat = await event.get_chat()
        user, reason = await get_user_from_event(event)
        if not user:
            return
        if user.id == bot.uid:
            return await edit_or_reply(event, "Desculpe, não consigo me silenciar🤭")
        if is_muted(user.id, event.chat_id):
            return await edit_or_reply(
                event, "Este usuário já está silenciado neste chat."
            )
        try:
            admin = chat.admin_rights
            creator = chat.creator
            if not admin and not creator:
                await edit_or_reply(
                    event, "`Você não pode silenciar uma pessoa sem direitos de administrador.` ಥ﹏ಥ  "
                )
                return
            result = await event.client(
                functions.channels.GetParticipantRequest(
                    channel=event.chat_id, user_id=user.id
                )
            )
            try:
                if result.participant.banned_rights.send_messages:
                    return await edit_or_reply(
                        event,
                        "Este usuário já está silenciado neste chat.",
                    )
            except:
                pass
            await event.client(EditBannedRequest(event.chat_id, user.id, MUTE_RIGHTS))
        except UserAdminInvalidError:
            if "admin_rights" in vars(chat) and vars(chat)["admin_rights"] is not None:
                if chat.admin_rights.delete_messages is not True:
                    return await edit_or_reply(
                        event,
                        "`Você não pode silenciar uma pessoa se não tiver permissão para excluir mensagens. ಥ﹏ಥ`",
                    )
            elif "creator" not in vars(chat):
                return await edit_or_reply(
                    event, "`Você não pode silenciar uma pessoa sem direitos de administrador.` ಥ﹏ಥ  "
                )
            try:
                mute(user.id, event.chat_id)
            except Exception as e:
                return await edit_or_reply(event, "Ocorreu um erro!\nErro é " + str(e))
        except Exception as e:
            return await edit_or_reply(event, f"**Erro: **`{str(e)}`")
        if reason:
            await edit_or_reply(
                event,
                f"{user.first_name} está silenciado em {event.chat.title}\n"
                f"`Motivo:`{reason}",
            )
        else:
            await edit_or_reply(
                event, f"{user.first_name} está silenciado em {event.chat.title}"
            )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#MUTE\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {event.chat.title}(`{event.chat_id}`)",
            )


@bot.on(admin_cmd(pattern="unmute(?: |$)(.*)", command="unmute"))
@bot.on(sudo_cmd(pattern="unmute(?: |$)(.*)", command="unmute", allow_sudo=True))
async def endmute(event):
    if event.fwd_from:
        return
    if event.is_private:
        await event.edit("Podem ocorrer problemas inesperados ou erros!")
        await sleep(3)
        userid = event.chat_id
        replied_user = await event.client(GetFullUserRequest(userid))
        chat_id = event.chat_id
        if not is_muted(userid, chat_id):
            return await event.edit(
                "__Este usuário não está silenciado neste chat__\n（ ^_^）o自自o（^_^ ）"
            )
        try:
            unmute(userid, chat_id)
        except Exception as e:
            await event.edit("Ocorreu um erro!\nErro é " + str(e))
        else:
            await event.edit("Mutado com sucesso\n乁( ◔ ౪◔)「    ┑(￣Д ￣)┍")
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#UNMUTE\n"
                f"USER: [{replied_user.user.first_name}](tg://user?id={userid})\n"
                f"CHAT: {event.chat.title}(`{event.chat_id}`)",
            )
    else:
        user = await get_user_from_event(event)
        user = user[0]
        if not user:
            return
        try:
            if is_muted(user.id, event.chat_id):
                unmute(user.id, event.chat_id)
            else:
                result = await event.client(
                    functions.channels.GetParticipantRequest(
                        channel=event.chat_id, user_id=user.id
                    )
                )
                try:
                    if result.participant.banned_rights.send_messages:
                        await event.client(
                            EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS)
                        )
                except:
                    return await edit_or_reply(
                        event,
                        "Este usuário já pode falar livremente neste chat",
                    )
        except Exception as e:
            return await edit_or_reply(event, f"**Erro: **`{str(e)}`")
        await edit_or_reply(
            event, "Mutado com sucesso\n乁( ◔ ౪◔)「    ┑(￣Д ￣)┍"
        )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#UNMUTE\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {event.chat.title}(`{event.chat_id}`)",
            )


@bot.on(admin_cmd(pattern="pin($| (.*))", command="pin"))
@bot.on(sudo_cmd(pattern="pin($| (.*))", command="pin", allow_sudo=True))
@errors_handler
async def pin(msg):
    if msg.fwd_from:
        return
    if not msg.is_private:
        chat = await msg.get_chat()
        admin = chat.admin_rights
        creator = chat.creator
        if not admin and not creator:
            return await edit_delete(msg, NO_ADMIN, 5)
    to_pin = msg.reply_to_msg_id
    if not to_pin:
        return await edit_delete(msg, "`Responda a uma mensagem para fixá-la.`", 5)
    options = msg.pattern_match.group(1)
    is_silent = False
    if options == "loud":
        is_silent = True
    try:
        await msg.client.pin_message(msg.chat_id, to_pin, notify=is_silent)
    except BadRequestError:
        return await edit_delete(msg, NO_PERM, 5)
    except Exception as e:
        return await edit_delete(msg, f"`{str(e)}`", 5)
    await edit_delete(msg, "`Fixado com sucesso!`", 3)
    user = await get_user_from_id(msg.sender_id, msg)
    if BOTLOG and not msg.is_private:
        try:
            await msg.client.send_message(
                BOTLOG_CHATID,
                "#PIN\n"
                f"ADMIN: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {msg.chat.title}(`{msg.chat_id}`)\n"
                f"LOUD: {is_silent}",
            )
        except:
            pass


@bot.on(admin_cmd(pattern="unpin($| (.*))", command="unpin"))
@bot.on(sudo_cmd(pattern="unpin($| (.*))", command="unpin", allow_sudo=True))
@errors_handler
async def pin(msg):
    if msg.fwd_from:
        return
    if not msg.is_private:
        chat = await msg.get_chat()
        admin = chat.admin_rights
        creator = chat.creator
        if not admin and not creator:
            await edit_delete(msg, NO_ADMIN, 5)
            return
    to_unpin = msg.reply_to_msg_id
    options = (msg.pattern_match.group(1)).strip()
    if not to_unpin and options != "all":
        await edit_delete(msg, "`Responda a uma mensagem para desafixar ou usar .unpin all`", 5)
        return
    if to_unpin and not options:
        try:
            await msg.client.unpin_message(msg.chat_id, to_unpin)
        except BadRequestError:
            return await edit_delete(msg, NO_PERM, 5)
        except Exception as e:
            return await edit_delete(msg, f"`{str(e)}`", 5)
    elif options == "all":
        try:
            await msg.client.unpin_message(msg.chat_id)
        except BadRequestError:
            return await edit_delete(msg, NO_PERM, 5)
        except Exception as e:
            return await edit_delete(msg, f"`{str(e)}`", 5)
    else:
        return await edit_delete(
            msg, "`Responda a uma mensagem para desafixar ou usar .unpin all`", 5
        )
    await edit_delete(msg, "`Desafixado com sucesso!`", 3)
    user = await get_user_from_id(msg.sender_id, msg)
    if BOTLOG and not msg.is_private:
        try:
            await msg.client.send_message(
                BOTLOG_CHATID,
                "#UNPIN\n"
                f"**Admin : **[{user.first_name}](tg://user?id={user.id})\n"
                f"**Chat : **{msg.chat.title}(`{msg.chat_id}`)\n",
            )
        except:
            pass


@bot.on(admin_cmd(pattern="kick(?: |$)(.*)", command="kick"))
@bot.on(sudo_cmd(pattern="kick(?: |$)(.*)", command="kick", allow_sudo=True))
@errors_handler
async def kick(usr):
    if usr.fwd_from:
        return
    chat = await usr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    if not admin and not creator:
        await edit_or_reply(usr, NO_ADMIN)
        return
    user, reason = await get_user_from_event(usr)
    if not user:
        await edit_or_reply(usr, "`Não foi possível buscar o usuário.`")
        return
    catevent = await edit_or_reply(usr, "`Chutando...`")
    try:
        await usr.client.kick_participant(usr.chat_id, user.id)
        await sleep(0.5)
    except Exception as e:
        await catevent.edit(NO_PERM + f"\n{str(e)}")
        return
    if reason:
        await catevent.edit(
            f"`Chutado` [{user.first_name}](tg://user?id={user.id})`!`\nMotivo: {reason}"
        )
    else:
        await catevent.edit(f"`Chutado` [{user.first_name}](tg://user?id={user.id})`!`")
    if BOTLOG:
        await usr.client.send_message(
            BOTLOG_CHATID,
            "#KICK\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {usr.chat.title}(`{usr.chat_id}`)\n",
        )


@bot.on(admin_cmd(pattern="iundlt$", command="iundlt"))
@bot.on(sudo_cmd(pattern="iundlt$", command="iundlt", allow_sudo=True))
async def _(event):
    if event.fwd_from:
        return
    c = await event.get_chat()
    if c.admin_rights or c.creator:
        a = await event.client.get_admin_log(
            event.chat_id, limit=5, edit=False, delete=True
        )
        deleted_msg = "Mensagem excluída neste grupo:"
        for i in a:
            deleted_msg += "\n👉`{}`".format(i.old.message)
        await edit_or_reply(event, deleted_msg)
    else:
        await edit_or_reply(
            event, "`Você precisa de permissões administrativas para fazer este comando`"
        )
        await sleep(3)
        try:
            await event.delete()
        except:
            pass


async def get_user_from_id(user, event):
    if isinstance(user, str):
        user = int(user)
    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        await event.edit(str(err))
        return None
    return user_obj


CMD_HELP.update(
    {
        "admin": "**Plugin : **`admin`\
        \n\n  •  **Syntax : **`.setgpic` <reply to image>\
        \n  •  **Uso: **Muda a imagem de exibição do grupo\
        \n\n  •  **Syntax : **`.promote` <username/reply> <rank (opcional)>\
        \n  •  **Uso: **Concede direitos de administrador para a pessoa no chat.\
        \n\n  •  **Syntax : **`.demote `<username/reply>\
        \n  •  **Uso: **Revoga as permissões de administrador da pessoa no chat.\
        \n\n  •  **Syntax : **`.ban` <username/reply> <motivo (opcional)>\
        \n  •  **Uso: **Bane a pessoa do seu chat.\
        \n\n  •  **Syntax : **`.unban` <username/reply>\
        \n  •  **Uso: **Remove o banimento da pessoa no chat.\
        \n\n  •  **Syntax : **`.mute` <username/reply> <motivo (opcional)>\
        \n  •  **Uso: **Silencia a pessoa no chat, também trabalha com administradores.\
        \n\n  •  **Syntax : **`.unmute` <username/reply>\
        \n  •  **Uso: **Remove a pessoa da lista de silenciados.\
        \n\n  •  **Syntax : **`.pin `<reply> or `.pin loud`\
        \n  •  **Uso: **Fixa a mensagem respondida no grupo\
        \n\n  •  **Syntax : **`.unpin `<reply> or `.unpin all`\
        \n  •  **Uso: **Libera a mensagem respondida no grupo\
        \n\n  •  **Syntax : **`.kick `<username/reply> \
        \n  •  **Uso: **Chuta a pessoa para fora do seu chat.\
        \n\n  •  **Syntax : **`.iundlt`\
        \n  •  **Uso: **Exibir as últimas 5 mensagens excluídas no grupo."
    }
)
