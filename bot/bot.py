import os
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, InlineQueryHandler, filters, \
    MessageHandler

import core.buy_in
import core.cash_out
import core.game

TOKEN = os.getenv('POKER_BOT_TOKEN')
NUMBER_REGEXP = '\\d+'
NOT_FOUND = -1


def __get_chat_id(update: Update) -> str:
    return str(update.effective_chat.id)


def __find_number(args: list[str]) -> int:
    for arg in args:
        if re.fullmatch(NUMBER_REGEXP, arg):
            return int(arg)
    return NOT_FOUND


def __get_mentioned_users(args: list[str], effective_user: str) -> list[str]:
    print(args)
    users = []
    for arg in args:
        if arg.startswith('@'):
            user = effective_user if arg == '@me' else arg[1::]
            users.append(user)
    return users


def __format_summary(total_buy_in: dict[str, int], total_cash_out: dict[str, int], bank_size: int = 0) -> str:
    if not total_buy_in:
        return 'Никто не входил'
    message = ''
    if bank_size != 0:
        message += f'Банк {bank_size}\n'
    message += '\nВход:\n'
    total_buy_in_sorted = sorted(total_buy_in.items(), key=lambda item: item[1], reverse=True)
    for user, total in total_buy_in_sorted:
        message += f'{user} {total}\n'
    if total_cash_out:
        message += '\nВыход:\n'
        total_cash_out_sorted = sorted(total_cash_out.items(), key=lambda item: item[1], reverse=True)
        for user, total in total_cash_out_sorted:
            message += f'{user} {total}\n'
    return message


def __format_profit(profits: dict[str, int]):
    message = '\nПрофит:\n'
    profits_sorted = sorted(profits.items(), key=lambda item: item[1], reverse=True)
    for user, profit in profits_sorted:
        message += f'{user} {profit}\n'
    return message


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка уже идёт')
        return
    core.game.start_game(chat_id)
    await update.message.reply_text('Катка началась')


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if not core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка не идёт')
        return
    amount = __find_number(context.args)
    if amount == NOT_FOUND:
        await update.message.reply_text('Не указана сумма закупа')
        return
    mentions = __get_mentioned_users(context.args, effective_user=update.effective_user.username)
    users = mentions if mentions else [update.effective_user.username]
    core.buy_in.add_buy_in(chat_id, users, amount)
    total_buy_in = core.buy_in.calculate_total_buy_in(chat_id, users)
    message = 'Закуп:\n'
    for user, total in total_buy_in.items():
        message += f'{user} {total}\n'
    bank_size = core.game.calculate_bank_size(chat_id)
    message += f'\nБанк {bank_size}'
    await update.message.reply_text(message)


async def quit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    if not core.game.has_active_games(chat_id):
        await update.message.reply_text('Катка не идёт')
        return
    mentions = __get_mentioned_users(context.args, effective_user=update.effective_user.username)
    user = mentions[0] if mentions else update.effective_user.username
    if not core.buy_in.has_buy_in(chat_id, user):
        await update.message.reply_text(f'{user} не заходил')
        return
    amount = __find_number(context.args)
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
    bank_size = core.game.calculate_bank_size(chat_id)
    if bank_size != 0:
        message = 'Банк не сходится\n'
        message += f'Вход больше выхода на {bank_size}\n' if bank_size > 0 else f'Вход меньше выхода на {-bank_size}\n'
        total_buy_in = core.buy_in.calculate_total_buy_in(chat_id)
        total_cash_out = core.cash_out.calculate_total_cash_out(chat_id)
        message += __format_summary(total_buy_in, total_cash_out, bank_size)
        await update.message.reply_text(message)
        return
    total_buy_in = core.buy_in.calculate_total_buy_in(chat_id)
    if not total_buy_in:
        core.game.finish_games(chat_id)
        await update.message.reply_text('Катка закончилась, никто не заходил')
        return
    total_cash_out = core.cash_out.calculate_total_cash_out(chat_id)
    message = 'Катка закончилась, банк сходится\n'
    message += __format_summary(total_buy_in, total_cash_out)
    profits = core.game.calculate_profit(chat_id)
    message += __format_profit(profits)
    message += '\nПереводы:\n'
    money_transfers = core.game.calculate_money_transfers(chat_id)
    for transfer in money_transfers:
        message += f'{transfer["from"]} -> {transfer["to"]}: {transfer["amount"]}\n'
    core.game.finish_games(chat_id)
    await update.message.reply_text(message)


async def statistics(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = __get_chat_id(update)
    total_profit = core.game.calculate_total_profit_in_all_finished_games(chat_id)
    if not total_profit:
        await update.message.reply_text('Нет завершенных игр')
        return
    message = __format_profit(total_profit)
    await update.message.reply_text(message)


async def actions(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton('Получить фишки', switch_inline_query_current_chat='/buy '),
            InlineKeyboardButton('Отдать фишки', switch_inline_query_current_chat='/quit ')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Действия', reply_markup=reply_markup)


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_username = context.bot.username
    message_text = update.message.text
    handle_as_command = message_text.startswith(f'@{bot_username} /')
    if not handle_as_command:
        return
    words = message_text.split(' ')
    command = words[1][1::]
    args = words[2::]
    context.args = args
    if command == 'buy':
        await buy(update, context)
    elif command == 'quit':
        await quit(update, context)


def start_bot() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('buy', buy))
    application.add_handler(CommandHandler('quit', quit))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('statistics', statistics))
    application.add_handler(CommandHandler('actions', actions))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
    application.run_polling()
