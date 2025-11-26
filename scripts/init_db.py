import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.persistence.database import init_db, engine
from src.core.config import settings


async def initialize_database():
    print(f"Initializing database at: {settings.database_url}")
    
    try:
        await init_db()
        print("✓ Database tables created successfully")
        
        async with engine.connect() as conn:
            print("✓ Database connection verified")
        
        print("\nDatabase initialization complete!")
        print(f"You can now run the application with: python -m src.main")
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(initialize_database())
