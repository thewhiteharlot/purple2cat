# Copyright (C) 2019 The Raphielscape Company LLC.
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
# credits to @AvinashReddy3108
"""
This module updates the userbot based on upstream revision
Ported from Kensurbot
"""
import asyncio
import sys
from os import environ, execle, path, remove

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from ..utils import admin_cmd, edit_or_reply, sudo_cmd
from . import CMD_HELP, runcmd

HEROKU_APP_NAME = Config.HEROKU_APP_NAME or None
HEROKU_API_KEY = Config.HEROKU_API_KEY or None
UPSTREAM_REPO_BRANCH = Config.UPSTREAM_REPO_BRANCH
UPSTREAM_REPO_URL = Config.UPSTREAM_REPO_URL

requirements_path = path.join(
    path.dirname(path.dirname(path.dirname(__file__))), "requirements.txt"
)


async def gen_chlog(repo, diff):
    ch_log = ""
    d_form = "%d/%m/%y"
    for c in repo.iter_commits(diff):
        ch_log += (
            f"  • {c.summary} ({c.committed_datetime.strftime(d_form)}) <{c.author}>\n"
        )
    return ch_log


async def print_changelogs(event, ac_br, changelog):
    changelog_str = (
        f"**Nova ATUALIZAÇÃO disponível para [{ac_br}]:\n\nCHANGELOG:**\n`{changelog}`"
    )
    if len(changelog_str) > 4096:
        await event.edit("`O registro de alterações é muito grande, visualize o arquivo para vê-lo.`")
        with open("output.txt", "w+") as file:
            file.write(changelog_str)
        await event.client.send_file(
            event.chat_id,
            "output.txt",
            reply_to=event.id,
        )
        remove("output.txt")
    else:
        await event.client.send_message(
            event.chat_id,
            changelog_str,
            reply_to=event.id,
        )
    return True


async def update_requirements():
    reqs = str(requirements_path)
    try:
        process = await asyncio.create_subprocess_shell(
            " ".join([sys.executable, "-m", "pip", "install", "-r", reqs]),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode
    except Exception as e:
        return repr(e)


async def deploy(event, repo, ups_rem, ac_br, txt):
    if HEROKU_API_KEY is not None:
        import heroku3

        heroku = heroku3.from_key(HEROKU_API_KEY)
        heroku_app = None
        heroku_applications = heroku.apps()
        if HEROKU_APP_NAME is None:
            await event.edit(
                "`Por favor, configure o` **HEROKU_APP_NAME** `Var`"
                " para ser capaz de implantar seu userbot...`"
            )
            repo.__del__()
            return
        for app in heroku_applications:
            if app.name == HEROKU_APP_NAME:
                heroku_app = app
                break
        if heroku_app is None:
            await event.edit(
                f"{txt}\n" "`Credenciais Heroku inválidas para implantação de userbot dyno.`"
            )
            return repo.__del__()
        await event.edit(
            "`Userbot dyno build em progresso, pode levar até 7 minutos.`"
        )
        ups_rem.fetch(ac_br)
        repo.git.reset("--hard", "FETCH_HEAD")
        heroku_git_url = heroku_app.git_url.replace(
            "https://", "https://api:" + HEROKU_API_KEY + "@"
        )
        if "heroku" in repo.remotes:
            remote = repo.remote("heroku")
            remote.set_url(heroku_git_url)
        else:
            remote = repo.create_remote("heroku", heroku_git_url)
        try:
            remote.push(refspec="HEAD:refs/heads/master", force=True)
        except Exception as error:
            await event.edit(f"{txt}\n`Aqui está o log de erros:\n{error}`")
            return repo.__del__()
        build = app.builds(order_by="created_at", sort="desc")[0]
        if build.status == "failed":
            await event.edit(
                "`Falha na construção!\n" "Cancelado ou ocorreram alguns erros...`"
            )
            await asyncio.sleep(5)
            return await event.delete()
        await event.edit("`Implantado com sucesso!\n" "Reiniciando, por favor aguarde...`")
    else:
        await event.edit("`Por favor configure`  **HEROKU_API_KEY**  ` Var...`")
    return


async def update(event, repo, ups_rem, ac_br):
    try:
        ups_rem.pull(ac_br)
    except GitCommandError:
        repo.git.reset("--hard", "FETCH_HEAD")
    await update_requirements()
    await event.edit(
        "`Atualizado com sucesso!\n" "O bot está reiniciando... Espere um minuto!`"
    )
    # Spin a new instance of bot
    args = [sys.executable, "-m", "userbot"]
    execle(sys.executable, *args, environ)
    return


@bot.on(admin_cmd(outgoing=True, pattern=r"update($| (now|deploy))"))
@bot.on(sudo_cmd(pattern="update($| (now|deploy))", allow_sudo=True))
async def upstream(event):
    "O comando .update, verifica se o bot está atualizado"
    conf = event.pattern_match.group(1).strip()
    event = await edit_or_reply(event, "`Verificando atualizações, por favor aguarde...`")
    off_repo = UPSTREAM_REPO_URL
    force_update = False
    if HEROKU_API_KEY is None or HEROKU_APP_NAME is None:
        return await edit_or_reply(
            event, "`Defina as vars necessárias primeiro para atualizar o bot`"
        )
    try:
        txt = "`Ops.. O atualizador não pode continuar devido a "
        txt += "alguns problemas ocorreram`\n\n**LOGTRACE:**\n"
        repo = Repo()
    except NoSuchPathError as error:
        await event.edit(f"{txt}\n`diretório {error} Não foi encontrado`")
        return repo.__del__()
    except GitCommandError as error:
        await event.edit(f"{txt}\n`Falha precoce! {error}`")
        return repo.__del__()
    except InvalidGitRepositoryError as error:
        if conf is None:
            return await event.edit(
                f"`Infelizmente, o diretório {error} "
                "não parece ser um repositório git.\n"
                "Mas podemos consertar isso ao forçar a atualização do userbot usando "
                ".update now.`"
            )
        repo = Repo.init()
        origin = repo.create_remote("upstream", off_repo)
        origin.fetch()
        force_update = True
        repo.create_head("master", origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)
    ac_br = repo.active_branch.name
    if ac_br != UPSTREAM_REPO_BRANCH:
        await event.edit(
            "**[ATUALIZADOR]:**\n"
            f"`Parece que você está usando seu próprio branch personalizado ({ac_br}). "
            "nesse caso, o Updater não consegue identificar "
            "qual ramo deve ser fundido. "
            "por favor, verifique em qualquer branch oficial`"
        )
        return repo.__del__()
    try:
        repo.create_remote("upstream", off_repo)
    except BaseException:
        pass
    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)
    changelog = await gen_chlog(repo, f"HEAD..upstream/{ac_br}")
    # Special case for deploy
    if conf == "deploy":
        await event.edit("`Implantando userbot, aguarde...`")
        await deploy(event, repo, ups_rem, ac_br, txt)
        return
    if changelog == "" and not force_update:
        await event.edit(
            "\n`CATUSERBOT está`  **ATUALIZADO**  `com`  "
            f"**{UPSTREAM_REPO_BRANCH}**\n"
        )
        return repo.__del__()
    if conf == "" and not force_update:
        await print_changelogs(event, ac_br, changelog)
        await event.delete()
        return await event.respond(
            'Envie "[`.update now`] ou [`.update deploy`]" para atualizar. Cheque `.info updater` para detalhes'
        )

    if force_update:
        await event.edit(
            "`Forçar a sincronização com o código do userbot estável mais recente, aguarde...`"
        )
    if conf == "now":
        await event.edit("`Atualizando userbot, por favor aguarde...`")
        await update(event, repo, ups_rem, ac_br)
    return


CMD_HELP.update(
    {
        "updater": "**Plugin : **`updater`"
        "\n\n  •  **Syntax : **`.update`"
        "\n  •  **Função :** Verifica se o repositório principal do userbot tem alguma atualização "
        "e mostra um changelog se assim for."
        "\n\n  •  **Syntax : **`.update now`"
        "\n  •  **Função :** Atualize seu userbot, "
        "se houver alguma atualização no repositório do userbot. Se você reiniciar, voltará para a última vez quando você implantou"
        "\n\n  •  **Syntax : **`.update deploy`"
        "\n  •  **Função :** Implante seu userbot. Então, mesmo que você reinicie, ele não volta para a versão anterior"
        "\nIsso acionará a implantação sempre, mesmo sem atualizações."
    }
)
