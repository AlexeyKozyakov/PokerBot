import os
import re

from telegram import Update, Message
from telegram.constants import MessageEntityType
from telegram.ext import Application, CommandHandler, ContextTypes

import core.buy_in
import core.cash_out
import core.game

TOKEN = os.getenv('POKER_BOT_TOKEN')
NUMBER_REGEXP = '\\d+'
NOT_FOUND = -1


def __get_chat_id(update: Update) -> str:
    return str(update.effective_chat.id)


def __find_number(text: str) -> int:
    result = re.search(NUMBER_REGEXP, text)
    if not result:
        return NOT_FOUND
    return int(result.group())


def __get_mentioned_users(message: Message) -> list[str]:
    result = []
    for entity in message.entities:
        if entity.type == MessageEntityType.MENTION:
            mention = message.text[entity.offset + 1:entity.offset + entity.length]
            result.append(mention)
    return result


def __format_summary(total_buy_in: dict[str, int], total_cash_out: dict[str, int], bank_size: int = 0) -> str:
    if not total_buy_in:
        return 'Никто не входил'
    message = ''
    if bank_size != 0:
        message += f'Банк {bank_size}\n'
    message += '\nВход:\n'
    for user, total in total_buy_in.items():
        message += f'{user} {total}\n'
    if total_cash_out:
        message += '\nВыход:\n'
        for user, total in total_cash_out.items():
            message += f'{user} {total}\n'
    return message


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка уже идёт')
        return
    core.game.start_game(chat_id)
    await update.message.reply_text('Катка началась')


async def buy(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if not core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка не идёт')
        return
    message = update.message
    amount = __find_number(message.text)
    if amount == NOT_FOUND:
        await update.message.reply_text('Не указана сумма закупа')
        return
    mentions = __get_mentioned_users(message)
    users = mentions if mentions else [update.effective_user.username]
    core.buy_in.add_buy_in(chat_id, users, amount)
    total_buy_in = core.buy_in.calculate_total_buy_in(chat_id, users)
    message = 'Закуп:\n'
    for user, total in total_buy_in.items():
        message += f'{user} {total}\n'
    bank_size = core.game.calculate_bank_size(chat_id)
    message += f'\nБанк {bank_size}'
    await update.message.reply_text(message)


async def quit(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if not core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка не идёт')
        return
    message = update.message
    mentions = __get_mentioned_users(message)
    user = mentions[0] if mentions else update.effective_user.username
    if not core.buy_in.has_buy_in(chat_id, user):
        await update.message.reply_text(f'{user} не заходил')
        return
    amount = __find_number(message.text)
    if amount == NOT_FOUND:
        await update.message.reply_text('Не указана сумма выхода')
        return
    core.cash_out.add_cash_out(chat_id, user, amount)
    profit = core.game.calculate_profit(chat_id, user)
    message = f'Профит:\n{user} {profit}\n'
    bank_size = core.game.calculate_bank_size(chat_id)
    message += f'\nБанк {bank_size}'
    await update.message.reply_text(message)


async def status(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if not core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка не идёт')
        return
    total_buy_in = core.game.calculate_total_buy_in(chat_id)
    total_cash_out = core.game.calculate_total_cash_out(chat_id)
    bank_size = core.game.calculate_bank_size(chat_id)
    message = __format_summary(total_buy_in, total_cash_out, bank_size)
    await update.message.reply_text(message)


async def stop(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if not core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка не идёт')
        return
    active_players = core.game.calculate_active_players(chat_id)
    if active_players:
        message = 'Не вышли игроки:\n'
        for player in active_players:
            message += f'{player}\n'
        await update.message.reply_text(message)
        return
    bank_diff = core.game.calculate_bank_size(chat_id)
    if bank_diff != 0:
        message = 'Банк не сходится\n'
        message += f'Вход больше выхода на {bank_diff}\n' if bank_diff > 0 else f'Вход меньше выхода на {-bank_diff}\n'
        total_buy_in = core.buy_in.calculate_total_buy_in(chat_id)
        total_cash_out = core.cash_out.calculate_total_cash_out(chat_id)
        bank_size = core.game.calculate_bank_size(chat_id)
        message += __format_summary(total_buy_in, total_cash_out, bank_size)
        await update.message.reply_text(message)
        return
    total_buy_in = core.buy_in.calculate_total_buy_in(chat_id)
    if not total_buy_in:
        await update.message.reply_text('Катка закончилась, никто не заходил')
        return
    total_cash_out = core.cash_out.calculate_total_cash_out(chat_id)
    money_transfers = core.game.calculate_money_transfers(chat_id)
    core.game.finish_games(chat_id)
    message = 'Катка закончилась, банк сходится\n'
    message += __format_summary(total_buy_in, total_cash_out)
    message += '\nПрофит:\n'
    for user in total_cash_out:
        message += f'{user} {total_cash_out[user] - total_buy_in[user]}\n'
    message += '\nПереводы:\n'
    for transfer in money_transfers:
        message += f'{transfer["from"]} -> {transfer["to"]}: {transfer["amount"]}\n'
    await update.message.reply_text(message)


def start_bot() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('buy', buy))
    application.add_handler(CommandHandler('quit', quit))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('stop', stop))
    application.run_polling()
