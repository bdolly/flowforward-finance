"""Initial accounts and account_balance_history tables

Revision ID: 001
Revises:
Create Date: 2024-12-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create accounts and account_balance_history tables."""
    # Create accounts table
    op.create_table(
        "accounts",
        # Primary key
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        # Plaid identifiers (from PlaidAccountMixin)
        sa.Column(
            "plaid_account_id",
            sa.String(100),
            nullable=False,
            unique=True,
            comment="Plaid's unique account identifier",
        ),
        sa.Column(
            "plaid_connection_id",
            sa.String(36),
            nullable=True,
            comment="Reference to Plaid Item/connection",
        ),
        sa.Column(
            "persistent_account_id",
            sa.String(100),
            nullable=True,
            comment="Stable ID that persists across Items",
        ),
        # Account identification
        sa.Column(
            "name",
            sa.String(255),
            nullable=False,
            comment="Account name (user-assigned or from institution)",
        ),
        sa.Column(
            "official_name",
            sa.String(255),
            nullable=True,
            comment="Official name from financial institution",
        ),
        sa.Column(
            "mask",
            sa.String(10),
            nullable=True,
            comment="Last 2-4 digits of account number",
        ),
        # Account classification
        sa.Column(
            "account_type",
            sa.String(50),
            nullable=False,
            server_default="depository",
            comment="depository, credit, loan, investment, other",
        ),
        sa.Column(
            "account_subtype",
            sa.String(50),
            nullable=True,
            comment="checking, savings, credit card, mortgage, etc.",
        ),
        # Institution info
        sa.Column(
            "institution_id",
            sa.String(50),
            nullable=True,
            comment="Plaid institution ID",
        ),
        sa.Column("institution_name", sa.String(255), nullable=True),
        # Status
        sa.Column(
            "verification_status",
            sa.String(50),
            nullable=True,
            comment="pending_automatic/manual_verification, verified",
        ),
        # Account-specific fields
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "is_emergency_fund",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        # Constraints
        sa.UniqueConstraint(
            "user_id", "plaid_account_id", name="uq_account_user_plaid"
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'closed', 'pending')",
            name="ck_valid_status",
        ),
    )

    # Create indexes for accounts table
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])
    op.create_index(
        "ix_accounts_plaid_account_id", "accounts", ["plaid_account_id"]
    )
    op.create_index(
        "ix_account_user_plaid", "accounts", ["user_id", "plaid_account_id"]
    )
    op.create_index(
        "ix_account_user_type", "accounts", ["user_id", "account_type"]
    )

    # Create account_balance_history table (Type 2 SCD)
    op.create_table(
        "account_balance_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(36),
            sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "balance",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
        ),
        sa.Column(
            "balance_type",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "valid_to",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "source",
            sa.String(50),
            nullable=False,
            server_default="plaid_sync",
        ),
        sa.Column(
            "plaid_last_updated",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Constraints
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_to > valid_from",
            name="ck_valid_to_after_valid_from",
        ),
        sa.CheckConstraint(
            "balance_type IN ('available', 'current')",
            name="ck_valid_balance_type",
        ),
        sa.CheckConstraint(
            "source IN "
            "('plaid_sync', 'manual_correction', 'system_adjustment')",
            name="ck_valid_source",
        ),
    )

    # Create indexes for account_balance_history table
    op.create_index(
        "ix_account_balance_history_account_id",
        "account_balance_history",
        ["account_id"],
    )
    op.create_index(
        "ix_account_balance_history_valid_from",
        "account_balance_history",
        ["valid_from"],
    )
    op.create_index(
        "ix_account_balance_history_valid_to",
        "account_balance_history",
        ["valid_to"],
    )
    op.create_index(
        "ix_account_balance_history_is_current",
        "account_balance_history",
        ["is_current"],
    )
    op.create_index(
        "ix_balance_history_temporal",
        "account_balance_history",
        ["account_id", "balance_type", "valid_from"],
    )
    # Partial unique index for current records (PostgreSQL-specific)
    op.create_index(
        "ix_balance_history_current",
        "account_balance_history",
        ["account_id", "balance_type"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )


def downgrade() -> None:
    """Drop accounts and account_balance_history tables."""
    # Drop account_balance_history indexes
    op.drop_index(
        "ix_balance_history_current", table_name="account_balance_history"
    )
    op.drop_index(
        "ix_balance_history_temporal", table_name="account_balance_history"
    )
    op.drop_index(
        "ix_account_balance_history_is_current",
        table_name="account_balance_history",
    )
    op.drop_index(
        "ix_account_balance_history_valid_to",
        table_name="account_balance_history",
    )
    op.drop_index(
        "ix_account_balance_history_valid_from",
        table_name="account_balance_history",
    )
    op.drop_index(
        "ix_account_balance_history_account_id",
        table_name="account_balance_history",
    )
    op.drop_table("account_balance_history")

    # Drop accounts indexes
    op.drop_index("ix_account_user_type", table_name="accounts")
    op.drop_index("ix_account_user_plaid", table_name="accounts")
    op.drop_index("ix_accounts_plaid_account_id", table_name="accounts")
    op.drop_index("ix_accounts_user_id", table_name="accounts")
    op.drop_table("accounts")
