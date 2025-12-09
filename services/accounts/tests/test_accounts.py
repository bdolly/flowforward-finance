"""Tests for account CRUD operations."""

from decimal import Decimal


class TestCreateAccount:
    """Tests for account creation."""

    def test_create_account_success(self, client, auth_headers, account_data):
        """Test successful account creation."""
        response = client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == account_data["name"]
        assert data["account_type"] == account_data["account_type"]
        assert data["institution"] == account_data["institution"]
        assert data["currency"] == account_data["currency"]
        # assert Decimal(data["balance"]) == Decimal(account_data["balance"])
        assert data["status"] == "active"
        # assert data["is_manual"] is True
        assert "id" in data
        assert "user_id" in data

    def test_create_account_minimal_data(self, client, auth_headers):
        """Test account creation with minimal required data."""
        minimal_data = {"name": "Minimal Account"}

        response = client.post(
            "/api/v1/accounts",
            json=minimal_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Account"
        assert data["account_type"] == "checking"  # Default
        assert data["currency"] == "USD"  # Default
        # assert Decimal(data["balance"]) == Decimal("0.00")  # Default

    def test_create_account_unauthorized(self, client, account_data):
        """Test account creation without authentication fails."""
        response = client.post("/api/v1/accounts", json=account_data)

        assert response.status_code == 401

    def test_create_account_all_types(self, client, auth_headers):
        """Test creating accounts of all supported types."""
        account_types = [
            "checking",
            "savings",
            "credit_card",
            "investment",
            "loan",
            "mortgage",
            "cash",
            "other",
        ]

        for acc_type in account_types:
            response = client.post(
                "/api/v1/accounts",
                json={"name": f"Test {acc_type}", "account_type": acc_type},
                headers=auth_headers,
            )
            assert response.status_code == 201
            assert response.json()["account_type"] == acc_type


class TestListAccounts:
    """Tests for listing accounts."""

    def test_list_accounts_empty(self, client, auth_headers):
        """Test listing accounts when none exist."""
        response = client.get("/api/v1/accounts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_accounts_with_data(self, client, auth_headers, create_account):
        """Test listing accounts returns created accounts."""
        # Create multiple accounts
        account1 = create_account(name="Account 1")
        account2 = create_account(name="Account 2", account_type="savings")

        response = client.get("/api/v1/accounts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_accounts_filter_by_type(self, client, auth_headers, create_account):
        """Test filtering accounts by type."""
        create_account(name="Checking", account_type="checking")
        create_account(name="Savings", account_type="savings")

        response = client.get(
            "/api/v1/accounts",
            params={"account_type": "checking"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["account_type"] == "checking"

    def test_list_accounts_pagination(self, client, auth_headers, create_account):
        """Test account listing pagination."""
        # Create 5 accounts
        for i in range(5):
            create_account(name=f"Account {i}")

        # Get first page
        response = client.get(
            "/api/v1/accounts",
            params={"page": 1, "page_size": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["total_pages"] == 3


class TestGetAccount:
    """Tests for getting a single account."""

    def test_get_account_by_uuid_success(
        self, client, auth_headers, create_account
    ):
        """Test getting an account by UUID."""
        account = create_account(name="Test Account")

        response = client.get(
            f"/api/v1/accounts/{account['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account["id"]
        assert data["name"] == account["name"]

    def test_get_account_by_mask_success(
        self, client, auth_headers, create_account
    ):
        """Test getting an account by 4-digit masked account number."""
        account = create_account(
            name="Masked Account",
            account_number_masked="1234",
        )

        response = client.get(
            "/api/v1/accounts/1234",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account["id"]
        assert data["name"] == "Masked Account"

    def test_get_account_by_mask_not_found(self, client, auth_headers):
        """Test getting an account by mask that doesn't exist."""
        response = client.get(
            "/api/v1/accounts/9999",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    def test_get_account_by_uuid_not_found(self, client, auth_headers):
        """Test getting an account by UUID that doesn't exist."""
        # Use a valid UUID format that doesn't exist
        response = client.get(
            "/api/v1/accounts/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    def test_get_account_invalid_identifier(self, client, auth_headers):
        """Test getting an account with invalid identifier format."""
        # Not a valid UUID and not a 4-digit mask
        response = client.get(
            "/api/v1/accounts/invalid-id",
            headers=auth_headers,
        )

        assert response.status_code == 422
        # Pydantic validation error
        data = response.json()
        assert "detail" in data

    def test_get_account_invalid_mask_format(self, client, auth_headers):
        """Test getting an account with invalid mask (not exactly 4 digits)."""
        # 3 digits - not valid
        response = client.get(
            "/api/v1/accounts/123",
            headers=auth_headers,
        )

        assert response.status_code == 422

        # 5 digits - not valid (and not a UUID)
        response = client.get(
            "/api/v1/accounts/12345",
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_get_account_multiple_with_same_mask(
        self, client, auth_headers, create_account
    ):
        """Test behavior when multiple accounts have the same mask."""
        # Create two accounts with same mask (edge case)
        create_account(name="Account 1", account_number_masked="5678")
        create_account(name="Account 2", account_number_masked="5678")

        response = client.get(
            "/api/v1/accounts/5678",
            headers=auth_headers,
        )

        # Should return one account (first match)
        assert response.status_code == 200
        data = response.json()
        assert data["account_number_masked"] == "5678"


class TestUpdateAccount:
    """Tests for updating accounts."""

    def test_update_account_name(self, client, auth_headers, create_account):
        """Test updating account name."""
        account = create_account(name="Original Name")

        response = client.patch(
            f"/api/v1/accounts/{account['id']}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_update_account_balance(self, client, auth_headers, create_account):
        """Test updating account balance."""
        account = create_account(balance="1000.00")

        response = client.patch(
            f"/api/v1/accounts/{account['id']}",
            json={"balance": "2000.00"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert Decimal(response.json()["balance"]) == Decimal("2000.00")

    def test_update_account_status(self, client, auth_headers, create_account):
        """Test updating account status."""
        account = create_account()

        response = client.patch(
            f"/api/v1/accounts/{account['id']}",
            json={"status": "inactive"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "inactive"

    def test_update_account_not_found(self, client, auth_headers):
        """Test updating a non-existent account."""
        response = client.patch(
            "/api/v1/accounts/non-existent-id",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestDeleteAccount:
    """Tests for deleting accounts."""

    def test_delete_account_success(self, client, auth_headers, create_account):
        """Test soft-deleting an account."""
        account = create_account()

        response = client.delete(
            f"/api/v1/accounts/{account['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Account closed successfully"

        # Verify account is closed
        get_response = client.get(
            f"/api/v1/accounts/{account['id']}",
            headers=auth_headers,
        )
        assert get_response.json()["status"] == "closed"

    def test_delete_account_not_found(self, client, auth_headers):
        """Test deleting a non-existent account."""
        response = client.delete(
            "/api/v1/accounts/non-existent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestNetWorthSummary:
    """Tests for net worth summary."""

    def test_net_worth_summary_empty(self, client, auth_headers):
        """Test net worth summary with no accounts."""
        response = client.get("/api/v1/accounts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_assets"]) == Decimal("0.00")
        assert Decimal(data["total_liabilities"]) == Decimal("0.00")
        assert Decimal(data["net_worth"]) == Decimal("0.00")
        assert data["accounts_count"] == 0

    def test_net_worth_summary_with_accounts(self, client, auth_headers, create_account):
        """Test net worth summary calculation."""
        # Create asset accounts
        create_account(name="Checking", account_type="checking", balance="5000.00")
        create_account(name="Savings", account_type="savings", balance="10000.00")

        # Create liability accounts
        create_account(name="Credit Card", account_type="credit_card", balance="2000.00")

        response = client.get("/api/v1/accounts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_assets"]) == Decimal("15000.00")
        assert Decimal(data["total_liabilities"]) == Decimal("2000.00")
        assert Decimal(data["net_worth"]) == Decimal("13000.00")
        assert data["accounts_count"] == 3


class TestBalancesByType:
    """Tests for balances by type endpoint."""

    def test_balances_by_type(self, client, auth_headers, create_account):
        """Test getting balances grouped by account type."""
        create_account(name="Checking 1", account_type="checking", balance="1000.00")
        create_account(name="Checking 2", account_type="checking", balance="2000.00")
        create_account(name="Savings", account_type="savings", balance="5000.00")

        response = client.get("/api/v1/accounts/by-type", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Find checking summary
        checking = next(s for s in data if s["account_type"] == "checking")
        assert Decimal(checking["total_balance"]) == Decimal("3000.00")
        assert checking["accounts_count"] == 2

