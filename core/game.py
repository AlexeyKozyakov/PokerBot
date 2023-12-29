from __future__ import annotations

import datetime

from core.buy_in import calculate_total_buy_in
from core.cash_out import calculate_total_cash_out
from core.models import Game


def has_active_games(chat_id: str) -> bool:
    return Game.select().where((Game.chat_id == chat_id) & ~Game.is_finished).exists()


def start_game(chat_id: str) -> None:
    Game.create(chat_id=chat_id, is_finished=False)


def finish_games(chat_id: str) -> None:
    Game.update(is_finished=True).where(Game.chat_id == chat_id).execute()


def __calculate_total_profit(games: list[Game]) -> dict[str, int]:
    profits = {}

    def update_profit(profit_user, diff):
        if profit_user not in profits:
            profits[profit_user] = 0
        profits[profit_user] += diff

    for game in games:
        for cash_out in game.cash_outs:
            update_profit(cash_out.user, cash_out.amount)
        for buy_in in game.buy_ins:
            update_profit(buy_in.user, -buy_in.amount)

    return profits


def calculate_profit(chat_id: str, user: str = None) -> int | dict[str, int]:
    if user:
        total_cash_out = calculate_total_cash_out(chat_id, user)
        total_buy_in = calculate_total_buy_in(chat_id, [user])[user]
        return total_cash_out - total_buy_in
    game = Game.get(chat_id=chat_id, is_finished=False)
    return __calculate_total_profit([game])


def calculate_total_profit_in_all_finished_games(chat_id: str) -> dict[str, int]:
    games = Game.select().where((Game.chat_id == chat_id) & Game.is_finished)
    return __calculate_total_profit(games)


def calculate_active_players(chat_id: str) -> list[str]:
    last_actions_time = {}
    game = Game.get(chat_id=chat_id, is_finished=False)

    def update_last_action_time(user, action, timestamp):
        if user not in last_actions_time:
            last_actions_time[user] = {'buy_in': datetime.datetime(1, 1, 1),
                                       'cash_out': datetime.datetime(1, 1, 1)}
        if last_actions_time[user][action] < timestamp:
            last_actions_time[user][action] = timestamp

    for buy_in in game.buy_ins:
        update_last_action_time(buy_in.user, 'buy_in', buy_in.timestamp)
    for cash_out in game.cash_outs:
        update_last_action_time(cash_out.user, 'cash_out', cash_out.timestamp)
    return [user for user, actions_time in last_actions_time.items() if
            actions_time['buy_in'] > actions_time['cash_out']]


def calculate_bank_size(chat_id: str) -> int:
    game = Game.get(chat_id=chat_id, is_finished=False)
    diff = 0
    for buy_in in game.buy_ins:
        diff += buy_in.amount
    for cash_out in game.cash_outs:
        diff -= cash_out.amount
    return diff


def calculate_money_transfers(chat_id: str) -> list[dict]:
    profits = calculate_profit(chat_id)

    if not profits:
        return []

    transfers = []
    while True:
        min_profit_user = min(profits, key=profits.get)
        min_profit = profits[min_profit_user]
        if min_profit >= 0:
            return transfers
        max_profit_user = max(profits, key=profits.get)
        max_profit = profits[max_profit_user]
        if max_profit <= 0:
            return transfers
        transfer_amount = min(-min_profit, max_profit)
        profits[min_profit_user] += transfer_amount
        profits[max_profit_user] -= transfer_amount
        transfer = {
            'from': min_profit_user,
            'to': max_profit_user,
            'amount': transfer_amount
        }
        transfers.append(transfer)
