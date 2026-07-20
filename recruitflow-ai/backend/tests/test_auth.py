import pytest
from fastapi import HTTPException

from app.auth import authenticate, current_user
from app.config import Settings
from app.schemas import LoginRequest


def test_signed_login_token_round_trip() -> None:
    settings = Settings(auth_secret="test-secret")
    login = authenticate(
        LoginRequest(username=settings.demo_department_username, password=settings.demo_department_password),
        settings,
    )

    user = current_user(f"Bearer {login.access_token}", settings)

    assert user.role == "department"
    assert user.display_name == "Department Demo"


def test_login_binds_approver_name_to_signed_identity() -> None:
    settings = Settings(auth_secret="test-secret")
    login = authenticate(
        LoginRequest(
            username=settings.demo_department_username,
            password=settings.demo_department_password,
            display_name="李审批",
        ),
        settings,
    )

    user = current_user(f"Bearer {login.access_token}", settings)

    assert user.display_name == "李审批"
    assert user.username == settings.demo_department_username
    assert user.role == "department"


def test_invalid_login_token_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        current_user("Bearer invalid.token", Settings(auth_secret="test-secret"))

    assert error.value.status_code == 401
