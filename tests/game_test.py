from core.buy_in import add_buy_in
from core.cash_out import add_cash_out
from core.game import start_game, has_active_games, finish_games, calculate_profit, calculate_active_players, \
    calculate_bank_size, calculate_money_transfers
from core.models import Game, CashOut, BuyIn
from tests.base import BaseTestCase

CHAT_ID_1 = '1234'
CHAT_ID_2 = '2345'


class GamesTestCase(BaseTestCase):
    def models(self):
        return [Game, BuyIn, CashOut]

    def setUp(self):
        super().setUp()
        self.__init_first_game()

    def test_chat_has_active_games(self):
        self.assertTrue(has_active_games(CHAT_ID_1))

    def test__chat_has_no_active_games(self):
        self.assertFalse(has_active_games(CHAT_ID_2))

    def test_finish_game(self):
        finish_games(CHAT_ID_1)
        self.assertFalse(has_active_games(CHAT_ID_1))

    def test_calculate_profit(self):
        self.assertEqual(1250, calculate_profit(CHAT_ID_1, 'user2'))

    def test_calculate_active_players(self):
        self.__init_second_game()
        self.assertEqual(['user2'], calculate_active_players(CHAT_ID_2))

    def test_no_active_players(self):
        start_game(CHAT_ID_2)
        self.__init_second_game()
        add_cash_out(CHAT_ID_2, 'user2', 300)
        self.assertFalse(calculate_active_players(CHAT_ID_2))

    def test_calculate_active_players_multiple_cash_out(self):
        start_game(CHAT_ID_2)
        self.__init_second_game()
        add_buy_in(CHAT_ID_2, ['user1', 'user2'], 600)
        add_cash_out(CHAT_ID_2, 'user2', 0)
        self.assertEqual(['user1'], calculate_active_players(CHAT_ID_2))

    def test_calculate_bank_size(self):
        self.__init_second_game()
        add_cash_out(CHAT_ID_2, 'user2', 300)
        self.assertEqual(1054, calculate_bank_size(CHAT_ID_2))

    def test_calculate_back_size_zero(self):
        self.assertEqual(0, calculate_bank_size(CHAT_ID_1))

    def test_calculate_money_transfers(self):
        self.assertEqual(
            [
                {
                    'from': 'user1',
                    'to': 'user2',
                    'amount': 1250
                },
                {
                    'from': 'user1',
                    'to': 'user3',
                    'amount': 250
                }
            ],
            calculate_money_transfers(CHAT_ID_1)
        )

    @staticmethod
    def __init_first_game():
        start_game(CHAT_ID_1)
        add_buy_in(CHAT_ID_1, ['user1', 'user2', 'user3'], 500)
        add_buy_in(CHAT_ID_1, ['user1'], 1000)
        add_cash_out(CHAT_ID_1, 'user1', 0)
        add_cash_out(CHAT_ID_1, 'user2', 1750)
        add_cash_out(CHAT_ID_1, 'user3', 750)

    @staticmethod
    def __init_second_game():
        start_game(CHAT_ID_2)
        add_buy_in(CHAT_ID_2, ['user1', 'user2', 'user3'], 500)
        add_buy_in(CHAT_ID_2, ['user2'], 100)
        add_cash_out(CHAT_ID_2, 'user1', 123)
        add_cash_out(CHAT_ID_2, 'user3', 123)
