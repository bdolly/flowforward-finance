"""SQLAlchemy models for Accounts Service."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PlaidAccountType(str, Enum):
    """Plaid account types."""
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER = "other"


class PlaidAccountSubtype(str, Enum):
    """Plaid account subtypes."""
    
    # Depository
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money market"
    CD = "cd"
    PREPAID = "prepaid"
    CASH_MANAGEMENT = "cash management"
    EBT = "ebt"
    
    # Credit
    CREDIT_CARD = "credit card"
    PAYPAL = "paypal"
    
    # Loan
    AUTO = "auto"
    BUSINESS = "business"
    COMMERCIAL = "commercial"
    CONSTRUCTION = "construction"
    CONSUMER = "consumer"
    HOME_EQUITY = "home equity"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    OVERDRAFT = "overdraft"
    LINE_OF_CREDIT = "line of credit"
    STUDENT = "student"
    
    # Investment
    BROKERAGE = "brokerage"
    CASH_ISA = "cash isa"
    CRYPTO_EXCHANGE = "crypto exchange"
    EDUCATION_SAVINGS_ACCOUNT = "education savings account"
    FIXED_ANNUITY = "fixed annuity"
    GIC = "gic"
    HEALTH_REIMBURSEMENT_ARRANGEMENT = "health reimbursement arrangement"
    HSA = "hsa"
    ISA = "isa"
    IRA = "ira"
    KEOGH = "keogh"
    LIF = "lif"
    LIFE_INSURANCE = "life insurance"
    LIRA = "lira"
    LRIF = "lrif"
    LRSP = "lrsp"
    MUTUAL_FUND = "mutual fund"
    NON_CUSTODIAL_WALLET = "non-custodial wallet"
    NON_TAXABLE_BROKERAGE_ACCOUNT = "non-taxable brokerage account"
    OTHER_ANNUITY = "other annuity"
    OTHER_INSURANCE = "other insurance"
    PENSION = "pension"
    PRIF = "prif"
    PROFIT_SHARING_PLAN = "profit sharing plan"
    QSHR = "qshr"
    RDSP = "rdsp"
    RESP = "resp"
    RETIREMENT = "retirement"
    RLIF = "rlif"
    ROTH = "roth"
    ROTH_401K = "roth 401k"
    RRIF = "rrif"
    RRSP = "rrsp"
    SARSEP = "sarsep"
    SEP_IRA = "sep ira"
    SIMPLE_IRA = "simple ira"
    SIPP = "sipp"
    STOCK_PLAN = "stock plan"
    TFSA = "tfsa"
    THRIFT_SAVINGS_PLAN = "thrift savings plan"
    TRUST = "trust"
    UGMA = "ugma"
    UTMA = "utma"
    VARIABLE_ANNUITY = "variable annuity"
    
    # Retirement specific (US employer-sponsored)
    PLAN_401A = "401a"
    PLAN_401K = "401k"
    PLAN_403B = "403b"
    PLAN_457B = "457b"
    PLAN_529 = "529"
    
    # Other
    PAYROLL = "payroll"
    OTHER = "other"



class PlaidAccountMixin:
    """
    Abstract mixin providing Plaid account fields.

    Maps to Plaid's Account object schema.
    See: https://plaid.com/docs/api/accounts/
    """

    # Plaid identifiers
    plaid_account_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="Plaid's unique account identifier",
    )
    plaid_connection_id: Mapped[str | None] = mapped_column(
        String(36),
        # ForeignKey("plaid_connections.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to Plaid Item/connection",
    )
    persistent_account_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Stable ID that persists across Items",
    )

    # Account identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Account name (user-assigned or from institution)",
    )
    official_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Official name from financial institution",
    )
    mask: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Last 2-4 digits of account number",
    )

    # Account classification
    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PlaidAccountType.DEPOSITORY.value,
        comment="depository, credit, loan, investment, other",
    )
    account_subtype: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="checking, savings, credit card, mortgage, etc.",
    )

    # Institution info
    institution_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Plaid institution ID",
    )
    institution_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Balances (flattened from Plaid's balances object)
    # TODO: extract to BalanceService
    # balance_available: Mapped[Decimal | None] = mapped_column(
    #     Numeric(precision=18, scale=2),
    #     nullable=True,
    #     comment="Available balance (spendable funds)",
    # )
    # balance_current: Mapped[Decimal | None] = mapped_column(
    #     Numeric(precision=18, scale=2),
    #     nullable=True,
    #     comment="Current balance",
    # )
    # balance_limit: Mapped[Decimal | None] = mapped_column(
    #     Numeric(precision=18, scale=2),
    #     nullable=True,
    #     comment="Credit limit (for credit accounts)",
    # )
    # iso_currency_code: Mapped[str | None] = mapped_column(
    #     String(3),
    #     nullable=True,
    #     default="USD",
    #     comment="ISO-4217 currency code",
    # )
    # unofficial_currency_code: Mapped[str | None] = mapped_column(
    #     String(20),
    #     nullable=True,
    #     comment="Unofficial currency for non-standard currencies",
    # )

    # Status
    verification_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="pending_automatic_verification, pending_manual_verification, verified",
    )