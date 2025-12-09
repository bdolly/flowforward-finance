"""Account and transaction routes for Accounts Service."""

from datetime import datetime, timezone
from decimal import Decimal
from math import ceil

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from dependencies import AuthenticatedUser, DBSession
from models import Account, AccountBalanceHistory, BalanceSource, BalanceType, Transaction
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
    MessageResponse,
    NetWorthSummary,
    PaginatedAccounts,
)

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])

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
        notes=account_data.notes,
        status=AccountStatusModel.ACTIVE.value,
    )
    # TODO: create a new account balance history record
    
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
            Account.balance.label("total_balance"),
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


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: str,
    db: DBSession,
    current_user: AuthenticatedUser,
) -> AccountResponse:
    """
    Get a specific account by ID.

    Args:
        account_id: Account ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Account: Account data
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

    return account


@router.patch("/{account_id}", response_model=Account)
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