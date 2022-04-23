import asyncio
from abc import abstractmethod


class AsyncObjectFactory:

    @abstractmethod
    async def create(self):
        raise NotImplementedError()


class AsyncObjectPool:

    async def new_instance(factory: AsyncObjectFactory, max_size: int):
        self = AsyncObjectPool()
        self.factory = factory
        self.max_size = max_size
        self.pool = asyncio.queues.Queue(max_size)
        self.mutex = asyncio.Lock()
        self.n_created = 0
        return self

    async def acquire(self):
        async with self.mutex:
            if self.pool.empty():
                if self.n_created < self.max_size:
                    await self.pool.put(await self.factory.create())
                    self.n_created += 1
        return await self.pool.get()

    async def release(self, obj):
        await self.pool.put(obj)


if __name__ == '__main__':
    class Integer:
        def __init__(self, val):
            self.val = val

    cnt = 0

    class IntegerFactory(AsyncObjectFactory):
        async def create(self):
            global cnt
            cnt += 1
            return Integer(cnt)

    async def test():
        pool = await AsyncObjectPool.new_instance(IntegerFactory(), 3)
        a = await pool.acquire()
        assert(a.val == 1)
        b = await pool.acquire()
        assert(b.val == 2)
        await pool.release(a)
        c = await pool.acquire()
        assert(c.val == 1)

    event_loop = asyncio.new_event_loop()
    task = event_loop.create_task(test())
    event_loop.run_until_complete(task)
