import unittest
from pathlib import Path

from bank_system import Bank


class TestBankSystem(unittest.TestCase):
    def setUp(self):
        self.storage = Path("data/test_bank_data.json")
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        if self.storage.exists():
            self.storage.unlink()
        self.bank = Bank(self.storage)

    def test_customer_and_account_flow(self):
        customer = self.bank.create_customer("Ayesha Khan", "ayesha@example.com", "UAE", "Global Trade")
        self.assertIn("customer_id", customer)

        account = self.bank.open_account(customer["customer_id"], "checking", "USD", 1000)
        self.assertEqual(account["balance"], 1000.0)

        deposit = self.bank.deposit(account["account_id"], 500, "Salary")
        self.assertEqual(deposit["amount"], 500)
        self.assertEqual(self.bank.get_account(account["account_id"]).balance, 1500.0)

        withdraw = self.bank.withdraw(account["account_id"], 200, "Expense")
        self.assertEqual(withdraw["amount"], 200)
        self.assertEqual(self.bank.get_account(account["account_id"]).balance, 1300.0)

        second_account = self.bank.open_account(customer["customer_id"], "savings", "USD", 250)
        transfer = self.bank.transfer(account["account_id"], second_account["account_id"], 300, "Savings transfer")
        self.assertEqual(transfer["amount"], 300)
        self.assertEqual(self.bank.get_account(account["account_id"]).balance, 1000.0)
        self.assertEqual(self.bank.get_account(second_account["account_id"]).balance, 550.0)

    def test_loan_creation(self):
        customer = self.bank.create_customer("Noah Ali", "noah@example.com", "UK", "Industrial Ops")
        account = self.bank.open_account(customer["customer_id"], "business", "USD", 100)
        loan = self.bank.create_loan(account["account_id"], 5000, 12, 7.5, "Equipment financing")
        self.assertEqual(loan["principal"], 5000)
        self.assertEqual(self.bank.get_account(account["account_id"]).balance, 5100.0)

    def test_summary_metrics(self):
        customer_a = self.bank.create_customer("Ibrahim Saleh", "ibrahim@example.com", "KSA", "Finance")
        account_a = self.bank.open_account(customer_a["customer_id"], "checking", "USD", 500)

        customer_b = self.bank.create_customer("Daniel Green", "daniel@example.com", "USA", "Logistics")
        account_b = self.bank.open_account(customer_b["customer_id"], "business", "USD", 200)

        self.bank.deposit(account_b["account_id"], 300, "Revenue")
        summary = self.bank.get_summary()
        self.assertEqual(summary["total_customers"], 2)
        self.assertEqual(summary["active_accounts"], 2)
        self.assertEqual(summary["total_balances"], 1000.0)


if __name__ == "__main__":
    unittest.main()
