from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bank_system import Bank


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Qureshi Bank System")
    subparsers = parser.add_subparsers(dest="command", required=True)

    customer = subparsers.add_parser("create-customer", help="Register a new customer")
    customer.add_argument("--name", required=True)
    customer.add_argument("--email", required=True)
    customer.add_argument("--country", required=True)
    customer.add_argument("--business", default="")

    open_account = subparsers.add_parser("open-account", help="Open a new banking account")
    open_account.add_argument("--customer-id", required=True)
    open_account.add_argument("--type", dest="account_type", required=True, choices=["checking", "savings", "business"])
    open_account.add_argument("--currency", default="USD")
    open_account.add_argument("--initial-deposit", type=float, default=0.0)

    deposit = subparsers.add_parser("deposit", help="Make a deposit")
    deposit.add_argument("--account-id", required=True)
    deposit.add_argument("--amount", required=True, type=float)
    deposit.add_argument("--description", default="Deposit")

    withdraw = subparsers.add_parser("withdraw", help="Make a withdrawal")
    withdraw.add_argument("--account-id", required=True)
    withdraw.add_argument("--amount", required=True, type=float)
    withdraw.add_argument("--description", default="Withdrawal")

    transfer = subparsers.add_parser("transfer", help="Transfer between accounts")
    transfer.add_argument("--from-account", required=True)
    transfer.add_argument("--to-account", required=True)
    transfer.add_argument("--amount", required=True, type=float)
    transfer.add_argument("--description", default="Transfer")

    loan = subparsers.add_parser("loan", help="Create a loan")
    loan.add_argument("--account-id", required=True)
    loan.add_argument("--principal", required=True, type=float)
    loan.add_argument("--term-months", required=True, type=int)
    loan.add_argument("--rate", required=True, type=float)
    loan.add_argument("--description", default="Business loan")

    statement = subparsers.add_parser("statement", help="Show account statement")
    statement.add_argument("--account-id", required=True)

    customer_list = subparsers.add_parser("customers", help="List all customers")
    customer_list.add_argument("--country", default=None)

    accounts = subparsers.add_parser("accounts", help="List all accounts")
    accounts.add_argument("--customer-id", default=None)

    summary = subparsers.add_parser("summary", help="Show overall bank summary")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    bank = Bank(Path("data/bank_data.json"))

    if args.command == "create-customer":
        customer = bank.create_customer(
            full_name=args.name,
            email=args.email,
            country=args.country,
            business_name=args.business,
        )
        print_json({"customer": customer})
        return

    if args.command == "open-account":
        account = bank.open_account(
            customer_id=args.customer_id,
            account_type=args.account_type,
            currency=args.currency,
            initial_deposit=args.initial_deposit,
        )
        print_json({"account": account})
        return

    if args.command == "deposit":
        result = bank.deposit(args.account_id, args.amount, args.description)
        print_json({"transaction": result})
        return

    if args.command == "withdraw":
        result = bank.withdraw(args.account_id, args.amount, args.description)
        print_json({"transaction": result})
        return

    if args.command == "transfer":
        result = bank.transfer(args.from_account, args.to_account, args.amount, args.description)
        print_json({"transfer": result})
        return

    if args.command == "loan":
        result = bank.create_loan(args.account_id, args.principal, args.term_months, args.rate, args.description)
        print_json({"loan": result})
        return

    if args.command == "statement":
        statement = bank.get_statement(args.account_id)
        print_json({"account_id": args.account_id, "transactions": statement})
        return

    if args.command == "customers":
        customers = bank.list_customers(args.country)
        print_json({"customers": customers})
        return

    if args.command == "accounts":
        accounts = bank.list_accounts(args.customer_id)
        print_json({"accounts": accounts})
        return

    if args.command == "summary":
        summary = bank.get_summary()
        print_json(summary)
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
