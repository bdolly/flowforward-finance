"""Pydantic schemas for Accounts Service request/response validation."""

import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Union
from uuid import UUID

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


class BalanceType(str, Enum):
    """Enumeration of balance types from Plaid."""

    AVAILABLE = "available"
    CURRENT = "current"


class BalanceSource(str, Enum):
    """Enumeration of balance snapshot sources."""

    PLAID_SYNC = "plaid_sync"
    MANUAL_CORRECTION = "manual_correction"
    SYSTEM_ADJUSTMENT = "system_adjustment"


# --- Account Identifier (UUID or Mask) ---

MASK_PATTERN = re.compile(r"^\d{4}$")


class AccountIdentifier:
    """
    Parsed account identifier - either a UUID or a 4-digit masked account number.
    
    Used for path parameters that accept either format.
    """

    __slots__ = ("value", "is_mask")

    def __init__(self, value: str, is_mask: bool = False):
        self.value = value
        self.is_mask = is_mask

    @classmethod
    def __get_validators__(cls):
        """Pydantic v1 compatibility."""
        yield cls.validate

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """Pydantic v2 schema definition for path parameter support."""
        from pydantic_core import core_schema

        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v) -> "AccountIdentifier":
        """Validate and parse string into AccountIdentifier."""
        if isinstance(v, cls):
            return v

        if not isinstance(v, str):
            raise ValueError("Account identifier must be a string")

        # Check for 4-digit mask pattern
        if MASK_PATTERN.match(v):
            return cls(value=v, is_mask=True)

        # Validate as UUID
        try:
            uuid_obj = UUID(v)
            return cls(value=str(uuid_obj), is_mask=False)
        except ValueError:
            raise ValueError(
                "Account identifier must be a valid UUID or 4-digit account mask"
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"AccountIdentifier(value={self.value!r}, is_mask={self.is_mask})"


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


# --- Account Balance History Schemas (SCD Type 2) ---


class AccountBalanceHistoryBase(BaseModel):
    """
    Base schema for AccountBalanceHistory.

    Type 2 Slowly Changing Dimension for account balance tracking.
    Each record represents a point-in-time balance snapshot with temporal validity.
    """

    balance: Decimal = Field(
        ...,
        max_digits=15,
        decimal_places=2,
        description="Balance value from Plaid at this point in time",
    )
    balance_type: BalanceType = Field(
        ...,
        description="Type of balance: 'available' for checking/savings, 'current' for credit/loans",
    )
    valid_from: datetime = Field(
        ...,
        description="Timestamp when this balance became effective",
    )
    valid_to: datetime | None = Field(
        None,
        description="Timestamp when this balance was superseded (NULL if current)",
    )
    is_current: bool = Field(
        True,
        description="Whether this is the current active snapshot (only one per account)",
    )
    source: BalanceSource = Field(
        BalanceSource.PLAID_SYNC,
        description="Origin of this balance snapshot",
    )
    plaid_last_updated: datetime | None = Field(
        None,
        description="Timestamp from Plaid indicating when balance was last updated at institution",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Audit trail and sync details (original_balance, sync_datetime, etc.)",
    )


class AccountBalanceHistoryCreate(AccountBalanceHistoryBase):
    """Schema for creating a new account balance history record."""

    account_id: str = Field(
        ...,
        description="Account this balance snapshot belongs to",
    )


class AccountBalanceHistoryUpdate(BaseModel):
    """Schema for updating an account balance history record."""

    valid_to: datetime | None = None
    is_current: bool | None = None
    metadata: dict | None = None


class AccountBalanceHistoryResponse(AccountBalanceHistoryBase):
    """Schema for account balance history response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    created_at: datetime = Field(
        ...,
        description="When this record was created in our system",
    )


class AccountBalanceHistorySummary(BaseModel):
    """Schema for account balance history summary (list view)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    balance: Decimal
    balance_type: BalanceType
    valid_from: datetime
    valid_to: datetime | None
    is_current: bool
    source: BalanceSource


# --- Aggregate Schemas ---


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


# class PaginatedTransactions(PaginatedResponse):
#     """Paginated transactions response."""

#     items: list[TransactionResponse]


class PaginatedAccountBalanceHistory(PaginatedResponse):
    """Paginated account balance history response."""

    items: list[AccountBalanceHistorySummary]

