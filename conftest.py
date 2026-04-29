import pytest
from django.test import Client
from accounts.models import CustomUser


@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(
        email="test@example.com",
        password="password123",
        role=CustomUser.Role.USER
    )

@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_superuser(
        email="admin@example.com",
        password="password123",
        role=CustomUser.Role.ADMIN
    )

@pytest.fixture
def staff_vendor(db):
    return CustomUser.objects.create_user(
        email="staff@example.com",
        password="password123",
        role=CustomUser.Role.VENDOR,
        is_staff=True
    )
