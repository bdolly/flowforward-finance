"""Account and transaction routes for Accounts Service."""

from datetime import datetime, timezone
from decimal import Decimal
from math import ceil

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from dependencies import AuthenticatedUser, DBSession
from models import Account, Transaction
from models import AccountStatus as AccountStatusModel
from models import TransactionType as TransactionTypeModel
from schemas import (
    AccountBalanceSummary,
    AccountCreate,
    AccountResponse,
    AccountStatus,
    AccountSummary,
    AccountType,
    AccountUpdate,
    AccountWithTransactions,
    MessageResponse,
    NetWorthSummary,
    PaginatedAccounts,
    PaginatedTransactions,
    TransactionCreate,
    TransactionResponse,
    TransactionType,
    TransactionUpdate,
)

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])
transaction_router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


# --- Account Endpoints ---


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> Account:
    """
    Create a new financial account.

    Args:
        account_data: Account creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        AccountResponse: Created account data
    """
    account = Account(
        user_id=current_user.id,
        name=account_data.name,
        account_type=account_data.account_type.value,
        institution=account_data.institution,
        account_number_masked=account_data.account_number_masked,
        currency=account_data.currency,
        balance=account_data.balance,
        credit_limit=account_data.credit_limit,
        notes=account_data.notes,
        status=AccountStatusModel.ACTIVE.value,
        is_manual=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.get("", response_model=PaginatedAccounts)
def list_accounts(
    db: DBSession,
    current_user: AuthenticatedUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    account_type: AccountType | None = None,
    status: AccountStatus | None = None,
) -> PaginatedAccounts:
    """
    List all accounts for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user
        page: Page number (1-indexed)
        page_size: Number of items per page
        account_type: Filter by account type
        status: Filter by account status

    Returns:
        PaginatedAccounts: Paginated list of accounts
    """
    query = db.query(Account).filter(Account.user_id == current_user.id)

    if account_type:
        query = query.filter(Account.account_type == account_type.value)
    if status:
        query = query.filter(Account.status == status.value)

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1

    accounts = (
        query.order_by(Account.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedAccounts(
        items=[AccountSummary.model_validate(acc) for acc in accounts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/summary", response_model=NetWorthSummary)
def get_net_worth_summary(
    db: DBSession,
    current_user: AuthenticatedUser,
) -> NetWorthSummary:
    """
    Get net worth summary across all accounts.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        NetWorthSummary: Summary of assets, liabilities, and net worth
    """
    accounts = (
        db.query(Account)
        .filter(
            Account.user_id == current_user.id,
            Account.status == AccountStatusModel.ACTIVE.value,
        )
        .all()
    )

    # Asset account types
    asset_types = {
        AccountType.CHECKING.value,
        AccountType.SAVINGS.value,
        AccountType.INVESTMENT.value,
        AccountType.CASH.value,
    }

    # Liability account types
    liability_types = {
        AccountType.CREDIT_CARD.value,
        AccountType.LOAN.value,
        AccountType.MORTGAGE.value,
    }

    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")

    for account in accounts:
        if account.account_type in asset_types:
            total_assets += account.balance
        elif account.account_type in liability_types:
            # For credit cards/loans, balance is typically negative or represents debt
            total_liabilities += abs(account.balance)

    return NetWorthSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=total_assets - total_liabilities,
        currency="USD",
        accounts_count=len(accounts),
    )


@router.get("/by-type", response_model=list[AccountBalanceSummary])
def get_balances_by_type(
    db: DBSession,
    current_user: AuthenticatedUser,
) -> list[AccountBalanceSummary]:
    """
    Get balance summary grouped by account type.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        list[AccountBalanceSummary]: List of balance summaries by type
    """
    results = (
        db.query(
            Account.account_type,
            func.sum(Account.balance).label("total_balance"),
            func.count(Account.id).label("accounts_count"),
        )
        .filter(
            Account.user_id == current_user.id,
            Account.status == AccountStatusModel.ACTIVE.value,
        )
        .group_by(Account.account_type)
        .all()
    )

    return [
        AccountBalanceSummary(
            account_type=AccountType(row.account_type),
            total_balance=row.total_balance or Decimal("0.00"),
            accounts_count=row.accounts_count,
        )
        for row in results
    ]


@router.get("/{account_id}", response_model=AccountWithTransactions)
def get_account(
    account_id: str,
    db: DBSession,
    current_user: AuthenticatedUser,
    include_transactions: bool = Query(True),
    transaction_limit: int = Query(10, ge=1, le=100),
) -> AccountWithTransactions:
    """
    Get a specific account by ID.

    Args:
        account_id: Account ID
        db: Database session
        current_user: Current authenticated user
        include_transactions: Whether to include recent transactions
        transaction_limit: Number of recent transactions to include

    Returns:
        AccountWithTransactions: Account data with optional transactions
    """
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    response = AccountWithTransactions.model_validate(account)

    if include_transactions:
        transactions = (
            db.query(Transaction)
            .filter(Transaction.account_id == account_id)
            .order_by(Transaction.transaction_date.desc())
            .limit(transaction_limit)
            .all()
        )
        response.transactions = [
            TransactionResponse.model_validate(t) for t in transactions
        ]

    return response


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    account_data: AccountUpdate,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> Account:
    """
    Update an existing account.

    Args:
        account_id: Account ID
        account_data: Account update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        AccountResponse: Updated account data
    """
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    update_data = account_data.model_dump(exclude_unset=True)

    # Convert enum values to strings for database storage
    if "account_type" in update_data and update_data["account_type"]:
        update_data["account_type"] = update_data["account_type"].value
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].value

    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return account


@router.delete("/{account_id}", response_model=MessageResponse)
def delete_account(
    account_id: str,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> MessageResponse:
    """
    Delete an account (soft delete by changing status to closed).

    Args:
        account_id: Account ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Deletion confirmation message
    """
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Soft delete by changing status
    account.status = AccountStatusModel.CLOSED.value
    db.commit()

    return MessageResponse(message="Account closed successfully")


# --- Transaction Endpoints ---


@transaction_router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
def create_transaction(
    transaction_data: TransactionCreate,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> Transaction:
    """
    Create a new transaction.

    Args:
        transaction_data: Transaction creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        TransactionResponse: Created transaction data
    """
    # Verify account belongs to user
    account = (
        db.query(Account)
        .filter(
            Account.id == transaction_data.account_id,
            Account.user_id == current_user.id,
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Verify transfer account if specified
    if transaction_data.transfer_account_id:
        transfer_account = (
            db.query(Account)
            .filter(
                Account.id == transaction_data.transfer_account_id,
                Account.user_id == current_user.id,
            )
            .first()
        )
        if not transfer_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer account not found",
            )

    transaction = Transaction(
        account_id=transaction_data.account_id,
        user_id=current_user.id,
        transaction_type=transaction_data.transaction_type.value,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        description=transaction_data.description,
        category=transaction_data.category,
        merchant=transaction_data.merchant,
        reference_number=transaction_data.reference_number,
        transaction_date=transaction_data.transaction_date,
        posted_date=transaction_data.posted_date,
        is_pending=transaction_data.is_pending,
        transfer_account_id=transaction_data.transfer_account_id,
        notes=transaction_data.notes,
    )

    # Update account balance
    _update_account_balance(db, account, transaction_data.transaction_type, transaction_data.amount)

    # Handle transfer if applicable
    if transaction_data.transfer_account_id and transfer_account:
        # Create corresponding transaction in transfer account
        transfer_type = (
            TransactionType.INCOME
            if transaction_data.transaction_type == TransactionType.EXPENSE
            else TransactionType.EXPENSE
        )
        _update_account_balance(db, transfer_account, transfer_type, transaction_data.amount)

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def _update_account_balance(
    db: Session,
    account: Account,
    transaction_type: TransactionType,
    amount: Decimal,
) -> None:
    """Update account balance based on transaction type."""
    if transaction_type == TransactionType.INCOME:
        account.balance += amount
    elif transaction_type == TransactionType.EXPENSE:
        account.balance -= amount
    elif transaction_type == TransactionType.ADJUSTMENT:
        account.balance = amount  # Adjustment sets the balance directly


@transaction_router.get("", response_model=PaginatedTransactions)
def list_transactions(
    db: DBSession,
    current_user: AuthenticatedUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    account_id: str | None = None,
    transaction_type: TransactionType | None = None,
    category: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> PaginatedTransactions:
    """
    List transactions for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user
        page: Page number (1-indexed)
        page_size: Number of items per page
        account_id: Filter by account ID
        transaction_type: Filter by transaction type
        category: Filter by category
        start_date: Filter transactions after this date
        end_date: Filter transactions before this date

    Returns:
        PaginatedTransactions: Paginated list of transactions
    """
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type.value)
    if category:
        query = query.filter(Transaction.category == category)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1

    transactions = (
        query.order_by(Transaction.transaction_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedTransactions(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@transaction_router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> Transaction:
    """
    Get a specific transaction by ID.

    Args:
        transaction_id: Transaction ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        TransactionResponse: Transaction data
    """
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@transaction_router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: str,
    transaction_data: TransactionUpdate,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> Transaction:
    """
    Update an existing transaction.

    Args:
        transaction_id: Transaction ID
        transaction_data: Transaction update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        TransactionResponse: Updated transaction data
    """
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    update_data = transaction_data.model_dump(exclude_unset=True)

    # Handle amount change - update account balance
    if "amount" in update_data or "transaction_type" in update_data:
        account = db.query(Account).filter(Account.id == transaction.account_id).first()
        if account:
            # Reverse old transaction effect
            old_type = TransactionType(transaction.transaction_type)
            if old_type == TransactionType.INCOME:
                account.balance -= transaction.amount
            elif old_type == TransactionType.EXPENSE:
                account.balance += transaction.amount

            # Apply new transaction effect
            new_type = update_data.get("transaction_type", old_type)
            new_amount = update_data.get("amount", transaction.amount)
            if isinstance(new_type, TransactionType):
                new_type = new_type
            else:
                new_type = TransactionType(new_type) if new_type else old_type

            if new_type == TransactionType.INCOME:
                account.balance += new_amount
            elif new_type == TransactionType.EXPENSE:
                account.balance -= new_amount

    # Convert enum values to strings
    if "transaction_type" in update_data and update_data["transaction_type"]:
        update_data["transaction_type"] = update_data["transaction_type"].value

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)

    return transaction


@transaction_router.delete("/{transaction_id}", response_model=MessageResponse)
def delete_transaction(
    transaction_id: str,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> MessageResponse:
    """
    Delete a transaction.

    Args:
        transaction_id: Transaction ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Deletion confirmation message
    """
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # Reverse the transaction effect on account balance
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    if account:
        if transaction.transaction_type == TransactionTypeModel.INCOME.value:
            account.balance -= transaction.amount
        elif transaction.transaction_type == TransactionTypeModel.EXPENSE.value:
            account.balance += transaction.amount

    db.delete(transaction)
    db.commit()

    return MessageResponse(message="Transaction deleted successfully")

