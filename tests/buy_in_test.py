from core.buy_in import add_buy_in, calculate_total_buy_in, has_buy_in
from core.game import start_game
from core.models import Game, BuyIn
from tests.base import BaseTestCase

CHAT_ID = '123'


class BuyInTestCase(BaseTestCase):
    def models(self):
        return [Game, BuyIn]

    def setUp(self):
        super().setUp()
        start_game(CHAT_ID)

    def test_add_buy_in_multiple_users(self):
        add_buy_in(CHAT_ID, ["user1", "user2"], amount=500)
        self.__assert_buy_in(
            [
                {
                    'game_chat_id': '123',
                    'user': "user1",
                    'amount': 500,
                },
                {
                    'game_chat_id': '123',
                    'user': "user2",
                    'amount': 500,
                }
            ]
        )

    def test_add_buy_in_single_user(self):
        add_buy_in(CHAT_ID, ["user1"], amount=1000)
        self.__assert_buy_in(
            [
                {
                    'game_chat_id': '123',
                    'user': "user1",
                    'amount': 1000,
                }
            ]
        )

    def test_add_buy_in_no_users(self):
        self.assertRaises(AssertionError, lambda: add_buy_in(CHAT_ID, [], amount=133))

    def test_add_buy_in_negative_amount(self):
        self.assertRaises(AssertionError, lambda: add_buy_in(CHAT_ID, ["user1"], amount=-2))

    def test_has_buy_in(self):
        add_buy_in(CHAT_ID, ["user1"], amount=1000)
        self.assertTrue(has_buy_in(CHAT_ID, "user1"))

    def test_has_no_buy_in(self):
        add_buy_in(CHAT_ID, ["user2"], amount=1000)
        self.assertFalse(has_buy_in(CHAT_ID, "user1"))

    def test_calculate_total_buy_in_for_specific_users(self):
        add_buy_in(CHAT_ID, ["user1", "user2", "user3"], 500)
        add_buy_in(CHAT_ID, ["user1"], 1000)
        self.assertEqual(
            {
                'user1': 1500,
                'user2': 500,
            },
            calculate_total_buy_in(CHAT_ID, ["user1", "user2"])
        )

    def test_calculate_total_buy_in_for_all_users(self):
        add_buy_in(CHAT_ID, ["user1", "user2", "user3"], 500)
        add_buy_in(CHAT_ID, ["user1"], 1000)
        self.assertEqual(
            {
                'user1': 1500,
                'user2': 500,
                'user3': 500
            },
            calculate_total_buy_in(CHAT_ID)
        )

    def __assert_buy_in(self, data):
        self.assertEqual(
            data,
            [
                {
                    'game_chat_id': buy_in.game.chat_id,
                    'user': buy_in.user,
                    'amount': buy_in.amount
                }
                for buy_in in BuyIn.select()
            ]
        )
