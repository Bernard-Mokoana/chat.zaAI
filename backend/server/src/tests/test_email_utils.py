from unittest.mock import MagicMock, patch

import pytest
from backend.server.src.utils.emailUtils import (
    build_email_verification_html,
    build_reset_password_html,
    create_email_transporter,
    send_email,
    send_email_verification,
)


class TestEmailUtils:
    @patch.dict(
        "os.environ",
        {
            "EMAIL_HOST": "smtp.mailtrap.io",
            "EMAIL_USER": "test_user",
            "EMAIL_PASSWORD": "test_password",
            "EMAIL_PORT": "2525",
            "EMAIL_SECURE": "false",
            "EMAIL_FROM": "bot@test.com",
        },
        clear=True,
    )
    def test_create_email_transporter_happy_path(self):
        config = create_email_transporter()
        assert config["host"] == "smtp.mailtrap.io"
        assert config["port"] == 2525
        assert config["secure"] is False

    @patch.dict("os.environ", {"EMAIL_PORT": "invalid-port"}, clear=True)
    def test_create_email_transporter_invalid_port(self):
        with pytest.raises(ValueError, match="EMAIL_PORT must be a valid integer"):
            create_email_transporter()

    @patch.dict("os.environ", {"EMAIL_PORT": "587"}, clear=True)
    def test_create_email_transporter_missing_host(self):
        with pytest.raises(
            ValueError, match="EMAIL_HOST environment variable is not set"
        ):
            create_email_transporter()

    @patch.dict(
        "os.environ", {"EMAIL_PORT": "587", "EMAIL_HOST": "smtp.test"}, clear=True
    )
    def test_create_email_transporter_missing_credentials(self):
        with pytest.raises(ValueError, match="Missing required environment variables"):
            create_email_transporter()

    @patch("backend.server.src.utils.emailUtils.smtplib.SMTP_SSL")
    def test_send_email_secure_happy_path(self, mock_smtp_ssl):
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        config = {
            "host": "smtp.test",
            "port": 465,
            "secure": True,
            "user": "u",
            "password": "p",
            "from": "bot@test.com",
        }

        send_email(config, "user@example.com", "Subject", "<p>Hi</p>")

        mock_server.login.assert_called_once_with("u", "p")
        mock_server.sendmail.assert_called_once()

    @patch("backend.server.src.utils.emailUtils.smtplib.SMTP")
    def test_send_email_non_secure_upgrades_to_tls(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        config = {
            "host": "smtp.test",
            "port": 587,
            "secure": False,
            "user": "u",
            "password": "p",
            "from": "bot@test.com",
        }

        send_email(config, "user@example.com", "Subject", "<p>Hi</p>")

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("u", "p")

    @patch.dict("os.environ", {"CORS_ORIGIN": "http://localhost:3000"})
    @patch("backend.server.src.utils.emailUtils.send_email")
    @patch("backend.server.src.utils.emailUtils.create_email_transporter")
    def test_send_email_verification(self, mock_transporter, mock_send_email):
        mock_transporter.return_value = {"from": "bot@test.com"}
        send_email_verification("test@example.com", "mock-token")
        mock_send_email.assert_called_once()

    def test_build_email_html_functions(self):
        html = build_email_verification_html("http://test.com/?t=1")
        assert 'href="http://test.com/?t=1"' in html  # Validates functional URL in href

        html_reset = build_reset_password_html("http://test.com/reset")
        assert "Reset Your Password" in html_reset
