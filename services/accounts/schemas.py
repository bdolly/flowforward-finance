"""Pydantic schemas for Accounts Service request/response validation."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# --- Enums ---


class AccountType(str, Enum):
    """Enumeration of supported account types."""

    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    CASH = "cash"
    OTHER = "other"


class AccountStatus(str, Enum):
    """Enumeration of account statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"
    PENDING = "pending"


class TransactionType(str, Enum):
    """Enumeration of transaction types."""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"


# --- Account Schemas ---


class AccountBase(BaseModel):
    """Base schema for Account."""

    name: str = Field(..., min_length=1, max_length=255)
    account_type: AccountType = AccountType.CHECKING
    institution: str | None = Field(None, max_length=255)
    account_number_masked: str | None = Field(None, max_length=50)
    currency: str = Field("USD", min_length=3, max_length=3)
    credit_limit: Decimal | None = None
    notes: str | None = None


class AccountCreate(AccountBase):
    """Schema for creating a new account."""

    balance: Decimal = Field(default=Decimal("0.00"))


class AccountUpdate(BaseModel):
    """Schema for updating an account."""

    name: str | None = Field(None, min_length=1, max_length=255)
    account_type: AccountType | None = None
    institution: str | None = Field(None, max_length=255)
    account_number_masked: str | None = Field(None, max_length=50)
    currency: str | None = Field(None, min_length=3, max_length=3)
    balance: Decimal | None = None
    credit_limit: Decimal | None = None
    status: AccountStatus | None = None
    notes: str | None = None


class AccountResponse(AccountBase):
    """Schema for account response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    balance: Decimal
    status: AccountStatus
    is_manual: bool
    created_at: datetime
    updated_at: datetime


class AccountSummary(BaseModel):
    """Schema for account summary (list view)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    account_type: AccountType
    institution: str | None
    currency: str
    balance: Decimal
    status: AccountStatus


# --- Transaction Schemas ---


class TransactionBase(BaseModel):
    """Base schema for Transaction."""

    transaction_type: TransactionType
    amount: Decimal = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    description: str | None = Field(None, max_length=500)
    category: str | None = Field(None, max_length=100)
    merchant: str | None = Field(None, max_length=255)
    reference_number: str | None = Field(None, max_length=100)
    transaction_date: datetime
    posted_date: datetime | None = None
    is_pending: bool = False
    notes: str | None = None


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""

    account_id: str
    transfer_account_id: str | None = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    transaction_type: TransactionType | None = None
    amount: Decimal | None = Field(None, gt=0)
    description: str | None = Field(None, max_length=500)
    category: str | None = Field(None, max_length=100)
    merchant: str | None = Field(None, max_length=255)
    transaction_date: datetime | None = None
    posted_date: datetime | None = None
    is_pending: bool | None = None
    notes: str | None = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    user_id: str
    transfer_account_id: str | None
    created_at: datetime
    updated_at: datetime


# --- Aggregate Schemas ---


class AccountWithTransactions(AccountResponse):
    """Account with recent transactions."""

    transactions: list[TransactionResponse] = []


class NetWorthSummary(BaseModel):
    """Net worth summary across all accounts."""

    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    currency: str = "USD"
    accounts_count: int


class AccountBalanceSummary(BaseModel):
    """Summary of balances by account type."""

    account_type: AccountType
    total_balance: Decimal
    accounts_count: int
    currency: str = "USD"


# --- Response Schemas ---


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str
    version: str


# --- Pagination Schemas ---


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedAccounts(PaginatedResponse):
    """Paginated accounts response."""

    items: list[AccountSummary]


class PaginatedTransactions(PaginatedResponse):
    """Paginated transactions response."""

    items: list[TransactionResponse]

