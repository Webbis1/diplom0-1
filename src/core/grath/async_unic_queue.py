from asyncio import Queue

class AsyncUnicQueue[T]:
    def __init__(self) -> None:
        self.__queue: Queue[T] = Queue()
        self.__pending: set[T] = set()
    
    async def put(self, item: T) -> None:
        if item not in self.__pending:
            self.__pending.add(item)
            await self.__queue.put(item)

    async def get(self) -> T:
        item: T = await self.__queue.get()
        self.__pending.discard(item)
        return item

    def task_done(self) -> None:
        self.__queue.task_done()

    async def join(self) -> None:
        await self.__queue.join()

    def empty(self) -> bool:
        return self.__queue.empty()

    def qsize(self) -> int:
        return self.__queue.qsize()