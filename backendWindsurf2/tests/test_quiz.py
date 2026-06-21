"""
test_quiz.py – Quiz endpoint tests.
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.note import Note
from utils.security import hash_password, encrypt_text


@pytest.mark.asyncio
async def test_create_quiz(client: AsyncClient, test_db_session: AsyncSession, sample_user_data, sample_note_data):
    """Test quiz creation."""
    # Create user
    user = User(
        email=sample_user_data["email"],
        full_name=sample_user_data["full_name"],
        hashed_password=hash_password(sample_user_data["password"])
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Create note
    note = Note(
        user_id=user.id,
        original_filename=sample_note_data["original_filename"],
        file_type=sample_note_data["file_type"],
        cleaned_text_encrypted=encrypt_text(sample_note_data["cleaned_text"])
    )
    test_db_session.add(note)
    await test_db_session.commit()
    
    # Login to get token
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Create quiz
    quiz_data = {
        "note_id": str(note.id),
        "total_questions": 5,
        "mc_ratio": 0.8,
        "difficulty": "medium"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/quizzes", json=quiz_data, headers=headers)
    
    assert response.status_code == 202
    data = response.json()
    assert "quiz_id" in data
    assert data["status"] == "pending"
    assert "message" in data


@pytest.mark.asyncio
async def test_create_quiz_invalid_note(client: AsyncClient, test_db_session: AsyncSession, sample_user_data):
    """Test quiz creation with invalid note ID fails."""
    # Create user
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
    
    # Try to create quiz with non-existent note
    quiz_data = {
        "note_id": str(uuid.uuid4()),
        "total_questions": 5,
        "mc_ratio": 0.8,
        "difficulty": "medium"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/quizzes", json=quiz_data, headers=headers)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_quiz_no_content(client: AsyncClient, test_db_session: AsyncSession, sample_user_data, sample_note_data):
    """Test quiz creation with note that has no content fails."""
    # Create user
    user = User(
        email=sample_user_data["email"],
        full_name=sample_user_data["full_name"],
        hashed_password=hash_password(sample_user_data["password"])
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Create note without content
    note = Note(
        user_id=user.id,
        original_filename=sample_note_data["original_filename"],
        file_type=sample_note_data["file_type"],
        cleaned_text_encrypted=None
    )
    test_db_session.add(note)
    await test_db_session.commit()
    
    # Login to get token
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Try to create quiz
    quiz_data = {
        "note_id": str(note.id),
        "total_questions": 5,
        "mc_ratio": 0.8,
        "difficulty": "medium"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/quizzes", json=quiz_data, headers=headers)
    
    assert response.status_code == 400
    assert "without content" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_quiz_status(client: AsyncClient, test_db_session: AsyncSession, sample_user_data, sample_note_data):
    """Test getting quiz status."""
    # Create user
    user = User(
        email=sample_user_data["email"],
        full_name=sample_user_data["full_name"],
        hashed_password=hash_password(sample_user_data["password"])
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Create note
    note = Note(
        user_id=user.id,
        original_filename=sample_note_data["original_filename"],
        file_type=sample_note_data["file_type"],
        cleaned_text_encrypted=encrypt_text(sample_note_data["cleaned_text"])
    )
    test_db_session.add(note)
    await test_db_session.commit()
    
    # Login to get token
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Create quiz
    quiz_data = {
        "note_id": str(note.id),
        "total_questions": 5,
        "mc_ratio": 0.8,
        "difficulty": "medium"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    create_response = await client.post("/api/v1/quizzes", json=quiz_data, headers=headers)
    quiz_id = create_response.json()["quiz_id"]
    
    # Get quiz status
    response = await client.get(f"/api/v1/quizzes/{quiz_id}/status", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["quiz_id"] == quiz_id
    assert "status" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_list_quizzes(client: AsyncClient, test_db_session: AsyncSession, sample_user_data, sample_note_data):
    """Test listing user's quizzes."""
    # Create user
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
    
    # List quizzes (should be empty initially)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/quizzes", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_unauthorized_quiz_access(client: AsyncClient):
    """Test that unauthorized users cannot access quiz endpoints."""
    quiz_data = {
        "note_id": str(uuid.uuid4()),
        "total_questions": 5,
        "mc_ratio": 0.8,
        "difficulty": "medium"
    }
    
    # Try to create quiz without token
    response = await client.post("/api/v1/quizzes", json=quiz_data)
    assert response.status_code == 401
    
    # Try to list quizzes without token
    response = await client.get("/api/v1/quizzes")
    assert response.status_code == 401
    
    # Try to get quiz status without token
    response = await client.get(f"/api/v1/quizzes/{uuid.uuid4()}/status")
    assert response.status_code == 401
