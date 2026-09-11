"""GitHub public API adapter for automated candidate portfolio auditing."""
from __future__ import annotations

import re
from typing import Dict, Any, List
import requests

from src.ports.github_port import GitHubPort
from src.domain.entities import GitHubAudit
from src.logger import logger


class GitHubAdapter(GitHubPort):
    """Adapter consuming public GitHub REST API without requiring enterprise credentials."""

    def __init__(self, timeout_seconds: int = 5):
        self.timeout = timeout_seconds
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TCS-ATS-Recruitment-Auditor/1.0",
        }

    def _clean_username(self, username_or_url: str) -> str:
        """Extract clean username from string, handle URLs or @ mentions."""
        raw = username_or_url.strip()
        # Remove trailing slash
        raw = raw.rstrip("/")
        # Extract from URL
        if "github.com/" in raw:
            parts = raw.split("github.com/")
            raw = parts[-1].split("/")[0]
        # Remove @ symbol
        raw = raw.lstrip("@")
        return raw.strip()

    def audit_user(self, username_or_url: str) -> GitHubAudit:
        """Audit candidate's public repositories, commit activity and dominant languages."""
        username = self._clean_username(username_or_url)
        if not username:
            return GitHubAudit(
                usuario="Desconocido",
                actividad_verificada=False,
                perfil_url="",
            )

        profile_url = f"https://github.com/{username}"
        api_user_url = f"https://api.github.com/users/{username}"
        api_repos_url = f"https://api.github.com/users/{username}/repos?per_page=30&sort=updated"

        try:
            # 1. Fetch user profile
            resp_user = requests.get(api_user_url, headers=self.headers, timeout=self.timeout)
            if resp_user.status_code == 404:
                logger.warning(f"Usuario GitHub no encontrado: {username}")
                return GitHubAudit(
                    usuario=username,
                    actividad_verificada=False,
                    perfil_url=profile_url,
                    existe=False,
                    resumen_actividad="Usuario no encontrado en la plataforma GitHub.",
                )
            elif resp_user.status_code != 200:
                logger.warning(f"GitHub API respondió con código {resp_user.status_code} para {username}")
                return GitHubAudit(
                    usuario=username,
                    actividad_verificada=False,
                    perfil_url=profile_url,
                    existe=False,
                    resumen_actividad=f"Respuesta inesperada de GitHub API (HTTP {resp_user.status_code}).",
                )

            user_data = resp_user.json()

            # 2. Fetch recent repositories
            resp_repos = requests.get(api_repos_url, headers=self.headers, timeout=self.timeout)
            repos_data = resp_repos.json() if resp_repos.status_code == 200 and isinstance(resp_repos.json(), list) else []

            repos_propios = 0
            repos_forks = 0
            stars_totales = 0
            languages_count: Dict[str, int] = {}

            for repo in repos_data:
                is_fork = repo.get("fork", False)
                stars_totales += repo.get("stargazers_count", 0)
                if is_fork:
                    repos_forks += 1
                else:
                    repos_propios += 1

                lang = repo.get("language")
                if lang:
                    languages_count[lang] = languages_count.get(lang, 0) + 1

            # Sort languages by frequency
            sorted_langs = sorted(languages_count.keys(), key=lambda l: languages_count[l], reverse=True)

            # Determine verified activity
            public_repos_total = user_data.get("public_repos", 0)
            actividad_verificada = (repos_propios > 0 or public_repos_total > 0)
            resumen = f"Perfil verificado con {repos_propios} repositorios propios, {repos_forks} forks y {stars_totales} estrellas acumuladas."

            return GitHubAudit(
                usuario=username,
                repos_propios=repos_propios,
                repos_forks=repos_forks,
                stars_totales=stars_totales,
                lenguajes_principales=sorted_langs[:5],
                commits_recientes_count=len(repos_data),
                actividad_verificada=actividad_verificada,
                perfil_url=profile_url,
                existe=True,
                resumen_actividad=resumen,
            )

        except Exception as e:
            logger.warning(f"Excepción al auditar GitHub para {username}: {e}")
            return GitHubAudit(
                usuario=username,
                actividad_verificada=False,
                perfil_url=profile_url,
                existe=False,
                resumen_actividad=f"Error auditando usuario: {e}",
            )

