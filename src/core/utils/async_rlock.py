from __future__ import annotations
from typing import Optional, Any
from decimal import Decimal

import asyncio

class AsyncRLock:
    def __init__(self) -> None:
        self._lock: asyncio.Lock = asyncio.Lock()
        self._owner: Optional[asyncio.Task[Any]] = None
        self._count: int = 0

    async def acquire(self) -> bool:
        task: Optional[asyncio.Task[Any]] = asyncio.current_task()
        if self._owner == task:
            self._count += 1
            return True
        await self._lock.acquire()
        self._owner = task
        self._count = 1
        return True

    def release(self) -> None:
        task: Optional[asyncio.Task[Any]] = asyncio.current_task()
        if self._owner != task:
            raise RuntimeError("Cannot release un-acquired lock")
        self._count -= 1
        if self._count == 0:
            self._owner = None
            self._lock.release()

    async def __aenter__(self) -> AsyncRLock:
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()