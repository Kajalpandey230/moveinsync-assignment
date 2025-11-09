"""MongoDB database connection module."""

import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Database:
    """MongoDB database connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    def get_connection_string(cls) -> str:
        """
        Get MongoDB connection string from environment variables.

        Returns:
            str: MongoDB connection string

        Raises:
            ValueError: If MONGODB_URL is not set in environment variables
        """
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise ValueError(
                "MONGODB_URL environment variable is not set. "
                "Please set it in your .env file or environment."
            )
        return mongodb_url

    @classmethod
    def get_database_name(cls) -> str:
        """
        Get database name from environment variables.

        Returns:
            str: Database name, defaults to 'moveinsync_db' if not set
        """
        return os.getenv("MONGODB_DATABASE", "moveinsync_db")

    @classmethod
    async def connect(cls) -> None:
        """
        Connect to MongoDB database.

        Raises:
            ConnectionFailure: If connection to MongoDB fails
        """
        try:
            connection_string = cls.get_connection_string()
            database_name = cls.get_database_name()

            cls.client = AsyncIOMotorClient(connection_string)
            cls.database = cls.client[database_name]

            # Verify connection by pinging the database
            await cls.client.admin.command("ping")
            print(f"Successfully connected to MongoDB database: {database_name}")

        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error connecting to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.database = None
            print("Disconnected from MongoDB")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get the database instance.

        Returns:
            AsyncIOMotorDatabase: The database instance

        Raises:
            RuntimeError: If database is not connected
        """
        if cls.database is None:
            raise RuntimeError(
                "Database is not connected. Call Database.connect() first."
            )
        return cls.database

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """
        Get the MongoDB client instance.

        Returns:
            AsyncIOMotorClient: The MongoDB client instance

        Raises:
            RuntimeError: If client is not connected
        """
        if cls.client is None:
            raise RuntimeError(
                "Database client is not connected. Call Database.connect() first."
            )
        return cls.client

