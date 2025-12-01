"""Base repository interface following the Repository Pattern."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type


class IRepository(ABC, Generic[T, ID]):
    """
    Abstract base repository interface.

    Provides a standard contract for data access operations.
    All repository implementations must follow this interface,
    enabling easy swapping of storage backends (file, DynamoDB, etc.).

    Type Parameters:
        T: The entity type this repository manages
        ID: The identifier type for entities
    """

    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> T | None:
        """
        Retrieve an entity by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(self) -> list[T]:
        """
        Retrieve all entities.

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        Add a new entity to the repository.

        Args:
            entity: The entity to add

        Returns:
            The added entity (may include generated fields)
        """
        pass

    @abstractmethod
    async def add_many(self, entities: list[T]) -> list[T]:
        """
        Add multiple entities to the repository.

        Args:
            entities: List of entities to add

        Returns:
            List of added entities
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: The entity with updated values

        Returns:
            The updated entity
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """
        Delete an entity by its identifier.

        Args:
            entity_id: The unique identifier of the entity to delete

        Returns:
            True if deleted, False if entity not found
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: ID) -> bool:
        """
        Check if an entity exists.

        Args:
            entity_id: The unique identifier to check

        Returns:
            True if entity exists, False otherwise
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Get the total count of entities.

        Returns:
            Total number of entities
        """
        pass
