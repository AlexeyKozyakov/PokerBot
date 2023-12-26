from core.models import Game, BuyIn


def add_buy_in(chat_id: str, users: list[str], amount: int) -> None:
    assert users and amount > 0
    game = Game.get(chat_id=chat_id, is_finished=False)
    buy_ins = [BuyIn(game=game, user=user, amount=amount) for user in users]
    BuyIn.bulk_create(buy_ins)


def has_buy_in(chat_id: str, user: str) -> bool:
    game = Game.get(chat_id=chat_id, is_finished=False)
    return BuyIn.select().where((BuyIn.game == game) & (BuyIn.user == user)).exists()


def calculate_total_buy_in(chat_id: str, users: list[str] = ()) -> dict[str, int]:
    game = Game.get(chat_id=chat_id, is_finished=False)
    users_set = set(users)
    total = {}
    for buy_in in game.buy_ins:
        user = buy_in.user
        if users_set and user not in users_set:
            continue
        if user not in total:
            total[user] = 0
        total[user] += buy_in.amount
    return total
