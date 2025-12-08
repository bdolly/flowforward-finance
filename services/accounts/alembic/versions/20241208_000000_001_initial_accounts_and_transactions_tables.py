"""Initial accounts and transactions tables

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
    """Create accounts and transactions tables."""
    # Create accounts table
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), index=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=False, default="checking"),
        sa.Column("institution", sa.String(255), nullable=True),
        sa.Column("account_number_masked", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, default="USD"),
        sa.Column(
            "balance",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            default=0.00,
        ),
        sa.Column(
            "credit_limit",
            sa.Numeric(precision=18, scale=2),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("is_manual", sa.Boolean(), default=True, nullable=False),
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
    )

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(36),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.String(36), index=True, nullable=False),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
        ),
        sa.Column("currency", sa.String(3), nullable=False, default="USD"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("merchant", sa.String(255), nullable=True),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("posted_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_pending", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "transfer_account_id",
            sa.String(36),
            sa.ForeignKey("accounts.id", ondelete="SET NULL"),
            nullable=True,
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
    )

    # Create additional indexes for common queries
    op.create_index(
        "ix_transactions_category",
        "transactions",
        ["category"],
    )
    op.create_index(
        "ix_transactions_transaction_date",
        "transactions",
        ["transaction_date"],
    )
    op.create_index(
        "ix_accounts_status",
        "accounts",
        ["status"],
    )


def downgrade() -> None:
    """Drop accounts and transactions tables."""
    op.drop_index("ix_accounts_status", table_name="accounts")
    op.drop_index("ix_transactions_transaction_date", table_name="transactions")
    op.drop_index("ix_transactions_category", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("accounts")

