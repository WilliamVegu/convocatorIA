"""Unit tests for GitHub Adapter auditing public candidate profiles."""
from unittest.mock import patch, MagicMock
from src.adapters.github.github_adapter import GitHubAdapter


def test_github_adapter_clean_username():
    adapter = GitHubAdapter()
    assert adapter._clean_username("https://github.com/torvalds") == "torvalds"
    assert adapter._clean_username("github.com/torvalds/") == "torvalds"
    assert adapter._clean_username("@torvalds") == "torvalds"
    assert adapter._clean_username("torvalds") == "torvalds"


def test_github_adapter_audit_success():
    adapter = GitHubAdapter()

    user_resp_mock = MagicMock()
    user_resp_mock.status_code = 200
    user_resp_mock.json.return_value = {
        "login": "octocat",
        "public_repos": 8,
        "followers": 42,
    }

    repos_resp_mock = MagicMock()
    repos_resp_mock.status_code = 200
    repos_resp_mock.json.return_value = [
        {"name": "repo1", "fork": False, "language": "Python", "stargazers_count": 10},
        {"name": "repo2", "fork": False, "language": "Python", "stargazers_count": 5},
        {"name": "repo3", "fork": False, "language": "Java", "stargazers_count": 2},
        {"name": "repo4", "fork": True, "language": "Go", "stargazers_count": 0},
    ]

    with patch("requests.get") as mock_get:
        def side_effect(url, **kwargs):
            if "repos" in url:
                return repos_resp_mock
            return user_resp_mock

        mock_get.side_effect = side_effect
        audit = adapter.audit_user("https://github.com/octocat")

        assert audit.username == "octocat"
        assert audit.existe is True
        assert audit.repos_propios == 3
        assert audit.repos_forks == 1
        assert audit.stars_totales == 17
        assert "Python" in audit.lenguajes_principales
        assert "Java" in audit.lenguajes_principales


def test_github_adapter_audit_not_found():
    adapter = GitHubAdapter()

    user_resp_mock = MagicMock()
    user_resp_mock.status_code = 404

    with patch("requests.get", return_value=user_resp_mock):
        audit = adapter.audit_user("usuario_inexistente_12345")
        assert audit.existe is False
        assert "no encontrado" in audit.resumen_actividad.lower()

