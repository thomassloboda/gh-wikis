"""Web routes for the application."""
from uuid import UUID
from typing import Annotated, Dict, Optional
from collections import defaultdict

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from gh_wikis.application.commands.wiki_job_commands import (
    CreateWikiJob, 
    CreateWikiJobHandler,
    DeleteWikiJob,
    DeleteWikiJobHandler,
    DeleteExportFile,
    DeleteExportFileHandler
)
from gh_wikis.application.queries.wiki_job_queries import (
    GetExportFileHandler,
    GetExportFileQuery,
    GetExportFilesHandler,
    GetExportFilesQuery,
    GetWikiJobHandler,
    GetWikiJobQuery,
    ListWikiJobsHandler,
    ListWikiJobsQuery,
)
from gh_wikis.interfaces.api.dependencies import (
    get_create_wiki_job_handler,
    get_delete_export_file_handler,
    get_delete_wiki_job_handler,
    get_export_file_handler,
    get_export_files_handler,
    get_list_wiki_jobs_handler,
    get_wiki_job_handler,
)

# Templates setup
templates = Jinja2Templates(directory="gh_wikis/interfaces/web/templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("home.html", {"request": request})


@router.post("/")
async def create_job(
    request: Request,
    repository_url: Annotated[str, Form()],
    handler: CreateWikiJobHandler = Depends(get_create_wiki_job_handler),
):
    """Create a new wiki job from form submission."""
    command = CreateWikiJob(repository_url=repository_url)
    job_id = await handler.handle(command)

    # Start processing the job asynchronously
    from gh_wikis.infrastructure.celery_app import celery_app

    celery_app.send_task("process_wiki", args=[str(job_id)])

    # Redirect to job detail page
    return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_list(
    request: Request,
    handler: ListWikiJobsHandler = Depends(get_list_wiki_jobs_handler),
):
    """Render the jobs list page."""
    query = ListWikiJobsQuery(limit=100, offset=0)
    jobs = await handler.handle(query)
    return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs})


@router.get("/wikis", response_class=HTMLResponse)
async def list_wikis(
    request: Request,
    jobs_handler: ListWikiJobsHandler = Depends(get_list_wiki_jobs_handler),
    files_handler: GetExportFilesHandler = Depends(get_export_files_handler),
):
    """Render wikis listing page with download links."""
    query = ListWikiJobsQuery(limit=100, offset=0)
    jobs = await jobs_handler.handle(query)
    
    # Get all files for completed jobs
    files_by_job = {}
    for job in jobs:
        if job.status.name == "COMPLETED":
            files_query = GetExportFilesQuery(job_id=job.id)
            job_files = await files_handler.handle(files_query)
            files_by_job[job.id] = job_files
            
            # Si aucun fichier n'a été trouvé mais que le job est complété, ça peut être un problème
            if not job_files:
                print(f"Warning: Completed job {job.id} has no files")
    
    # Pass jobs and files to template
    return templates.TemplateResponse(
        "wikis.html", 
        {
            "request": request, 
            "jobs": jobs, 
            "files": files_by_job
        }
    )


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(
    request: Request,
    job_id: UUID,
    job_handler: GetWikiJobHandler = Depends(get_wiki_job_handler),
    files_handler: GetExportFilesHandler = Depends(get_export_files_handler),
):
    """Render the job detail page."""
    # Get job
    job_query = GetWikiJobQuery(job_id=job_id)
    job = await job_handler.handle(job_query)

    if not job:
        # Job not found
        return templates.TemplateResponse(
            "job_detail.html",
            {"request": request, "job": None, "files": [], "error": "Job not found"},
            status_code=404,
        )

    # Get export files
    if job.status.name == "COMPLETED":
        files_query = GetExportFilesQuery(job_id=job_id)
        files = await files_handler.handle(files_query)
    else:
        files = []

    # Pass job and files to template
    return templates.TemplateResponse(
        "job_detail.html", {"request": request, "job": job, "files": files}
    )


@router.post("/jobs/{job_id}/delete")
async def delete_job(
    request: Request,
    job_id: UUID,
    handler: DeleteWikiJobHandler = Depends(get_delete_wiki_job_handler),
):
    """Delete a wiki job."""
    try:
        command = DeleteWikiJob(job_id=job_id)
        await handler.handle(command)
        return RedirectResponse(url="/jobs", status_code=303)
    except Exception as e:
        # Handle error and redirect to jobs page with error message
        return RedirectResponse(
            url=f"/jobs?error={str(e)}",
            status_code=303
        )


@router.post("/files/{file_id}/delete")
async def delete_file(
    request: Request,
    file_id: UUID,
    handler: DeleteExportFileHandler = Depends(get_delete_export_file_handler),
    file_handler: GetExportFileHandler = Depends(get_export_file_handler),
):
    """Delete an export file."""
    # Get the file to determine job_id for redirect
    query = GetExportFileQuery(file_id=file_id)
    file = await file_handler.handle(query)
    job_id = file.job_id if file else None
    
    try:
        command = DeleteExportFile(file_id=file_id)
        await handler.handle(command)
        
        if job_id:
            return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)
        else:
            return RedirectResponse(url="/jobs", status_code=303)
    except Exception as e:
        # Redirect to job detail or jobs page with error
        if job_id:
            return RedirectResponse(url=f"/jobs/{job_id}?error={str(e)}", status_code=303)
        else:
            return RedirectResponse(url=f"/jobs?error={str(e)}", status_code=303)