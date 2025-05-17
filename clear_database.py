#!/usr/bin/env python
"""Script to clear all data from the database."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from gh_wikis.infrastructure.config import settings

async def clear_database():
    """Clear all data from the database while respecting foreign key constraints."""
    print("Connecting to database...")
    engine = create_async_engine(settings.database_url)
    
    async with AsyncSession(engine) as session:
        print("Clearing export_files table...")
        # Delete from export_files first (child table)
        await session.execute(text("DELETE FROM export_files"))
        
        print("Clearing wiki_jobs table...")
        # Then delete from wiki_jobs (parent table)
        await session.execute(text("DELETE FROM wiki_jobs"))
        
        # Commit the changes
        await session.commit()
    
    print("Database cleared successfully!")

if __name__ == "__main__":
    asyncio.run(clear_database())