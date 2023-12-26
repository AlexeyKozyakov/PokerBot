from __future__ import annotations

from core.models import Game, CashOut


def add_cash_out(chat_id: str, user: str, amount: int) -> None:
    assert amount >= 0
    game = Game.get(chat_id=chat_id, is_finished=False)
    CashOut.create(game=game, user=user, amount=amount)


def calculate_total_cash_out(chat_id: str, user: str = None) -> int | dict[str, int]:
    game = Game.get(chat_id=chat_id, is_finished=False)
    if user:
        total = 0
        for cash_out in game.cash_outs:
            if cash_out.user == user:
                total += cash_out.amount
        return total
    total = {}
    for cash_out in game.cash_outs:
        user = cash_out.user
        if user not in total:
            total[user] = 0
        total[user] += cash_out.amount
    return total
