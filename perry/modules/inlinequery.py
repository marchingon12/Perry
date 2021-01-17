#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (C) 22021-present Austin Hornhead // This file is part of Perry
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import html
from typing import List, Any

from telegram.ext import InlineQueryHandler
from telegram.error import BadRequest
from telegram import User, Update, InlineKeyboardMarkup, InlineKeyboardButton

from perry import (
    dispatcher,
    updater,
    TOKEN,
    OWNER_ID,
    WEBHOOK,
    CERT_PATH,
    PORT,
    URL,
    LOGGER,
    BLACKLIST_CHATS,
    WHITELIST_CHATS,
    CLEAN_UPDATE,
)

# ----------------------------------------------#
# Main inline query handler function.
# ----------------------------------------------#


def inlinequery(update: Update, _) -> None:
    """
    Main InlineQueryHandler callback.
    """
    query = update.inline_query.query
    user = update.effective_user

    results: List = []
    inline_help_dicts = [
        {
            "title": "Search for movies",
            "description": "Get movies information",
            "message_text": gs(user.id, "movie_inline_hlp"),
            "thumb_urL": const.MOVIE_INLINE_LOGO,
            "keyboard": ".movie ",
        },
    ]

    inline_funcs = {
        "ud": urban_dict_query,
        "dict": multi_lang_dict_query,
        "kang": anime_query,
    }

    if (f := query.split(" ", 1)[0]) in inline_funcs:
        inline_funcs[f](query.removeprefix(f).strip(), update, user)
    else:
        for ihelp in inline_help_dicts:
            results.append(
                article(
                    title=ihelp["title"],
                    description=ihelp["description"],
                    message_text=ihelp["message_text"],
                    thumb_url=ihelp["thumb_urL"],
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="Click Here",
                                    switch_inline_query_current_chat=ihelp[
                                        "keyboard"
                                    ],
                                )
                            ]
                        ]
                    ),
                )
            )

        handle_inline_query(update, results)


def urabn_dict_query(query: str, update: Update, user: User) -> None:
    """
    Handle movie inline query.
    """
    results: List = []
    try:
        res = movie_api.search(query)
    except (TmdbApiError, ZeroResultsFound):
        return

    for con in res["results"]:
        results.append(
            article(
                title=con.get("title", "N/A"),
                description=con.get("release_date", "N/A"),
                thumb_url=f"https://image.tmdb.org/t/p/w500/{con['poster_path']}",
                message_text=gs(user.id, "inline_str").format(
                    html.escape(con.get("original_title", "N/A")),
                    con.get("release_date", "N/A"),
                    con.get("popularity", "N/A"),
                    con.get("original_language", "N/A"),
                    con.get("vote_average", "N/A"),
                    html.escape(con.get("overview", "N/A")),
                )
                + f"<a href='https://image.tmdb.org/t/p/w500/{con['poster_path']}'>&#xad</a>",
                reply_markup=kb.inline_keyb(mv_id=con["id"]),
            )
        )

    handle_inline_query(update, results)