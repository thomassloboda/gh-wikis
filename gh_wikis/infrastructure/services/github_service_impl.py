"""GitHub service implementation."""
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from github import Github
from github.Repository import Repository

from gh_wikis.domain.services.github_service import GitHubService
from gh_wikis.infrastructure.config import settings


class GitHubServiceImpl(GitHubService):
    """Implementation of the GitHub service interface."""

    def __init__(self, token: Optional[str] = None):
        """Initialize the service."""
        self.token = token or settings.github_token
        self.github_client = Github(self.token) if self.token else Github()

    async def extract_repo_info(self, repo_url: str) -> Tuple[str, str]:
        """Extract owner and repository name from GitHub URL."""
        parsed_url = urlparse(repo_url)

        # Validate that this is a GitHub URL
        if not (parsed_url.netloc == "github.com" or parsed_url.netloc.endswith(".github.com")):
            raise ValueError(f"Not a valid GitHub URL: {repo_url}")

        # Get the path part of the URL and remove leading/trailing slashes
        path = parsed_url.path.strip("/")
        parts = path.split("/")

        # A valid GitHub repository URL has at least owner/repo format
        if len(parts) < 2:
            raise ValueError(f"Not a valid GitHub repository URL: {repo_url}")

        owner, repo = parts[0], parts[1]
        return owner, repo

    async def has_wiki(self, owner: str, repo: str) -> bool:
        """Check if a repository has a wiki."""
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            has_wiki_flag = repository.has_wiki
            
            # Even if the has_wiki flag is False, we can try to directly check if wiki pages exist
            # This handles cases where the API property is inaccurate
            if not has_wiki_flag:
                try:
                    # Try to fetch wiki pages directly - if this succeeds, then the wiki exists
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/wiki/pages"
                    headers = {}
                    if self.token:
                        headers["Authorization"] = f"token {self.token}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(api_url, headers=headers) as response:
                            if response.status == 200:
                                # Wiki pages exist, despite the has_wiki flag
                                print(f"Repository {owner}/{repo} has wiki pages, despite has_wiki=False")
                                return True
                except Exception as wiki_check_error:
                    print(f"Secondary wiki check error: {str(wiki_check_error)}")
                    # If the secondary check fails, stick with the original flag value
                    pass
            
            return has_wiki_flag
            
        except Exception as e:
            print(f"Error checking if repository has wiki: {str(e)}")
            # Instead of raising an exception, return False and let the application fall back to README
            return False

    async def get_wiki_pages(self, owner: str, repo: str) -> List[Dict[str, str]]:
        """Get the list of wiki pages for a repository."""
        # This is not directly supported by PyGithub, so we need to use GitHub's API directly
        api_url = f"https://api.github.com/repos/{owner}/{repo}/wiki/pages"
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        pages = await response.json()
                        return [{"name": page["title"], "path": page["path"]} for page in pages]
                    else:
                        error_text = await response.text()
                        print(f"Error fetching wiki pages via API: {response.status} {error_text}")
                        
                        # If we can't get the wiki pages via API, try a fallback approach
                        # First try to scrape the wiki page to find all wiki pages
                        try:
                            print(f"Trying to scrape wiki pages for {owner}/{repo}")
                            wiki_url = f"https://github.com/{owner}/{repo}/wiki"
                            async with session.get(wiki_url) as wiki_response:
                                if wiki_response.status == 200:
                                    html_content = await wiki_response.text()
                                    # Look for wiki pages in the sidebar
                                    # GitHub wiki sidebar has links with specific patterns
                                    import re
                                    # Pattern to match wiki page links in the sidebar
                                    pattern = r'href="\/[^\/]+\/[^\/]+\/wiki\/([^"]+)"[^>]*>([^<]+)<'
                                    matches = re.findall(pattern, html_content)
                                    
                                    if matches:
                                        # Extract wiki page names and paths
                                        wiki_pages = []
                                        for path, name in matches:
                                            # Skip non-content pages like "_Footer" and "_Sidebar"
                                            if not path.startswith("_"):
                                                wiki_pages.append({
                                                    "name": name.strip(),
                                                    "path": path.strip()
                                                })
                                        
                                        if wiki_pages:
                                            print(f"Found {len(wiki_pages)} wiki pages by scraping HTML")
                                            return wiki_pages
                        except Exception as scrape_error:
                            print(f"Error scraping wiki pages: {str(scrape_error)}")
                        
                        # If scraping fails, try to check for specific common pages
                        wiki_pages = []
                        try:
                            # Check for Home page first (required for all wikis)
                            home_url = f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/Home.md"
                            async with session.get(home_url) as home_response:
                                if home_response.status == 200:
                                    print(f"Found Home page for {owner}/{repo} wiki")
                                    wiki_pages.append({"name": "Home", "path": "Home"})
                            
                            # Check for other common wiki pages
                            common_pages = [
                                "API-Export-JSON-Format", "Configuration-&-Deep-Linking", 
                                "Projects", "Supported-Data", "Getting-Started", "Installation",
                                "Usage", "FAQ", "Troubleshooting", "Documentation"
                            ]
                            
                            for page_path in common_pages:
                                page_url = f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page_path}.md"
                                async with session.get(page_url) as page_response:
                                    if page_response.status == 200:
                                        # Replace hyphens with spaces for display name
                                        display_name = page_path.replace('-', ' ')
                                        wiki_pages.append({"name": display_name, "path": page_path})
                                        print(f"Found wiki page: {display_name}")
                            
                            if wiki_pages:
                                print(f"Found {len(wiki_pages)} wiki pages via individual checks")
                                return wiki_pages
                        except Exception as page_check_error:
                            print(f"Error checking common wiki pages: {str(page_check_error)}")
                        
                        # If no wiki pages found, return an empty list
                        # The application will fall back to using the README
                        return []
        except Exception as e:
            print(f"Exception fetching wiki pages: {str(e)}")
            return []

    async def get_wiki_page_content(self, owner: str, repo: str, page_path: str) -> str:
        """Get the content of a wiki page."""
        # GitHub's API doesn't provide direct access to wiki page content through their REST API
        # We need to access the raw content directly from the wiki.git repository
        
        # Handle special characters in page_path
        # Some page paths might have spaces or other characters that need to be handled
        import urllib.parse
        
        # Don't double-encode if already URL-encoded
        if '%' not in page_path:
            # Replace spaces with hyphens (GitHub wiki convention)
            page_path_normalized = page_path.replace(' ', '-')
            # URL encode other special characters
            page_path_encoded = urllib.parse.quote(page_path_normalized, safe='-_')
        else:
            page_path_encoded = page_path
        
        # Try with and without the .md extension
        urls_to_try = [
            f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page_path_encoded}.md",
            f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page_path_encoded}",
            f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page_path}.md",
            f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page_path}"
        ]
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                for url in urls_to_try:
                    try:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                print(f"Successfully fetched content from {url}")
                                return await response.text()
                    except Exception as url_error:
                        print(f"Error fetching from {url}: {str(url_error)}")
                        continue
                
                # If all attempts fail, try one last approach with the GitHub web URL
                try:
                    web_url = f"https://github.com/{owner}/{repo}/wiki/{page_path_encoded}"
                    async with session.get(web_url, headers=headers) as web_response:
                        if web_response.status == 200:
                            html_content = await web_response.text()
                            # Extract markdown content from the GitHub wiki page
                            import re
                            # Look for the markdown-body content
                            markdown_match = re.search(r'<div[^>]*markdown-body[^>]*>(.*?)</div>', 
                                                     html_content, re.DOTALL)
                            if markdown_match:
                                content = markdown_match.group(1)
                                # Clean up HTML tags
                                content = re.sub(r'<[^>]*>', '', content)
                                return content
                except Exception as web_error:
                    print(f"Error fetching from web URL: {str(web_error)}")
                
                # If we get here, all attempts failed
                print(f"All attempts to fetch content for {page_path} failed")
                return f"*Could not fetch content for {page_path}*"
        except Exception as e:
            print(f"Exception fetching wiki page: {str(e)}")
            return f"*Error fetching content for {page_path}: {str(e)}*"

    async def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """Get the README file from a repository."""
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            try:
                readme = repository.get_readme()
                return readme.decoded_content.decode("utf-8")
            except Exception:
                return None
        except Exception as e:
            raise ValueError(f"Error fetching README: {str(e)}")