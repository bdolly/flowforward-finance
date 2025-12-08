"""Tests for transaction CRUD operations."""

from datetime import datetime, timezone
from decimal import Decimal


class TestCreateTransaction:
    """Tests for transaction creation."""

    def test_create_transaction_expense(self, client, auth_headers, create_account):
        """Test creating an expense transaction."""
        account = create_account(balance="1000.00")
        transaction_data = {
            "account_id": account["id"],
            "transaction_type": "expense",
            "amount": "50.00",
            "description": "Grocery shopping",
            "category": "Food",
            "merchant": "Supermarket",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "expense"
        assert Decimal(data["amount"]) == Decimal("50.00")
        assert data["description"] == "Grocery shopping"
        assert data["category"] == "Food"
        assert data["account_id"] == account["id"]

        # Verify account balance was updated
        account_response = client.get(
            f"/api/v1/accounts/{account['id']}",
            headers=auth_headers,
        )
        assert Decimal(account_response.json()["balance"]) == Decimal("950.00")

    def test_create_transaction_income(self, client, auth_headers, create_account):
        """Test creating an income transaction."""
        account = create_account(balance="1000.00")
        transaction_data = {
            "account_id": account["id"],
            "transaction_type": "income",
            "amount": "500.00",
            "description": "Salary",
            "category": "Income",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers,
        )

        assert response.status_code == 201

        # Verify account balance increased
        account_response = client.get(
            f"/api/v1/accounts/{account['id']}",
            headers=auth_headers,
        )
        assert Decimal(account_response.json()["balance"]) == Decimal("1500.00")

    def test_create_transaction_invalid_account(self, client, auth_headers):
        """Test creating transaction with invalid account ID."""
        transaction_data = {
            "account_id": "invalid-account-id",
            "transaction_type": "expense",
            "amount": "50.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    def test_create_transaction_unauthorized(self, client, create_account):
        """Test transaction creation without authentication."""
        # Need to create account first with auth
        # This test verifies unauthenticated requests fail
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": "some-id",
                "transaction_type": "expense",
                "amount": "50.00",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
        )

        assert response.status_code == 401


class TestListTransactions:
    """Tests for listing transactions."""

    def test_list_transactions_empty(self, client, auth_headers):
        """Test listing transactions when none exist."""
        response = client.get("/api/v1/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_transactions_with_data(self, client, auth_headers, create_account):
        """Test listing transactions returns created transactions."""
        account = create_account()
        
        # Create transactions
        for i in range(3):
            client.post(
                "/api/v1/transactions",
                json={
                    "account_id": account["id"],
                    "transaction_type": "expense",
                    "amount": "10.00",
                    "description": f"Transaction {i}",
                    "transaction_date": datetime.now(timezone.utc).isoformat(),
                },
                headers=auth_headers,
            )

        response = client.get("/api/v1/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_transactions_filter_by_account(self, client, auth_headers, create_account):
        """Test filtering transactions by account."""
        account1 = create_account(name="Account 1")
        account2 = create_account(name="Account 2")

        # Create transactions in both accounts
        client.post(
            "/api/v1/transactions",
            json={
                "account_id": account1["id"],
                "transaction_type": "expense",
                "amount": "10.00",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/transactions",
            json={
                "account_id": account2["id"],
                "transaction_type": "expense",
                "amount": "20.00",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )

        response = client.get(
            "/api/v1/transactions",
            params={"account_id": account1["id"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["account_id"] == account1["id"]

    def test_list_transactions_filter_by_type(self, client, auth_headers, create_account):
        """Test filtering transactions by type."""
        account = create_account()

        # Create different transaction types
        client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "transaction_type": "expense",
                "amount": "10.00",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "transaction_type": "income",
                "amount": "100.00",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )

        response = client.get(
            "/api/v1/transactions",
            params={"transaction_type": "income"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["transaction_type"] == "income"

    def test_list_transactions_pagination(self, client, auth_headers, create_account):
        """Test transaction listing pagination."""
        account = create_account()

        # Create 5 transactions
        for i in range(5):
            client.post(
                "/api/v1/transactions",
                json={
                    "account_id": account["id"],
                    "transaction_type": "expense",
                    "amount": "10.00",
                    "transaction_date": datetime.now(timezone.utc).isoformat(),
                },
                headers=auth_headers,
            )

        response = client.get(
            "/api/v1/transactions",
            params={"page": 1, "page_size": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["total_pages"] == 3


class TestGetTransaction:
    """Tests for getting a single transaction."""

    def test_get_transaction_success(self, client, auth_headers, create_account):
        """Test getting a transaction by ID."""
        account = create_account()
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "transaction_type": "expense",
                "amount": "50.00",
                "description": "Test transaction",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        transaction = create_response.json()

        response = client.get(
            f"/api/v1/transactions/{transaction['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction["id"]
        assert data["description"] == "Test transaction"

    def test_get_transaction_not_found(self, client, auth_headers):
        """Test getting a non-existent transaction."""
        response = client.get(
            "/api/v1/transactions/non-existent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestUpdateTransaction:
    """Tests for updating transactions."""

    def test_update_transaction_description(self, client, auth_headers, create_account):
        """Test updating transaction description."""
        account = create_account()
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "transaction_type": "expense",
                "amount": "50.00",
                "description": "Original",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        transaction = create_response.json()

        response = client.patch(
            f"/api/v1/transactions/{transaction['id']}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_update_transaction_category(self, client, auth_headers, create_account):
        """Test updating transaction category."""
        account = create_account()
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "transaction_type": "expense",
                "amount": "50.00",
                "category": "Food",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        transaction = create_response.json()

        response = client.patch(
            f"/api/v1/transactions/{transaction['id']}",
            json={"category": "Entertainment"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["category"] == "Entertainment"


class TestDeleteTransaction:
    """Tests for deleting transactions."""

    def test_delete_transaction_success(self, client, auth_headers, create_account):
        """Test deleting a transaction reverses balance effect."""
        account = create_account(balance="1000.00")

        # Create expense transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "transaction_type": "expense",
                "amount": "100.00",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        transaction = create_response.json()

        # Verify balance decreased
        account_after_expense = client.get(
            f"/api/v1/accounts/{account['id']}",
            headers=auth_headers,
        )
        assert Decimal(account_after_expense.json()["balance"]) == Decimal("900.00")

        # Delete the transaction
        response = client.delete(
            f"/api/v1/transactions/{transaction['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Transaction deleted successfully"

        # Verify balance was restored
        account_after_delete = client.get(
            f"/api/v1/accounts/{account['id']}",
            headers=auth_headers,
        )
        assert Decimal(account_after_delete.json()["balance"]) == Decimal("1000.00")

    def test_delete_transaction_not_found(self, client, auth_headers):
        """Test deleting a non-existent transaction."""
        response = client.delete(
            "/api/v1/transactions/non-existent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

