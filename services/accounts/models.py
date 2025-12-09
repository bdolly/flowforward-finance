"""SQLAlchemy models for Accounts Service."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from time import timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from PlaidAccountModels import PlaidAccountMixin


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


class Account(PlaidAccountMixin, Base):
    """Financial account model."""

    __tablename__ = "accounts"

    __table_args__ = (
        # Unique constraint: one plaid_id per user
        UniqueConstraint(
            "user_id",
            "plaid_account_id",
            name="uq_account_user_plaid",
        ),
        CheckConstraint(
            f"status IN ({', '.join([f'\'{status.value}\'' for status in AccountStatus])})",
            name="ck_valid_status",
        ),
        # Composite indexes for common query patterns
        Index("ix_account_user_plaid", "user_id", "plaid_account_id"),
        Index("ix_account_user_type", "user_id", "account_type"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AccountStatus.ACTIVE.value,
    )
    is_emergency_fund: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships

    balance_history: Mapped[list["AccountBalanceHistory"]] = relationship(
        "AccountBalanceHistory",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    # get method for balance that gets the current balance from the balance history
    @property
    def balance(self) -> Decimal:
        """Get the current balance for the account."""
        return self.balance_history.filter(AccountBalanceHistory.is_current == True).first().balance

    def __repr__(self) -> str:
        """Return string representation of Account."""
        return f"<Account(id={self.id}, name={self.name})>"


class BalanceType(str, Enum):
    """Enumeration of balance types from Plaid."""

    AVAILABLE = "available"
    CURRENT = "current"


class BalanceSource(str, Enum):
    """Enumeration of balance snapshot sources."""

    PLAID_SYNC = "plaid_sync"
    MANUAL_CORRECTION = "manual_correction"
    SYSTEM_ADJUSTMENT = "system_adjustment"


class AccountBalanceHistory(Base):
    """
    Type 2 Slowly Changing Dimension for account balance tracking.

    This model tracks balance snapshots from Plaid syncs, eliminating the need
    for balance adjustment transactions. Each record represents a point-in-time
    balance snapshot with temporal validity.

    Design Pattern: Slowly Changing Dimension Type 2
    - Maintains full history of balance changes
    - Uses valid_from/valid_to for temporal queries
    - Enables point-in-time balance reconstruction
    - Single is_current=True record per account
    """

    __tablename__ = "account_balance_history"

    __table_args__ = (
        # Ensure valid_to > valid_from when valid_to is set
        CheckConstraint(
            "valid_to IS NULL OR valid_to > valid_from",
            name="ck_valid_to_after_valid_from",
        ),
        # Ensure balance_type is valid
        CheckConstraint(
            f"balance_type IN ({', '.join([f'\'{balance_type.value}\'' for balance_type in BalanceType])})",
            name="ck_valid_balance_type",
        ),
        # Ensure source is valid
        CheckConstraint(
            f"source IN ({', '.join([f'\'{source.value}\'' for source in BalanceSource])})",
            name="ck_valid_source",
        ),
        # Composite index for temporal queries
        Index(
            "ix_balance_history_temporal",
            "account_id",
            "balance_type",
            "valid_from",
        ),
        # Partial unique index: one current record per account + balance_type
        Index(
            "ix_balance_history_current",
            "account_id",
            "balance_type",
            unique=True,
            postgresql_where="is_current = true",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=BalanceSource.PLAID_SYNC.value,
    )
    plaid_last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        "metadata",
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

  
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="balance_history",
    )

    def __repr__(self) -> str:
        """Return string representation of AccountBalanceHistory."""
        return (
            f"<AccountBalanceHistory(id={self.id}, "
            f"account_id={self.account_id}, balance={self.balance})>"
        )