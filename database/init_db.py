
from database.db import engine
from src.job_matching.job_model import Base, Job
from src.tracking.application_model import Application
from src.tracking.application_history_model import ApplicationHistory


def initialize_database():
    """Create all registered AI-JobPilot database tables."""

    print("Initializing AI-JobPilot database...")

    # Ensure all models are registered with Base.metadata.
    _ = (Job, Application, ApplicationHistory)

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")

    print("\nAvailable tables:")
    for table_name in Base.metadata.tables:
        print(f"- {table_name}")


if __name__ == "__main__":
    initialize_database()
