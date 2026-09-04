from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .repositories import UserRepository


class AuthApiTestCase(TestCase):
    """Test the authentication contract used by the API."""

    login_url = "/api/auth/login/"
    refresh_url = "/api/auth/refresh/"
    username: str
    password: str
    user: AbstractBaseUser

    @classmethod
    def setUpTestData(cls) -> None:
        user_model = get_user_model()
        cls.username = "test-user"
        cls.password = "correct-password"
        cls.user = user_model.objects.create(
            username=cls.username,
        )
        cls.user.set_password(cls.password)
        cls.user.save()

    def setUp(self) -> None:
        self.client = APIClient()

    def _login(self) -> dict[str, str]:
        response = self.client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens: dict[str, str] = response.json()
        return tokens

    def test_login_returns_tokens(self) -> None:
        tokens = self._login()

        self.assertIsInstance(tokens.get("access"), str)
        self.assertTrue(tokens["access"])
        self.assertIsInstance(tokens.get("refresh"), str)
        self.assertTrue(tokens["refresh"])

    def test_login_with_invalid_password_fails(self) -> None:
        response = self.client.post(
            self.login_url,
            {"username": self.username, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response_data: dict[str, str] = response.json()
        self.assertNotIn("access", response_data)
        self.assertNotIn("refresh", response_data)

    def test_refresh_returns_new_access_token(self) -> None:
        tokens = self._login()

        response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: dict[str, str] = response.json()
        self.assertIsInstance(response_data.get("access"), str)
        self.assertTrue(response_data["access"])


class UserRepositoryTests(TestCase):
    def test_is_exists_returns_true_for_existing_user(self) -> None:
        user = get_user_model().objects.create_user(username="existing-user")

        self.assertTrue(UserRepository().is_exists(user.pk))

    def test_is_exists_returns_false_for_missing_user(self) -> None:
        self.assertFalse(UserRepository().is_exists(999999))
