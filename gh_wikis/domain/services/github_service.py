"""GitHub service interface."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class GitHubService(ABC):
    """Interface for GitHub API interactions."""

    @abstractmethod
    async def extract_repo_info(self, repo_url: str) -> Tuple[str, str]:
        """
        Extract owner and repository name from a GitHub URL.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Tuple containing owner and repository name

        Raises:
            ValueError: If the URL is not a valid GitHub repository URL
        """
        pass

    @abstractmethod
    async def has_wiki(self, owner: str, repo: str) -> bool:
        """
        Check if a repository has a wiki.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            True if the repository has a wiki, False otherwise
        """
        pass

    @abstractmethod
    async def get_wiki_pages(self, owner: str, repo: str) -> List[Dict[str, str]]:
        """
        Get the list of wiki pages for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of dictionaries containing page information (name, path)
        """
        pass

    @abstractmethod
    async def get_wiki_page_content(self, owner: str, repo: str, page_path: str) -> str:
        """
        Get the content of a wiki page.

        Args:
            owner: Repository owner
            repo: Repository name
            page_path: Path to the wiki page

        Returns:
            Content of the wiki page as markdown
        """
        pass

    @abstractmethod
    async def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        Get the README file from a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Content of the README as markdown, or None if not found
        """
        pass