# Userbot module for purging unneeded messages(usually spam or ot).

from asyncio import sleep

from telethon.errors import rpcbaseerrors

from ..utils import admin_cmd, edit_or_reply, errors_handler, sudo_cmd
from . import BOTLOG, BOTLOG_CHATID, CMD_HELP


@bot.on(admin_cmd(outgoing=True, pattern="purge$"))
@bot.on(sudo_cmd(allow_sudo=True, pattern="purge$"))
@errors_handler
async def fastpurger(purg):
    # For .purge command, purge all messages starting from the reply.
    chat = await purg.get_input_chat()
    msgs = []
    itermsg = purg.client.iter_messages(chat, min_id=purg.reply_to_msg_id)
    count = 0

    if purg.reply_to_msg_id is not None:
        async for msg in itermsg:
            msgs.append(msg)
            count += 1
            msgs.append(purg.reply_to_msg_id)
            if len(msgs) == 100:
                await purg.client.delete_messages(chat, msgs)
                msgs = []
    else:
        await edit_or_reply(
            purg,
            "`Nenhuma mensagem especificada.`",
        )
        return

    if msgs:
        await purg.client.delete_messages(chat, msgs)
    done = await purg.client.send_message(
        purg.chat_id,
        "Mensagens apagadas!\nForam apagadas " + str(count) + " mensagens.",
    )

    if BOTLOG:
        await purg.client.send_message(
            BOTLOG_CHATID,
            "#PURGE \nForam apagadas " + str(count) + " mensagens sem erros.",
        )
    await sleep(2)
    await done.delete()


@bot.on(admin_cmd(outgoing=True, pattern="purgeme"))
@bot.on(sudo_cmd(allow_sudo=True, pattern="purgeme"))
@errors_handler
async def purgeme(delme):
    # For .purgeme, delete x count of your latest message.
    message = delme.text
    count = int(message[9:])
    i = 1

    async for message in delme.client.iter_messages(delme.chat_id, from_user="me"):
        if i > count + 1:
            break
        i += 1
        await message.delete()

    smsg = await delme.client.send_message(
        delme.chat_id,
        "`Mensagens apagadas!` Foram apagadas " + str(count) + " mensagens.",
    )
    if BOTLOG:
        await delme.client.send_message(
            BOTLOG_CHATID,
            "#PURGEME \nForam apagadas " + str(count) + " mensagens sem erros.",
        )
    await sleep(2)
    i = 1
    await smsg.delete()


@bot.on(admin_cmd(outgoing=True, pattern="del$"))
@bot.on(sudo_cmd(allow_sudo=True, pattern="del$"))
@errors_handler
async def delete_it(delme):
    """ O comando .del, exclui a mensagem respondida. """
    msg_src = await delme.get_reply_message()
    if delme.reply_to_msg_id:
        try:
            await msg_src.delete()
            await delme.delete()
            if BOTLOG:
                await delme.client.send_message(
                    BOTLOG_CHATID, "#DEL \nA exclusão da mensagem foi bem sucedida"
                )
        except rpcbaseerrors.BadRequestError:
            if BOTLOG:
                await delme.client.send_message(
                    BOTLOG_CHATID, "Bem, eu não posso deletar essa mensagem"
                )


CMD_HELP.update(
    {
        "purge": "**Plugin : **`purge`\
        \n\n**Syntax : **`.purge responda a mensagem para começar a apagar a partir dela`\
        \n**Função : **__Limpa todas as mensagens a partir da respondida.__\
        \n\n**Syntax : **`.purgeme <x>`\
        \n**Função : **__Exclui x quantidade de suas mensagens mais recentes.__\
        \n\n**Syntax : **`.del responda a mensagem para deletar`\
        \n**Função : **__Exclui a mensagem que você respondeu.__"
    }
)
