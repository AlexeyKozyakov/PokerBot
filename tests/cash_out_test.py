from core.cash_out import add_cash_out, calculate_total_cash_out
from core.game import start_game
from core.models import CashOut, Game
from tests.base import BaseTestCase

CHAT_ID = "123"


class CashOutTestCase(BaseTestCase):
    def models(self):
        return [Game, CashOut]

    def setUp(self):
        super().setUp()
        start_game(CHAT_ID)

    def test_add_cash_out(self):
        add_cash_out(CHAT_ID, "user1", 1345)
        add_cash_out(CHAT_ID, "user1", 500)
        add_cash_out(CHAT_ID, "user2", 234)
        self.assertEqual(
            [
                {
                    "chat_id": "123",
                    'user': "user1",
                    'amount': 1345
                },
                {
                    "chat_id": "123",
                    'user': "user1",
                    'amount': 500
                },
                {
                    "chat_id": "123",
                    'user': "user2",
                    'amount': 234
                }
            ],
            [
                {
                    'chat_id': cash_out.game.chat_id,
                    'user': cash_out.user,
                    'amount': cash_out.amount,
                }
                for cash_out in CashOut.select()
            ]
        )

    def test_add_cash_out_negative_amount(self):
        self.assertRaises(AssertionError, lambda: add_cash_out(CHAT_ID, "user1", -200))

    def test_calculate_total_cash_out_for_specific_user(self):
        add_cash_out(CHAT_ID, "user1", 1250)
        add_cash_out(CHAT_ID, "user2", 400)
        add_cash_out(CHAT_ID, "user3", 800)
        add_cash_out(CHAT_ID, "user2", 800)
        self.assertEqual(1200, calculate_total_cash_out(CHAT_ID, "user2"))

    def test_calculate_total_cash_out_for_all_users(self):
        add_cash_out(CHAT_ID, "user1", 1250)
        add_cash_out(CHAT_ID, "user2", 400)
        add_cash_out(CHAT_ID, "user3", 800)
        add_cash_out(CHAT_ID, "user2", 800)
        add_cash_out(CHAT_ID, 'user1', 300)
        self.assertEqual(
            {
                'user1': 1550,
                'user2': 1200,
                'user3': 800
            },
            calculate_total_cash_out(CHAT_ID)
        )
