import html
import random
import re
import wikipedia
import subprocess
import sys
import os
from typing import Optional, List
from requests import get
from html import escape
from datetime import datetime
from google_trans_new import LANGUAGES, google_translator

from io import BytesIO
from random import randint
import requests as r

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
from telegram.utils.helpers import escape_markdown, mention_html
from telegram.error import BadRequest

from perry import (
    dispatcher,
    OWNER_ID,
    TOKEN,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    WALL_API,
    spamwtc,
)
from perry.__main__ import STATS, USER_INFO, GDPR
from perry.modules.disable import DisableAbleCommandHandler
from perry.modules.helper_funcs.extraction import extract_user
from perry.modules.helper_funcs.filters import CustomFilters
from perry.modules.helper_funcs.alternate import typing_action, send_action
from perry.modules.helper_funcs.misc import HasNextWrapper


@typing_action
def get_id(update, context):
    args = context.args
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if (
            update.effective_message.reply_to_message
            and update.effective_message.reply_to_message.forward_from
        ):
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                "The original sender, {}, has an ID of `{}`.\nThe forwarder, {}, has an ID of `{}`.".format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            user = context.bot.get_chat(user_id)
            update.effective_message.reply_text(
                "{}'s id is `{}`.".format(
                    escape_markdown(user.first_name), user.id
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text(
                "Your id is `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            update.effective_message.reply_text(
                "This group's id is `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN,
            )


def info(update, context):
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat

    if user_id:
        user = context.bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif (
        not msg.reply_to_message
        and len(args) >= 1
        and not args[0].startswith("@")
        and not args[0].isdigit()
        and not msg.parse_entities([MessageEntity.TEXT_MENTION])
    ):
        msg.reply_text("I can't extract a user from this.")
        return

    else:
        return

    del_msg = msg.reply_text(
        "Hold tight while I steal some data from <b>FBI Database</b>...",
        parse_mode=ParseMode.HTML,
    )

    text = (
        "<b>USER INFO</b>:"
        "\n\nID: <code>{}</code>"
        "\nFirst Name: {}".format(user.id, html.escape(user.first_name))
    )

    if user.last_name:
        text += "\nLast Name: {}".format(html.escape(user.last_name))

    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))

    text += "\nPermanent user link: {}".format(mention_html(user.id, "link"))

    text += "\nNumber of profile pics: {}".format(
        context.bot.get_user_profile_photos(user.id).total_count
    )

    try:
        sw = spamwtc.get_ban(int(user.id))
        if sw:
            text += "\n\n<b>This person is banned in Spamwatch!</b>"
            text += f"\nResason: <pre>{sw.reason}</pre>"
        else:
            pass
    except:
        pass  # Don't break on exceptions like if api is down?

    if user.id == OWNER_ID:
        text += "\n\nAye this guy is my owner.\nI would never do anything against him!"

    elif user.id in SUDO_USERS:
        text += (
            "\n\nThis person is one of my sudo users! "
            "Nearly as powerful as my owner - so watch it."
        )

    elif user.id in SUPPORT_USERS:
        text += (
            "\n\nThis person is one of my support users! "
            "Not quite a sudo user, but can still gban you off the map."
        )

    elif user.id in WHITELIST_USERS:
        text += (
            "\n\nThis person has been whitelisted! "
            "That means I'm not allowed to ban/kick them."
        )

    try:
        memstatus = chat.get_member(user.id).status
        if memstatus == "administrator" or memstatus == "creator":
            result = context.bot.get_chat_member(chat.id, user.id)
            if result.custom_title:
                text += f"\n\nThis user has custom title <b>{result.custom_title}</b> in this chat."
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    try:
        profile = context.bot.get_user_profile_photos(user.id).photos[0][-1]
        context.bot.sendChatAction(chat.id, "upload_photo")
        context.bot.send_photo(
            chat.id,
            photo=profile,
            caption=(text),
            parse_mode=ParseMode.HTML,
        )
    except IndexError:
        context.bot.sendChatAction(chat.id, "typing")
        msg.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )
    finally:
        del_msg.delete()


@typing_action
def echo(update, context):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@typing_action
def gdpr(update, context):
    update.effective_message.reply_text("Deleting identifiable data...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text(
        "Your personal data has been deleted.\n\nNote that this will not unban "
        "you from any chats, as that is telegram data, not perry data. "
        "Flooding, warns, and gbans are also preserved, as of "
        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
        "which clearly states that the right to erasure does not apply "
        '"for the performance of a task carried out in the public interest", as is '
        "the case for the aforementioned pieces of data.",
        parse_mode=ParseMode.MARKDOWN,
    )


MARKDOWN_HELP = """
Markdown is a very powerful formatting tool supported by telegram. {} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>~strike~</code> wrapping text with '~' will produce strikethrough text
- <code>--underline--</code> wrapping text with '--' will produce underline text
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
""".format(
    dispatcher.bot.first_name
)


@typing_action
def markdown_help(update, context):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML
    )
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!"
    )
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, --underline--, *bold*, `code`, ~strike~ "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)"
    )


@typing_action
def wiki(update, context):
    kueri = re.split(pattern="wiki", string=update.effective_message.text)
    wikipedia.set_lang("en")
    if len(str(kueri[1])) == 0:
        update.effective_message.reply_text("Enter keywords!")
    else:
        try:
            pertama = update.effective_message.reply_text("⌛ Loading...")
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="🔍 More Info...",
                            url=wikipedia.page(kueri).url,
                        )
                    ]
                ]
            )
            context.bot.editMessageText(
                chat_id=update.effective_chat.id,
                message_id=pertama.message_id,
                text=wikipedia.summary(kueri, sentences=10),
                reply_markup=keyboard,
            )
        except wikipedia.PageError as e:
            update.effective_message.reply_text(f"⚠ Error: {e}")
        except BadRequest as et:
            update.effective_message.reply_text(f"⚠ Error: {et}")
        except wikipedia.exceptions.DisambiguationError as eet:
            update.effective_message.reply_text(
                f"⚠ Error\n There are too many query! Express it more!\nPossible query result:\n{eet}"
            )


@typing_action
def ud(update, context):
    msg = update.effective_message
    args = context.args
    text = " ".join(args).lower()
    if not text:
        msg.reply_text("Please enter keywords to search!")
        return
    try:
        results = get(
            f"http://api.urbandictionary.com/v0/define?term={text}"
        ).json()
        reply_text = (
            f"Word: {text}\n\n"
            f'Definition:\n{results["list"][0]["definition"]}\n\n'
            f'Example:\n{results["list"][0]["example"]}\n\n'
        )
    except IndexError:
        reply_text = f"Word: {text}\nResults: Sorry could not find any matching results!"
    ignore_chars = "[]"
    reply = reply_text
    for chars in ignore_chars:
        reply = reply.replace(chars, "")
    if len(reply) >= 4096:
        reply = reply[:4096]  # max msg lenth of tg.
    try:
        msg.reply_text(reply)
    except BadRequest as err:
        msg.reply_text(f"Error! {err.message}")


@typing_action
def dictionary(update, context):

    msg = update.effective_message
    user = update.effective_user
    user_data = context.user_data
    inputlist = update.effective_message.text.split(None, 2)[1:]

    # handle args
    lang = "en"
    if len(inputlist) == 0:
        return msg.reply_text("Please enter keywords to search!")
    elif len(inputlist) == 1:
        text = inputlist[0]
    else:
        lang, text = inputlist

    resp = get(f"https://api.dictionaryapi.dev/api/v2/entries/{lang}/{text}")
    if resp.status_code != 200:
        return msg.reply_text("Sorry! could'nt find any results...")
    results = resp.json()[0]["meanings"]

    # make HasNextWrapper obj from search
    # results to paginate through.
    iter_page = HasNextWrapper(results)
    curr_page = iter_page.next()

    # make iter obj persistent so iter pointer
    # remember it's position.
    user_data["dictionary_page"] = (text, iter_page)

    message_text = (
        f"*Word*: {text}\n"
        f'*× Type*: {curr_page.get("partOfSpeech") or "N/A"}\n'
        f'*× Definition*: {curr_page["definitions"][0].get("definition") or "N/A"}\n'
        f'*× Example*: {curr_page["definitions"][0].get("example") or "N/A"}\n'
        f'*× Synonym*: {", ".join(curr_page["definitions"][0].get("synonyms", [])[:4]) or "N/A"}\n'
    )
    message_text += f"\n_Press 'Next' to view different parts of speech if available (noun, verb, adjective, etc.)._"

    msg.reply_text(
        message_text,
        parse_mode="markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Next ➡️",
                        callback_data=f"dictionaryNextPage_{user.id}",
                    )
                ]
            ]
        ),
    )


def dictionary_btn(update, context):
    user = update.effective_user
    query = update.callback_query
    user_data = context.user_data

    user_id = query.data.split("_")[1]
    if int(user_id) != user.id:
        return query.answer(
            "You're not the person who initated the command!", show_alert=True
        )

    try:
        iter_page = user_data["dictionary_page"][1]
        searched_word = user_data["dictionary_page"][0]
    except KeyError:
        return query.answer(
            "Data of this button is lost! Most likely due to the restart of the bot.",
            show_alert=True,
        )

    if iter_page.hasnext():
        query.answer()
        curr_page = iter_page.next()
        message_text = (
            f"*Word*: {searched_word}\n"
            f'*× Type*: {curr_page.get("partOfSpeech") or "N/A"}\n'
            f'*× Definition*: {curr_page["definitions"][0].get("definition") or "N/A"}\n'
            f'*× Example*: {curr_page["definitions"][0].get("example") or "N/A"}\n'
            f'*× Synonyms*: {", ".join(curr_page["definitions"][0].get("synonyms", [])[:4]) or "N/A"}\n'
        )
        message_text += f"\n_Press 'Next' to view different parts of speech if available (noun, verb, adjective, etc.)._"
        query.edit_message_text(
            message_text,
            reply_markup=query.message.reply_markup,
            parse_mode="markdown",
        )
    else:
        query.answer("No other meanings found!")


@typing_action
def src(update, context):
    update.effective_message.reply_text(
        "Hey there! You can find what makes me click [here](www.github.com/marchingon12/Perry).",
        parse_mode=ParseMode.MARKDOWN,
    )


@typing_action
def getlink(update, context):
    args = context.args
    message = update.effective_message
    if args:
        pattern = re.compile(r"-\d+")
    else:
        message.reply_text("You don't seem to be referring to any chats.")
    links = "Invite link(s):\n"
    for chat_id in pattern.findall(message.text):
        try:
            chat = context.bot.getChat(chat_id)
            bot_member = chat.get_member(context.bot.id)
            if bot_member.can_invite_users:
                invitelink = context.bot.exportChatInviteLink(chat_id)
                links += str(chat_id) + ":\n" + invitelink + "\n"
            else:
                links += (
                    str(chat_id)
                    + ":\nI don't have access to the invite link."
                    + "\n"
                )
        except BadRequest as excp:
            links += str(chat_id) + ":\n" + excp.message + "\n"
        except TelegramError as excp:
            links += str(chat_id) + ":\n" + excp.message + "\n"

    message.reply_text(links)


@typing_action
def pyeval(update, context):
    """
    Executes python programs dynamically
    in runtime. (`OWNER_ID`) only!
    """
    msg = update.effective_message
    args = context.args

    if len(args) <= 0:
        return msg.reply_text("Please enter python code after /exec!")
    else:
        code = msg.text.split(None, 1)[1]

    command = "".join(f"\n {x}" for x in code.split("\n.strip()"))

    res = subprocess.run(
        [sys.executable, "-c", command.strip()],
        capture_output=True,
        text=True,
        check=False,
    )
    result = str(res.stdout + res.stderr)

    # don't send results if it has bot token inside.
    if TOKEN in result:
        result = "Results includes bot TOKEN, aborting..."

    if len(result) > 2500:
        with open("output.txt", "w+") as f:
            f.write(result)
        context.bot.sendDocument(msg.chat.id, open("output.txt", "rb"))
        os.remove("output.txt")
    else:
        try:
            context.bot.sendMessage(
                msg.chat.id,
                "<pre>" + escape(result) + "</pre>",
                reply_to_message_id=msg.message_id,
                parse_mode=ParseMode.HTML,
            )
        except Exception as excp:
            if str(excp.message) == "Message must be non-empty":
                return msg.reply_text("None")
            msg.reply_text(str(excp.message))


@typing_action
def shell(update, context):
    """
    To execute terminal commands via bot
    (`OWNER_ID`) only!
    """

    msg = update.effective_message
    rep = msg.reply_text("Running command...")
    try:
        res = subprocess.Popen(
            context.args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = res.communicate()
        result = str(stdout.decode().strip()) + str(stderr.decode().strip())
        rep.edit_text(
            "<code>" + escape(result) + "</code>", parse_mode=ParseMode.HTML
        )
    except Exception as excp:
        if hasattr(excp, "message"):
            if str(excp.message) == "Message must be non-empty":
                return msg.edit_text("None")
            rep.edit_text(str(excp))


def staff_ids(update, context):
    sfile = "List of SUDO & SUPPORT users:\n"
    sfile += f"× SUDO USER IDs; {SUDO_USERS}\n"
    sfile += f"× SUPPORT USER IDs; {SUPPORT_USERS}"
    with BytesIO(str.encode(sfile)) as output:
        output.name = "staff-ids.txt"
        update.effective_message.reply_document(
            document=output,
            filename="staff-ids.txt",
            caption="Here is the list of SUDO & SUPPORTS users.",
        )


def stats(update, context):
    update.effective_message.reply_text(
        "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS])
    )


@typing_action
def github(update, context):
    message = update.effective_message
    args = context.args
    text = " ".join(args).lower()
    usr = get(f"https://api.github.com/users/{text}").json()
    if len(args) >= 1:
        if usr.get("login"):
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

            difnames = {
                "id": "Account ID",
                "type": "Account type",
                "created_at": "Account created at",
                "updated_at": "Last updated",
                "public_repos": "Public Repos",
                "public_gists": "Public Gists",
            }

            goaway = [None, 0, "null", ""]

            for x, y in usr.items():
                if x in whitelist:
                    x = difnames.get(x, x.title())

                    if x in ["Account created at", "Last updated"]:
                        y = datetime.strptime(y, "%Y-%m-%dT%H:%M:%SZ")

                    if y not in goaway:
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
        else:
            message.reply_text = (
                "User not found. Make sure you entered valid username!"
            )
    else:
        message.reply_text("Enter the GitHub username you want stats for!")


@typing_action
def repo(update, context):
    message = update.effective_message
    args = context.args
    text = " ".join(args).lower()
    usr = get(f"https://api.github.com/users/{text}/repos?per_page=40").json()
    if len(args) >= 1:
        reply_text = f"*{text}*" + "*'s*" + "* Repos:*\n"
        for i in range(len(usr)):
            reply_text += f"[{usr[i]['name']}]({usr[i]['html_url']})\n"
        message.reply_text(
            reply_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    else:
        message.reply_text(
            "Enter someone's GitHub username to view their repos!"
        )


@typing_action
def nekobin(update, context):
    message = update.effective_message
    args = message.text.split(None, 2)[1:]

    if len(args) == 1:
        extension = "txt"
        text = args[0]
        message.reply_text(
            "You have not specified a file extension. Default: <b>.txt</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        extension, text = args

    if len(text) >= 1:
        key = (
            r.post(
                "https://nekobin.com/api/documents",
                json={"content": f"{text}\n"},
            )
            .json()
            .get("result")
            .get("key")
        )

        dispatcher.bot.send_message(
            message.chat.id,
            text="<b>Nekofied: </b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="View on nekobin",
                            url=f"https://nekobin.com/{key}.{extension}",
                        ),
                    ]
                ]
            ),
        )
    else:
        message.reply_text(
            "You have two options: \n1. Reply to a file or text to nekofy it!\n 2. Send command with text and specify file extension."
        )


# /exec: Enables the OWNER and SUDO_USERS to execute python code using the bot.
# /shell: Enables the OWNER to run bash commands within the server using the bot.
# /echo: For SUDO_USERS, Perry will write and replace your message.
# /stats: OWNER can call bot stats.
# /getlink: OWNER can get group link by using group id.
__help__ = """
An "odds and ends" module for small, simple commands which don't really fit anywhere

 × /id: Get the current group id. If used by replying to a message, gets that user's id.
 × /info: Get information about a user.
 × /source: Get the codebase source link.
 × /gitstats <username>: Get Github stats of a user.
 × /repo <username>: Displays a list of hyperlinked repos of a user on Github.
 × /wiki <query>: Search wikipedia articles.
 × /dict <query>: Search for words you are unsure about with a dictionary. Supported languages are: en, de fr.
 × /ud <query> : Search stuffs in urban dictionary.
 × /reverse: Reverse searches image or stickers on google.
 × /gdpr: Deletes your information from the bot's database. Private chats only.
 × /markdownhelp: Quick summary of how markdown works in telegram - can only be called in private chats.
"""

__mod_name__ = "Miscs"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)
ECHO_HANDLER = CommandHandler("echo", echo, filters=CustomFilters.sudo_filter)
MD_HELP_HANDLER = CommandHandler(
    "markdownhelp", markdown_help, filters=Filters.private
)
STATS_HANDLER = CommandHandler("stats", stats, filters=Filters.user(OWNER_ID))
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
UD_HANDLER = DisableAbleCommandHandler("ud", ud)
GETLINK_HANDLER = CommandHandler(
    "getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID)
)
STAFFLIST_HANDLER = CommandHandler(
    "staffids", staff_ids, filters=Filters.user(OWNER_ID)
)
SRC_HANDLER = CommandHandler("source", src, filters=Filters.private)
SHELL_HANDLER = CommandHandler(
    "shell", shell, filters=Filters.user(OWNER_ID), run_async=True
)
PYEVAL_HANDLER = CommandHandler(
    "exec", pyeval, filters=CustomFilters.sudo_filter, run_async=True
)
GITHUB_HANDLER = CommandHandler(
    "gitstats", github, pass_args=True, run_async=True
)
REPO_HANDLER = CommandHandler("repo", repo, pass_args=True, run_async=True)
DICT_HANDLER = CommandHandler(
    "dict", dictionary, pass_args=True, run_async=True
)
DICT_BTN_HANDLER = CallbackQueryHandler(
    dictionary_btn, pattern=r"dictionaryNextPage_"
)
NEKOFY_HANDLER = CommandHandler(
    "nekofy", nekobin, pass_args=True, run_async=True
)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(STAFFLIST_HANDLER)
dispatcher.add_handler(SRC_HANDLER)
dispatcher.add_handler(SHELL_HANDLER)
dispatcher.add_handler(PYEVAL_HANDLER)
dispatcher.add_handler(GITHUB_HANDLER)
dispatcher.add_handler(REPO_HANDLER)
dispatcher.add_handler(DICT_HANDLER)
dispatcher.add_handler(DICT_BTN_HANDLER)
dispatcher.add_handler(NEKOFY_HANDLER)
