import html
import re
from typing import Optional, List
from requests import get
from datetime import datetime
from html import escape

from telegram import (
    Message,
    Chat,
    MessageEntity,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ParseMode,
    ChatAction,
    TelegramError,
)
from telegram.ext import CommandHandler, CallbackQueryHandler, Filters
from telegram.utils.helpers import (
    escape_markdown,
    mention_html,
    mention_markdown,
)
from telegram.error import BadRequest

from perry import (
    dispatcher,
    OWNER_ID,
    TOKEN,
    SUDO_USERS,
)
from perry.modules.helper_funcs.alternate import typing_action, send_action
from perry.modules.disable import DisableAbleCommandHandler


@typing_action
def gitstats(update, context):
    message = update.effective_message
    args = context.args
    text = " ".join(args).lower()
    usr = get(f"https://api.github.com/users/{text}").json()
    if len(args) >= 1:
        try:
            text = f"*Username:* [{usr['login']}](https://github.com/{usr['login']})"

            whitelist = [
                "name",
                "id",
                "type",
                "location",
                "blog",
                "bio",
                "followers",
                "following",
                "hireable",
                "public_gists",
                "public_repos",
                "email",
                "company",
                "updated_at",
                "created_at",
            ]

            rename = {
                "id": "Account ID",
                "type": "Account type",
                "created_at": "Account created at",
                "updated_at": "Last updated",
                "public_repos": "Public Repos",
                "public_gists": "Public Gists",
            }

            empty = [None, 0, "null", ""]

            for x, y in usr.items():
                if x in whitelist:
                    x = rename.get(x, x.title())

                    if x in ["Account created at", "Last updated"]:
                        y = datetime.strptime(y, "%Y-%m-%dT%H:%M:%SZ")

                    if y not in empty:
                        if x == "Blog":
                            x = "Website"
                            y = f"[Here!]({y})"
                            text += "\n*{}:* {}".format(x, y)
                        else:
                            text += "\n*{}:* `{}`".format(x, y)

            chat = update.effective_chat
            dispatcher.bot.send_photo(
                "{}".format(chat.id),
                f"{usr['html_url']}",
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                # disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=f"{usr['login']}'s profile",
                                url=f"{usr['html_url']}",
                            )
                        ]
                    ]
                ),
            )
        except KeyError:
            return message.reply_text(
                "*User/Organization not found!* \nMake sure to enter a valid username.",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        message.reply_text("Enter the GitHub username you want stats for!")


@typing_action
def repo(update, context):
    message = update.effective_message
    args = message.text.split(None, 2)[1:]
    text = ""

    # handle args
    if len(args) == 0:
        return message.reply_text(
            "Enter someone's GitHub username to view their repos or get repo data with username and repo name!"
        )
    elif len(args) == 1:
        user = args[0]
        usr_data = get(
            f"https://api.github.com/users/{user}/repos?per_page=40"
        ).json()

        if len(usr_data) != 0:
            reply_text = f"*{user}*" + f"'s" + "* Repos:*\n"
            for i in range(len(usr_data)):
                reply_text += (
                    f"- [{usr_data[i]['name']}]({usr_data[i]['html_url']})\n"
                )
            message.reply_text(
                reply_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        else:
            return message.reply_text(
                "*User/Organization not found!* \nMake sure to enter a valid username.",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        user, repo = args
        rep_data = get(f"https://api.github.com/repos/{user}/{repo}").json()
        brc_data = get(
            f"https://api.github.com/repos/{user}/{repo}/branches"
        ).json()
        try:
            text = f"*Repo name:* {rep_data['full_name']}"
            text += f"\n*Language*: {rep_data['language']}"
            if f"{rep_data['license']}" != "null":
                licensePlate = rep_data["license"]["name"]
            else:
                licensePlate = rep_data["license"]
            text += f"\n*License*: `{licensePlate}`"

            whitelist = [
                "description",
                "id",
                "homepage",
                "archived",
                "updated_at",
                "created_at",
                "open_issues",
            ]

            rename = {
                "id": "Repo ID",
                "created_at": "Created date",
                "updated_at": "Last updated",
                "open_issues": "Open issues",
            }

            empty = [None, "null", "", False]

            for x, y in rep_data.items():
                if x in whitelist:

                    x = rename.get(x, x.title())

                    if x in ["Created date", "Last updated"]:
                        y = datetime.strptime(y, "%Y-%m-%dT%H:%M:%SZ")

                    if y not in empty:
                        if x == "Homepage":
                            y = f"[Here!]({y})"
                        elif x in [
                            "Created date",
                            "Last updated",
                            "Description",
                        ]:
                            text += f"\n*{x}:* \n`{y}`"
                        else:
                            text += f"\n*{x}:* `{y}`"

            count = 0
            for i in range(len(brc_data)):
                count += 1
            text += f"\n*Branches:* `{count}`"
            text += f"\n*🍴 Forks:* `{rep_data['forks_count']}` | *🌟 Stars:* `{rep_data['stargazers_count']}` "

            chat = update.effective_chat
            dispatcher.bot.send_photo(
                "{}".format(chat.id),
                f"{rep_data['html_url']}",
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Repo link", url=f"{rep_data['html_url']}"
                            ),
                            InlineKeyboardButton(
                                text="Issues",
                                url=f"https://github.com/{user}/{repo}/issues",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="Pull Requests",
                                url=f"https://github.com/{user}/{repo}/pulls",
                            ),
                            InlineKeyboardButton(
                                text="Commits",
                                url=f"https://github.com/{user}/{repo}/commits/{rep_data['default_branch']}",
                            ),
                        ],
                        # [
                        #     InlineKeyboardButton(
                        #         text="Clone",
                        #         callback_data=f"cloneMessage_{user.id, user, repo}",
                        #     ),
                        #     InlineKeyboardButton(
                        #         text="Branch",
                        #         callback_data=f"branchMessage_{user.id, user, repo}",
                        #     ),
                        # ],
                    ]
                ),
            )
        except KeyError:
            return message.reply_text(
                "*User/Organization not found!* \nMake sure to enter a valid username.",
                parse_mode=ParseMode.MARKDOWN,
            )


@typing_action
def gitclone(update, context):
    """
    Allows one to download zip of a repo directly through Telegram (max 2gb).
    """
    message = update.effective_message
    args = message.text.split(None, 3)[1:]
    text = ""

    if len(args) == 3:
        user, repo, branch = args
        url = get(f"https://github.com/{user}/{repo}/tree/{branch}")
        if url.status_code == 404:
            return message.reply_text(
                "*Username, repository name or branch not found!*",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            data = get(f"https://api.github.com/repos/{user}/{repo}").json()
            # https://api.github.com/repos/{user}/{repo}/zipball/{branch}
            archive = f"https://github.com/{user}/{repo}/archive/{branch}.zip"
    elif len(args) == 2:
        try:
            user, repo = args
            data = get(f"https://api.github.com/repos/{user}/{repo}").json()
            archive = f"https://github.com/{user}/{repo}/archive/{data['default_branch']}.zip"
            text += "Branch not specified, default branch used.\n\n"
            branch = f"{data['default_branch']}"
        except KeyError:
            return message.reply_text(
                "*Username or repository name not found!*",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        return message.reply_text(
            "*You did not fufill the requirements!* \nSpecify the data needed: username, repository name and branch (optional).",
            parse_mode=ParseMode.MARKDOWN,
        )

    try:
        text += f"*Repo*: {data['name']} - {branch} branch. \n*HTTPS*:\n`{data['clone_url']}` \n*SSH*:\n`{data['ssh_url']}` \n*Zip*: {archive}"
        message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except KeyError:
        return message.reply_text(
            "*Username or repository name not found!*",
            parse_mode=ParseMode.MARKDOWN,
        )


def gitclone_btn(update, context):
    message = update.effective_message
    args = message.text.split(None, 2)[1:]
    user = update.effective_user
    query = update.callback_query
    user_data = context.user_data

    user_id = query.data.split("_")[1]
    if int(user_id) != user.id:
        return query.answer(
            "You're not the person who initated the command!", show_alert=True
        )


@typing_action
def gitbranch(update, context):
    message = update.effective_message
    args = message.text.split(None, 2)[1:]

    # handle args
    if len(args) == 1:
        return message.reply_text(
            "*You did not fufill the requirements!* \nSpecify the data needed: username and repository name.",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif len(args) == 2:
        user, repo = args
        rep_data = get(
            f"https://api.github.com/repos/{user}/{repo}/branches"
        ).json()

        if len(rep_data) != 0:
            reply_text = f" *{user}/{repo}* branches:\n"
            for i in range(len(rep_data)):
                reply_text += f"- [{rep_data[i]['name']}](https://github.com/{user}/{repo}/tree/{rep_data[i]['name']})\n"
            message.reply_text(
                reply_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        else:
            return message.reply_text(
                "*User/Organization not found!* \nMake sure to enter a valid username.",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        return message.reply_text(
            "Enter someone's GitHub username to view their repos or get repo data with username and repo name!"
        )


def gitbranch_btn(update, context):
    message = update.effective_message
    args = message.text.split(None, 2)[1:]

    user = update.effective_user
    data = update.callback_query.data
    user_id = query.data.split("_")[1]
    if int(user_id) != user.id:
        return query.answer(
            "You're not the person who initated the command!", show_alert=True
        )

    message.edit_text(gitbranch(message, args))


__help__ = """
Some useful git functions to make Github browsing easier and faster.

× /gitclone <username> <repo>: Get zip and git clone links of a public repo.
× /repo <username>: Displays a list of hyperlinked public repos by a user on Github.
× /repo <username> <repo>: Get stats on a public repo.
× /gitstats <username>: Get Github stats of a user.
× /gitbranch <username> <repo>: Display a list of hyperlinked branches of a public repo.
"""

__mod_name__ = "GitHub"

GITHUB_HANDLER = CommandHandler(
    "gitstats", gitstats, pass_args=True, run_async=True
)
GITCLONE_HANDLER = CommandHandler(
    "gitclone", gitclone, pass_args=True, run_async=True
)
REPO_HANDLER = CommandHandler("repo", repo, pass_args=True, run_async=True)
GITCLONE_BTN_HANDLER = CallbackQueryHandler(
    gitclone_btn, pattern=r"cloneMessage_"
)
GITBRANCH_HANDLER = CommandHandler(
    "gitbranch", gitbranch, pass_args=True, run_async=True
)
GITBRANCH_BTN_HANDLER = CallbackQueryHandler(
    gitbranch_btn, pattern=r"branchMessage_"
)

dispatcher.add_handler(GITHUB_HANDLER)
dispatcher.add_handler(REPO_HANDLER)
dispatcher.add_handler(GITCLONE_HANDLER)
dispatcher.add_handler(GITCLONE_BTN_HANDLER)
dispatcher.add_handler(GITBRANCH_HANDLER)
dispatcher.add_handler(GITBRANCH_BTN_HANDLER)