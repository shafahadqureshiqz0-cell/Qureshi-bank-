from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class BankError(ValueError):
    pass


@dataclass
class Transaction:
    transaction_id: str
    account_id: str
    transaction_type: str
    amount: float
    currency: str
    description: str
    timestamp: str


@dataclass
class Loan:
    loan_id: str
    account_id: str
    principal: float
    term_months: int
    interest_rate: float
    outstanding_balance: float
    created_at: str
    status: str = "active"


@dataclass
class Account:
    account_id: str
    customer_id: str
    account_type: str
    currency: str
    balance: float = 0.0
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    transactions: List[Transaction] = field(default_factory=list)
    loans: List[Loan] = field(default_factory=list)


@dataclass
class Customer:
    customer_id: str
    full_name: str
    email: str
    country: str
    business_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    accounts: List[str] = field(default_factory=list)


class Bank:
    def __init__(self, storage_path: str | Path = "data/bank_data.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.customers: Dict[str, Customer] = {}
        self.accounts: Dict[str, Account] = {}
        self.loans: Dict[str, Loan] = {}
        self._load()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _load(self) -> None:
        if not self.storage_path.exists():
            self.save()
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except json.JSONDecodeError:
            self.save()
            return

        for customer_data in payload.get("customers", []):
            customer = Customer(**customer_data)
            self.customers[customer.customer_id] = customer

        for account_data in payload.get("accounts", []):
            account = Account(**account_data)
            account.transactions = [Transaction(**tx) for tx in account_data.get("transactions", [])]
            account.loans = [Loan(**loan) for loan in account_data.get("loans", [])]
            self.accounts[account.account_id] = account

        for loan_data in payload.get("loans", []):
            loan = Loan(**loan_data)
            self.loans[loan.loan_id] = loan

    def save(self) -> None:
        payload = {
            "customers": [asdict(customer) for customer in self.customers.values()],
            "accounts": [asdict(account) for account in self.accounts.values()],
            "loans": [asdict(loan) for loan in self.loans.values()],
        }
        with self.storage_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    def create_customer(self, full_name: str, email: str, country: str, business_name: str = "") -> Dict[str, Any]:
        if not full_name.strip() or not email.strip() or not country.strip():
            raise BankError("Full name, email, and country are required.")

        customer_id = uuid4().hex[:10]
        customer = Customer(
            customer_id=customer_id,
            full_name=full_name.strip(),
            email=email.strip(),
            country=country.strip(),
            business_name=business_name.strip(),
        )
        self.customers[customer_id] = customer
        self.save()
        return asdict(customer)

    def get_customer(self, customer_id: str) -> Customer:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise BankError(f"Customer {customer_id} not found.")
        return customer

    def open_account(
        self,
        customer_id: str,
        account_type: str,
        currency: str = "USD",
        initial_deposit: float = 0.0,
    ) -> Dict[str, Any]:
        customer = self.get_customer(customer_id)
        account_type = account_type.lower()
        if account_type not in {"checking", "savings", "business"}:
            raise BankError("Unsupported account type. Choose checking, savings, or business.")
        if initial_deposit < 0:
            raise BankError("Initial deposit cannot be negative.")

        account_id = uuid4().hex[:12]
        account = Account(
            account_id=account_id,
            customer_id=customer_id,
            account_type=account_type,
            currency=currency.upper(),
            balance=initial_deposit,
        )

        if initial_deposit > 0:
            account.transactions.append(
                Transaction(
                    transaction_id=uuid4().hex[:10],
                    account_id=account_id,
                    transaction_type="deposit",
                    amount=initial_deposit,
                    currency=currency.upper(),
                    description="Initial deposit",
                    timestamp=self._now(),
                )
            )

        self.accounts[account_id] = account
        customer.accounts.append(account_id)
        self.save()
        return asdict(account)

    def get_account(self, account_id: str) -> Account:
        account = self.accounts.get(account_id)
        if account is None:
            raise BankError(f"Account {account_id} not found.")
        return account

    def _record_transaction(self, account: Account, transaction_type: str, amount: float, currency: str, description: str) -> Transaction:
        if amount <= 0:
            raise BankError("Amount must be greater than zero.")
        transaction = Transaction(
            transaction_id=uuid4().hex[:10],
            account_id=account.account_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency.upper(),
            description=description,
            timestamp=self._now(),
        )
        account.transactions.append(transaction)
        return transaction

    def deposit(self, account_id: str, amount: float, description: str = "Deposit") -> Dict[str, Any]:
        account = self.get_account(account_id)
        if amount <= 0:
            raise BankError("Deposit amount must be positive.")

        account.balance += amount
        tx = self._record_transaction(account, "deposit", amount, account.currency, description)
        self.save()
        return asdict(tx)

    def withdraw(self, account_id: str, amount: float, description: str = "Withdrawal") -> Dict[str, Any]:
        account = self.get_account(account_id)
        if amount <= 0:
            raise BankError("Withdrawal amount must be positive.")
        if amount > account.balance:
            raise BankError("Insufficient funds for withdrawal.")

        account.balance -= amount
        tx = self._record_transaction(account, "withdrawal", amount, account.currency, description)
        self.save()
        return asdict(tx)

    def transfer(self, from_account_id: str, to_account_id: str, amount: float, description: str = "Transfer") -> Dict[str, Any]:
        if from_account_id == to_account_id:
            raise BankError("Source and destination accounts must be different.")

        source = self.get_account(from_account_id)
        destination = self.get_account(to_account_id)

        if amount <= 0:
            raise BankError("Transfer amount must be positive.")
        if amount > source.balance:
            raise BankError("Insufficient funds for transfer.")
        if source.currency != destination.currency:
            raise BankError("Cross-currency transfers are not supported in this version.")

        source.balance -= amount
        destination.balance += amount

        source_tx = self._record_transaction(source, "transfer_out", amount, source.currency, description)
        destination_tx = self._record_transaction(destination, "transfer_in", amount, destination.currency, description)
        self.save()
        return {"from_account": source.account_id, "to_account": destination.account_id, "amount": amount, "currency": source.currency, "source_tx": asdict(source_tx), "destination_tx": asdict(destination_tx)}

    def create_loan(
        self,
        account_id: str,
        principal: float,
        term_months: int,
        interest_rate: float,
        description: str = "Business loan",
    ) -> Dict[str, Any]:
        account = self.get_account(account_id)
        if principal <= 0:
            raise BankError("Loan principal must be positive.")
        if term_months <= 0:
            raise BankError("Loan term must be greater than zero months.")
        if interest_rate < 0:
            raise BankError("Interest rate cannot be negative.")

        loan = Loan(
            loan_id=uuid4().hex[:10],
            account_id=account_id,
            principal=principal,
            term_months=term_months,
            interest_rate=interest_rate,
            outstanding_balance=principal,
            created_at=self._now(),
        )
        account.loans.append(loan)
        self.loans[loan.loan_id] = loan
        account.balance += principal
        self._record_transaction(account, "loan_disbursement", principal, account.currency, description)
        self.save()
        return asdict(loan)

    def get_statement(self, account_id: str) -> List[Dict[str, Any]]:
        account = self.get_account(account_id)
        return [asdict(txn) for txn in account.transactions]

    def list_customers(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        customers = list(self.customers.values())
        if country:
            customers = [customer for customer in customers if customer.country.lower() == country.lower()]
        return [asdict(customer) for customer in customers]

    def list_accounts(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        accounts = list(self.accounts.values())
        if customer_id:
            accounts = [account for account in accounts if account.customer_id == customer_id]
        return [asdict(account) for account in accounts]

    def get_summary(self) -> Dict[str, Any]:
        total_balances = sum(account.balance for account in self.accounts.values())
        active_accounts = sum(1 for account in self.accounts.values() if account.status == "active")
        total_customers = len(self.customers)
        total_loans = sum(loan.outstanding_balance for loan in self.loans.values())
        return {
            "total_customers": total_customers,
            "active_accounts": active_accounts,
            "total_balances": total_balances,
            "total_loans": total_loans,
            "currency_breakdown": {
                currency: round(sum(account.balance for account in self.accounts.values() if account.currency == currency), 2)
                for currency in sorted({account.currency for account in self.accounts.values()})
            },
        }
