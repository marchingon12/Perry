from typing import Optional, List
from gtts import gTTS
import os
import requests
import json
from emoji import UNICODE_EMOJI

from telegram import ChatAction, ParseMode

from perry import dispatcher
from perry.modules.disable import DisableAbleCommandHandler
from perry.modules.helper_funcs.alternate import typing_action, send_action

from google_trans_new import LANGUAGES, google_translator


def gtrans(update, context):
    # Thanks to @Killer_Loli from SaitamaRobot for translate function
    # Check out the SaitamaRobot translate module here: https://github.com/AnimeKaizoku/SaitamaRobot/blob/master/SaitamaRobot/modules/gtranslator.py
    msg = update.effective_message
    problem_lang_code = [key for key in LANGUAGES if "-" in key]
    try:
        if msg.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if msg.reply_to_message.text:
                text = msg.reply_to_message.text
            elif msg.reply_to_message.caption:
                text = msg.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "en"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        dest_lang = None
        if source_lang.count("-") == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count("-") == 1:
            for lang in problem_lang_code:
                if lang in source_lang:
                    dest_lang = source_lang
                    source_lang = None
                    break
            if dest_lang is None:
                dest_lang = source_lang.split("-")[1]
                source_lang = source_lang.split("-")[0]
        else:
            dest_lang = source_lang
            source_lang = None

        exclude_list = UNICODE_EMOJI.keys()
        for emoji in exclude_list:
            if emoji in text:
                text = text.replace(emoji, "")

        trl = google_translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, lang_tgt=dest_lang)
            return msg.reply_text(
                f"Translated from `{detection[0]}` to `{dest_lang}`:\n*{trans_str}*",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            trans_str = trl.translate(
                text, lang_tgt=dest_lang, lang_src=source_lang
            )
            msg.reply_text(
                f"Translated from `{source_lang}` to `{dest_lang}`:\n*{trans_str}*",
                parse_mode=ParseMode.MARKDOWN,
            )

    except IndexError:
        update.effective_message.reply_text(
            "Reply to messages to translate them into the preffered language!\n\n"
            "Example: `/tr en-de` to translate from English to German\n"
            "Or use: `/tr de` for auto detection and translating it into German.\n",
            parse_mode=ParseMode.MARKDOWN,
        )
    except ValueError:
        update.effective_message.reply_text(
            "The intended language is not found!"
        )
    else:
        return


@send_action(ChatAction.RECORD_AUDIO)
def gtts(update, context):
    msg = update.effective_message
    reply = " ".join(context.args)
    if not reply:
        if msg.reply_to_message:
            reply = msg.reply_to_message.text
        else:
            return msg.reply_text(
                "Reply to some message or enter some text to convert it into audio format!"
            )
        for x in "\n":
            reply = reply.replace(x, "")
    try:
        tts = gTTS(reply)
        tts.save("perry.mp3")
        with open("perry.mp3", "rb") as speech:
            msg.reply_audio(speech)
    finally:
        if os.path.isfile("perry.mp3"):
            os.remove("perry.mp3")


# Open API key
API_KEY = "6ae0c3a0-afdc-4532-a810-82ded0054236"
URL = "http://services.gingersoftware.com/Ginger/correct/json/GingerTheText"


@typing_action
def spellcheck(update, context):
    if update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message

        params = dict(
            lang="US", clientVersion="2.0", apiKey=API_KEY, text=msg.text
        )

        res = requests.get(URL, params=params)
        changes = json.loads(res.text).get("LightGingerTheTextResult")
        curr_string = ""
        prev_end = 0

        for change in changes:
            start = change.get("From")
            end = change.get("To") + 1
            suggestions = change.get("Suggestions")
            if suggestions:
                sugg_str = suggestions[0].get(
                    "Text"
                )  # should look at this list more
                curr_string += msg.text[prev_end:start] + sugg_str
                prev_end = end

        curr_string += msg.text[prev_end:]
        update.effective_message.reply_text(curr_string)
    else:
        update.effective_message.reply_text(
            "Reply to some message to get grammar corrected text!"
        )


__help__ = """
Language boundaries are no more! Translate other people's messages to know what their talking about.
The translate module is using Google Translate as the translation processing method, so there might be a few errors here and there.

× /tr or /tl: Reply to messages to translate them into the preffered language! \nDefault: Language of target message -> English
× /tr <language code>: Translates targeted message into selected language code. \n> Example: /tr de
× /tr <language of msg>-<language code>: Manual language selection for targeted message to selected language code. \n> Example: /tr en-de
× /splcheck: As a reply to get grammar corrected text of gibberish message.
× /tts: To some message to convert it into audio format!
"""
__mod_name__ = "Translate"

dispatcher.add_handler(
    DisableAbleCommandHandler(
        ["tr", "tl"], gtrans, pass_args=True, run_async=True
    )
)
dispatcher.add_handler(DisableAbleCommandHandler("tts", gtts, pass_args=True))
dispatcher.add_handler(DisableAbleCommandHandler("splcheck", spellcheck))
