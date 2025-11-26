#!/usr/bin/env python3
"""
Database initialization script.

This script initializes the database schema and optionally creates sample data.
It can be run standalone or imported and used programmatically.

Usage:
    python -m scripts.init_db [--sample-data] [--drop-existing]
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db, get_db_context, engine
from src.models import Website, MonitorConfig, SQLModel
from src.config import settings


def drop_all_tables():
    """Drop all tables from the database."""
    print("Dropping all existing tables...")
    SQLModel.metadata.drop_all(bind=engine)
    print("All tables dropped.")


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully.")


def create_sample_data():
    """Create sample data for testing."""
    print("Creating sample data...")
    
    with get_db_context() as db:
        website1 = Website(
            name="Main WHMCS Site",
            website_url="https://example.com",
            api_identifier="sample_identifier_1",
            api_secret="sample_secret_1",
            region="US-East",
            is_active=True
        )
        db.add(website1)
        db.commit()
        db.refresh(website1)
        print(f"  Created website: {website1.name} (ID: {website1.id})")
        
        website2 = Website(
            name="Secondary WHMCS Site",
            website_url="https://secondary.example.com",
            api_identifier="sample_identifier_2",
            api_secret="sample_secret_2",
            region="EU-West",
            is_active=True
        )
        db.add(website2)
        db.commit()
        db.refresh(website2)
        print(f"  Created website: {website2.name} (ID: {website2.id})")
        
        monitor1 = MonitorConfig(
            website_id=website1.id,
            product_id=101,
            product_name="VPS Hosting",
            threshold_low=5,
            threshold_high=50,
            is_active=True,
            status="active",
            purchase_link="https://example.com/cart.php?a=add&pid=101"
        )
        db.add(monitor1)
        
        monitor2 = MonitorConfig(
            website_id=website1.id,
            product_id=102,
            product_name="Dedicated Server",
            threshold_low=2,
            threshold_high=20,
            is_active=True,
            status="active"
        )
        db.add(monitor2)
        
        monitor3 = MonitorConfig(
            website_id=website2.id,
            product_id=201,
            product_name="Cloud Storage",
            threshold_low=10,
            threshold_high=100,
            is_active=True,
            status="active"
        )
        db.add(monitor3)
        
        db.commit()
        print(f"  Created 3 monitor configurations")
    
    print("Sample data created successfully.")


def main():
    """Main entry point for the initialization script."""
    parser = argparse.ArgumentParser(
        description="Initialize the WHMCS Stock Monitor database"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop all existing tables before creating new ones"
    )
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Create sample data after initializing the database"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WHMCS Stock Monitor - Database Initialization")
    print("=" * 60)
    print(f"Database URL: {settings.database_url}")
    print()
    
    try:
        if args.drop_existing:
            drop_all_tables()
            print()
        
        create_tables()
        print()
        
        if args.sample_data:
            create_sample_data()
            print()
        
        print("=" * 60)
        print("Database initialization completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Database initialization failed!")
        print(f"Error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
