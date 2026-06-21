import asyncio

class Broadcaster:
    def __init__(self):
        self._queues = []  # список личных очередей
        self.work = True
    
    async def listen(self):
        """Запускаем один источник (например, WebSocket)"""
        for i in range(5):
            # Это имитация сообщений из WebSocket
            msg = f"Новость {i}"
            print(f"Пришло: {msg}")
            
            # Кладем это сообщение в очередь КАЖДОГО подписчика
            for q in self._queues:
                await q.put(msg)
            
            await asyncio.sleep(1)
            
    
    async def subscribe(self):
        """Подписчик получает свою личную очередь"""
        q = asyncio.Queue()
        self._queues.append(q)
        
        
        while self.work:
            msg = await q.get()
            yield msg

async def subscriber(name, broadcaster):
    
    async for msg in broadcaster.subscribe():
        print(msg)

async def main():
    b = Broadcaster()
    
    # Запускаем источник (он будет рассылать)
    asyncio.create_task(b.listen())
    
    # Запускаем трех подписчиков
    await asyncio.gather(
        subscriber("Алиса", b),
        subscriber("Боб", b),
        subscriber("Чарли", b),
    )
    
asyncio.run(main())