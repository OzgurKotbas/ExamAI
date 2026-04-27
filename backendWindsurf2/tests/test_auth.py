"""
test_auth.py – Authentication endpoint tests.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from utils.security import hash_password


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, test_db_session: AsyncSession):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "newpassword123"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == user_data["email"]
    assert data["user"]["full_name"] == user_data["full_name"]
    assert "id" in data["user"]
    
    # Verify user was created in database
    user = await test_db_session.get(User, data["user"]["id"])
    assert user is not None
    assert user.email == user_data["email"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email fails."""
    user_data = {
        "email": "duplicate@example.com",
        "full_name": "Duplicate User",
        "password": "password123"
    }
    
    # First registration should succeed
    response1 = await client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201
    
    # Second registration should fail
    response2 = await client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, test_db_session: AsyncSession, sample_user_data):
    """Test user login."""
    # Create user first
    user = User(
        email=sample_user_data["email"],
        full_name=sample_user_data["full_name"],
        hashed_password=hash_password(sample_user_data["password"])
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Login
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == sample_user_data["email"]


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials fails."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "invalid credentials" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_db_session: AsyncSession, sample_user_data):
    """Test getting current user profile."""
    # Create and login user
    user = User(
        email=sample_user_data["email"],
        full_name=sample_user_data["full_name"],
        hashed_password=hash_password(sample_user_data["password"])
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Login to get token
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == sample_user_data["email"]
    assert data["full_name"] == sample_user_data["full_name"]


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token fails."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user without token fails."""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 401
