"""Service for processing wiki content."""
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from gh_wikis.domain.events.wiki_job_events import Event, ExportFileCreated, WikiJobCompleted
from gh_wikis.domain.model.wiki_job import ExportFile, FileFormat, WikiJob
from gh_wikis.domain.repositories.wiki_job_repository import (
    ExportFileRepository,
    WikiJobRepository,
)
from gh_wikis.domain.services.file_storage import FileStorageService
from gh_wikis.domain.services.github_service import GitHubService


class WikiProcessor:
    """Service for processing wiki content."""

    def __init__(
        self,
        github_service: GitHubService,
        file_storage: FileStorageService,
        wiki_job_repository: WikiJobRepository,
        export_file_repository: ExportFileRepository,
        event_publisher: "EventPublisher",
    ):
        """Initialize the processor."""
        self.github_service = github_service
        self.file_storage = file_storage
        self.wiki_job_repository = wiki_job_repository
        self.export_file_repository = export_file_repository
        self.event_publisher = event_publisher

    async def process_wiki(self, job_id: UUID) -> None:
        """Process wiki content for a job."""
        job = await self.wiki_job_repository.get(job_id)
        if job is None:
            raise ValueError(f"Wiki job with ID {job_id} not found")

        try:
            # Extract repository information
            await self._update_progress(job, 5, f"Extracting repository information from URL: {job.repository_url}")
            owner, repo = await self.github_service.extract_repo_info(job.repository_url)

            # Update progress
            await self._update_progress(job, 10, f"Checking repository {owner}/{repo}")

            # Determine if the repository has a wiki
            try:
                has_wiki = await self.github_service.has_wiki(owner, repo)
                content = ""

                if has_wiki:
                    # Get wiki pages
                    await self._update_progress(job, 20, f"Repository has wiki enabled. Fetching wiki pages...")
                    wiki_pages = await self.github_service.get_wiki_pages(owner, repo)

                    if not wiki_pages:
                        await self._update_progress(job, 25, "No wiki pages found despite wiki being enabled. Falling back to README.")
                        readme = await self.github_service.get_readme(owner, repo)
                        if readme:
                            content = readme
                            await self._update_progress(job, 30, "Using README content as fallback")
                        else:
                            content = f"# {repo}\n\nNo wiki pages or README found for this repository."
                            await self._update_progress(job, 30, "No wiki pages or README found")
                    else:
                        # Process each wiki page
                        await self._update_progress(job, 25, f"Found {len(wiki_pages)} wiki pages")
                        total_pages = len(wiki_pages)
                        
                        for i, page in enumerate(wiki_pages):
                            progress = 25 + int((i / total_pages) * 35)
                            await self._update_progress(
                                job, progress, f"Processing page {i+1}/{total_pages}: {page['name']}"
                            )

                            try:
                                page_content = await self.github_service.get_wiki_page_content(
                                    owner, repo, page["path"]
                                )
                                content += f"# {page['name']}\n\n{page_content}\n\n---\n\n"
                            except Exception as page_error:
                                error_msg = f"Error processing page {page['name']}: {str(page_error)}"
                                await self._update_progress(job, progress, error_msg)
                                content += f"# {page['name']}\n\n*Error fetching content: {str(page_error)}*\n\n---\n\n"
                else:
                    # If no wiki, get the README
                    await self._update_progress(job, 20, "No wiki found for repository, fetching README")
                    readme = await self.github_service.get_readme(owner, repo)
                    if readme:
                        content = readme
                        await self._update_progress(job, 30, "Retrieved README content successfully")
                    else:
                        content = f"# {repo}\n\nNo wiki or README found for this repository."
                        await self._update_progress(job, 30, "No README found")
            
            except Exception as repo_error:
                await self._update_progress(job, 15, f"Error accessing repository: {str(repo_error)}")
                # Try to get README as fallback
                try:
                    readme = await self.github_service.get_readme(owner, repo)
                    if readme:
                        content = readme
                        await self._update_progress(job, 30, "Using README content as fallback after error")
                    else:
                        content = f"# {repo}\n\nError accessing repository: {str(repo_error)}"
                except Exception:
                    content = f"# {repo}\n\nError accessing repository: {str(repo_error)}"

            # Generate export files
            await self._update_progress(job, 60, "Generating Markdown export")
            await self._generate_markdown_export(job, content)

            await self._update_progress(job, 70, "Generating PDF export")
            await self._generate_pdf_export(job, content)

            await self._update_progress(job, 80, "Generating EPUB export")
            await self._generate_epub_export(job, content)

            # Mark job as completed
            await self._update_progress(job, 100, "Export completed")
            job.complete()
            await self.wiki_job_repository.update(job)

            # Publish completion event
            completion_event = WikiJobCompleted(
                id=uuid4(),
                timestamp=datetime.utcnow(),
                aggregate_id=job.id,
            )
            await self.event_publisher.publish(completion_event)

        except Exception as e:
            # Mark job as failed
            job.fail(str(e))
            await self.wiki_job_repository.update(job)
            # Exception will be caught by the task runner and appropriate event will be published

    async def _update_progress(self, job: WikiJob, percentage: int, message: str) -> None:
        """Update job progress."""
        job.update_progress(percentage, message)
        await self.wiki_job_repository.update(job)
        
        # Try to explicitly commit if we have access to the session
        # This is a workaround for problems with database session management
        try:
            repo = self.wiki_job_repository
            if hasattr(repo, "session") and hasattr(repo.session, "commit"):
                await repo.session.commit()
        except Exception:
            pass

    async def _generate_markdown_export(self, job: WikiJob, content: str) -> None:
        """Generate markdown export."""
        repo_name = job.repository_url.split("/")[-1]
        filename = f"{repo_name}_wiki.md"

        # Store markdown content
        storage_path, size_bytes = await self.file_storage.store_file(
            content.encode("utf-8"), filename, job.id
        )

        # Create and save export file record
        export_file = ExportFile.create(
            job_id=job.id,
            format=FileFormat.MARKDOWN,
            filename=filename,
            storage_path=storage_path,
            size_bytes=size_bytes,
        )
        await self.export_file_repository.add(export_file)

        # Publish event
        event = ExportFileCreated(
            id=uuid4(),
            timestamp=export_file.created_at,
            aggregate_id=job.id,
            file_id=export_file.id,
            format=export_file.format,
            filename=export_file.filename,
            storage_path=export_file.storage_path,
            size_bytes=export_file.size_bytes,
        )
        await self.event_publisher.publish(event)

    async def _generate_pdf_export(self, job: WikiJob, content: str) -> None:
        """Generate PDF export using WeasyPrint or fallback to simple HTML."""
        from markdown import markdown
        import tempfile
        import io
        
        repo_name = job.repository_url.split("/")[-1]
        filename = f"{repo_name}_wiki.pdf"
        
        try:
            # Convert markdown to HTML
            html_content = markdown(content)
            html_doc = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{repo_name} Wiki</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif;
                        margin: 50px;
                        line-height: 1.5;
                    }}
                    h1, h2, h3, h4, h5, h6 {{ color: #333; margin-top: 20px; }}
                    h1 {{ border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
                    pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    blockquote {{ border-left: 3px solid #ddd; margin-left: 0; padding-left: 15px; color: #777; }}
                    img {{ max-width: 100%; }}
                    hr {{ border: 0; border-top: 1px solid #eee; margin: 30px 0; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            try:
                # Try to use WeasyPrint first
                from weasyprint import HTML
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    # Generate PDF with WeasyPrint
                    HTML(string=html_doc).write_pdf(temp_file.name)
                    
                    # Read PDF content
                    with open(temp_file.name, 'rb') as f:
                        pdf_content = f.read()
                    
                    # Delete temporary file
                    import os
                    os.unlink(temp_file.name)
            except Exception as weasy_error:
                print(f"WeasyPrint error: {str(weasy_error)}, falling back to simple HTML")
                # Fallback to simple HTML if WeasyPrint fails
                pdf_content = html_doc.encode('utf-8')
                
            # Store content
            storage_path, size_bytes = await self.file_storage.store_file(
                pdf_content, filename, job.id
            )
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            # If generation fails, create a simple text file
            error_msg = f"PDF generation failed: {str(e)}"
            pdf_content = error_msg.encode("utf-8")
            storage_path, size_bytes = await self.file_storage.store_file(
                pdf_content, filename, job.id
            )

        # Create and save export file record
        export_file = ExportFile.create(
            job_id=job.id,
            format=FileFormat.PDF,
            filename=filename,
            storage_path=storage_path,
            size_bytes=size_bytes,
        )
        await self.export_file_repository.add(export_file)

        # Publish event
        event = ExportFileCreated(
            id=uuid4(),
            timestamp=export_file.created_at,
            aggregate_id=job.id,
            file_id=export_file.id,
            format=export_file.format,
            filename=export_file.filename,
            storage_path=export_file.storage_path,
            size_bytes=export_file.size_bytes,
        )
        await self.event_publisher.publish(event)

    async def _generate_epub_export(self, job: WikiJob, content: str) -> None:
        """Generate EPUB export using ebooklib."""
        import tempfile
        from ebooklib import epub
        import re
        from markdown import markdown
        from bs4 import BeautifulSoup
        
        repo_name = job.repository_url.split("/")[-1]
        filename = f"{repo_name}_wiki.epub"
        
        try:
            # Create a new EPUB book
            book = epub.EpubBook()
            
            # Set metadata
            book.set_identifier(f"gh-wiki-{job.id}")
            book.set_title(f"{repo_name} Wiki")
            book.set_language('en')
            
            # Split content into chapters based on markdown headers
            chapter_pattern = r'# (.*?)(?=\n# |$)'
            chapters = re.split(chapter_pattern, content)
            
            # If no chapters found or odd number of items, handle as single chapter
            if len(chapters) <= 1 or len(chapters) % 2 != 1:
                # Create a single chapter
                chapter = epub.EpubHtml(title=repo_name, file_name='content.xhtml')
                chapter.content = f'<html><body>{markdown(content)}</body></html>'
                book.add_item(chapter)
                book.spine = ['nav', chapter]
                book.toc = [epub.Link('content.xhtml', repo_name, 'intro')]
            else:
                # Process chapters (first item is content before first header)
                toc = []
                spine = ['nav']
                
                # Handle initial content if any
                if chapters[0].strip():
                    intro = epub.EpubHtml(title="Introduction", file_name='intro.xhtml')
                    intro.content = f'<html><body>{markdown(chapters[0])}</body></html>'
                    book.add_item(intro)
                    spine.append(intro)
                    toc.append(epub.Link('intro.xhtml', 'Introduction', 'intro'))
                
                # Process each chapter
                for i in range(1, len(chapters), 2):
                    chapter_title = chapters[i]
                    chapter_content = chapters[i+1] if i+1 < len(chapters) else ""
                    
                    # Clean the title for filename
                    filename_safe_title = re.sub(r'[^\w\-]', '_', chapter_title.lower())
                    file_name = f'chapter_{filename_safe_title}.xhtml'
                    
                    # Create chapter
                    chapter = epub.EpubHtml(title=chapter_title, file_name=file_name)
                    chapter.content = f'<html><body><h1>{chapter_title}</h1>{markdown(chapter_content)}</body></html>'
                    
                    # Add chapter
                    book.add_item(chapter)
                    spine.append(chapter)
                    toc.append(epub.Link(file_name, chapter_title, filename_safe_title))
                
                # Set spine and table of contents
                book.spine = spine
                book.toc = toc
            
            # Add navigation files
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
                # Write EPUB to temporary file
                epub.write_epub(temp_file.name, book, {})
                
                # Read EPUB content
                with open(temp_file.name, 'rb') as f:
                    epub_content = f.read()
                
                # Delete temporary file
                import os
                os.unlink(temp_file.name)
            
            # Store EPUB content
            storage_path, size_bytes = await self.file_storage.store_file(
                epub_content, filename, job.id
            )
            
        except Exception as e:
            print(f"Error generating EPUB: {str(e)}")
            # If EPUB generation fails, create a simple text file with error message
            error_msg = f"EPUB generation failed: {str(e)}"
            epub_content = error_msg.encode("utf-8")
            storage_path, size_bytes = await self.file_storage.store_file(
                epub_content, filename, job.id
            )

        # Create and save export file record
        export_file = ExportFile.create(
            job_id=job.id,
            format=FileFormat.EPUB,
            filename=filename,
            storage_path=storage_path,
            size_bytes=size_bytes,
        )
        await self.export_file_repository.add(export_file)

        # Publish event
        event = ExportFileCreated(
            id=uuid4(),
            timestamp=export_file.created_at,
            aggregate_id=job.id,
            file_id=export_file.id,
            format=export_file.format,
            filename=export_file.filename,
            storage_path=export_file.storage_path,
            size_bytes=export_file.size_bytes,
        )
        await self.event_publisher.publish(event)