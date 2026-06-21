from typing import Protocol, Dict, Any
from contextlib import AbstractAsyncContextManager

from .api import Api

class Connection(Protocol):
    """Интерфейс (Protocol) для управления асинхронным подключением к биржам."""

    @property
    def connected(self) -> bool:
        """Проверяет, активно ли подключение и работает ли сервис."""
        ...

    @property
    def working(self) -> bool:
        """Проверяет, запущен ли внутренний контур управления соединением."""
        ...

    async def connection(self):
        """Устанавливает подключение к бирже."""
        ...

    async def disconnect(self) -> None:
        """Закрывает подключение и очищает ресурсы."""
        ...
    
    def client(self) -> AbstractAsyncContextManager["Api"]:
        """async with connection.client() as api:
        """
        ...
