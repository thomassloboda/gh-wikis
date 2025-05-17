"""API routes for the application."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, StreamingResponse

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
from gh_wikis.domain.model.wiki_job import WikiJobStatus
from gh_wikis.domain.services.file_storage import FileStorageService
from gh_wikis.infrastructure.tasks.wiki_tasks import process_wiki
from gh_wikis.interfaces.api.dependencies import (
    get_create_wiki_job_handler,
    get_delete_export_file_handler,
    get_delete_wiki_job_handler,
    get_export_file_handler,
    get_export_files_handler,
    get_file_storage,
    get_list_wiki_jobs_handler,
    get_wiki_job_handler,
)
from gh_wikis.interfaces.api.schemas import (
    CreateWikiJobRequest,
    ExportFileResponse,
    WikiJobListResponse,
    WikiJobResponse,
)

router = APIRouter(prefix="/api")


@router.post("/jobs", response_model=WikiJobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: CreateWikiJobRequest,
    handler: CreateWikiJobHandler = Depends(get_create_wiki_job_handler),
    job_query_handler: GetWikiJobHandler = Depends(get_wiki_job_handler),
) -> WikiJobResponse:
    """Create a new wiki job."""
    try:
        # Validate GitHub URL format
        if not request.repository_url or "github.com/" not in str(request.repository_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub repository URL. Must be a valid GitHub repository URL."
            )
            
        command = CreateWikiJob(repository_url=str(request.repository_url))
        job_id = await handler.handle(command)

        # Start processing the job asynchronously
        from gh_wikis.infrastructure.celery_app import celery_app
        task = celery_app.send_task("process_wiki", args=[str(job_id)])
        
        # Return the created job
        job = await job_query_handler.handle(GetWikiJobQuery(job_id=job_id))
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        return WikiJobResponse(
            id=job.id,
            repository_url=job.repository_url,
            status=job.status.name.lower(),
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            progress_percentage=job.progress_percentage,
            progress_message=job.progress_message,
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/jobs", response_model=WikiJobListResponse)
async def list_jobs(
    limit: int = 100,
    offset: int = 0,
    handler: ListWikiJobsHandler = Depends(get_list_wiki_jobs_handler),
) -> WikiJobListResponse:
    """List all wiki jobs."""
    query = ListWikiJobsQuery(limit=limit, offset=offset)
    jobs = await handler.handle(query)

    # Convert domain entities to response schema
    response_jobs = [
        WikiJobResponse(
            id=job.id,
            repository_url=job.repository_url,
            status=job.status.name.lower(),
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            progress_percentage=job.progress_percentage,
            progress_message=job.progress_message,
        )
        for job in jobs
    ]

    return WikiJobListResponse(jobs=response_jobs, total=len(response_jobs))


@router.get("/jobs/{job_id}", response_model=WikiJobResponse)
async def get_job(
    job_id: UUID, handler: GetWikiJobHandler = Depends(get_wiki_job_handler)
) -> WikiJobResponse:
    """Get a wiki job by ID."""
    query = GetWikiJobQuery(job_id=job_id)
    job = await handler.handle(query)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return WikiJobResponse(
        id=job.id,
        repository_url=job.repository_url,
        status=job.status.name.lower(),
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        progress_percentage=job.progress_percentage,
        progress_message=job.progress_message,
    )


@router.get("/jobs/{job_id}/files", response_model=List[ExportFileResponse])
async def get_job_files(
    job_id: UUID,
    handler: GetExportFilesHandler = Depends(get_export_files_handler),
    job_handler: GetWikiJobHandler = Depends(get_wiki_job_handler),
    file_storage: FileStorageService = Depends(get_file_storage),
) -> List[ExportFileResponse]:
    """Get all export files for a job."""
    # Check if the job exists
    job_query = GetWikiJobQuery(job_id=job_id)
    job = await job_handler.handle(job_query)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get export files
    query = GetExportFilesQuery(job_id=job_id)
    files = await handler.handle(query)

    # Generate download URLs and convert to response schema
    response_files = []
    for file in files:
        download_url = await file_storage.get_download_url(file.storage_path)
        response_files.append(
            ExportFileResponse(
                id=file.id,
                job_id=file.job_id,
                format=file.format.name.lower(),
                filename=file.filename,
                size_bytes=file.size_bytes,
                created_at=file.created_at,
                download_url=download_url,
            )
        )

    return response_files


@router.get("/files/{file_id}")
async def get_file(
    file_id: UUID,
    handler: GetExportFileHandler = Depends(get_export_file_handler),
    file_storage: FileStorageService = Depends(get_file_storage),
):
    """Get a file by ID and redirect to download URL."""
    query = GetExportFileQuery(file_id=file_id)
    file = await handler.handle(query)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Get download URL
    download_url = await file_storage.get_download_url(file.storage_path)

    # Redirect to download URL
    return RedirectResponse(url=download_url)


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: UUID,
    handler: GetExportFileHandler = Depends(get_export_file_handler),
    file_storage: FileStorageService = Depends(get_file_storage),
):
    """Download a file directly."""
    query = GetExportFileQuery(file_id=file_id)
    file = await handler.handle(query)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Get file content
    content = await file_storage.get_file(file.storage_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File content not found")

    # Set content type based on file format
    content_type = "application/octet-stream"
    if file.format.name.lower() == "markdown":
        content_type = "text/markdown"
    elif file.format.name.lower() == "pdf":
        content_type = "application/pdf"
    elif file.format.name.lower() == "epub":
        content_type = "application/epub+zip"

    # Return file for download
    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(
    job_id: UUID,
    handler: DeleteWikiJobHandler = Depends(get_delete_wiki_job_handler),
):
    """Delete a wiki job and all associated files."""
    try:
        command = DeleteWikiJob(job_id=job_id)
        await handler.handle(command)
        return {"status": "success", "message": "Job deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


@router.delete("/files/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file(
    file_id: UUID,
    handler: DeleteExportFileHandler = Depends(get_delete_export_file_handler),
):
    """Delete an export file."""
    try:
        command = DeleteExportFile(file_id=file_id)
        await handler.handle(command)
        return {"status": "success", "message": "File deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")