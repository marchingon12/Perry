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
