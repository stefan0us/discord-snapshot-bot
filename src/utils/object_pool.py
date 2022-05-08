import asyncio
from typing import Callable


class AsyncObjectPool:

    async def new_instance(create_func: Callable, max_size: int = 3, *args, **kwargs):
        self = AsyncObjectPool()
        self.create_func = create_func
        self.args = args
        self.kwargs = kwargs
        self.max_size = max_size
        self.pool = asyncio.queues.Queue(max_size)
        self.mutex = asyncio.Lock()
        self.n_created = 0
        return self

    async def acquire(self):
        async with self.mutex:
            if self.pool.empty():
                if self.n_created < self.max_size:
                    if asyncio.iscoroutinefunction(self.create_func):
                        new_object = await self.create_func(*self.args, **self.kwargs)
                    else:
                        new_object = self.create_func(*self.args, **self.kwargs)
                    await self.pool.put(new_object)
                    self.n_created += 1
        return await self.pool.get()

    async def release(self, obj):
        await self.pool.put(obj)


if __name__ == '__main__':
    from itertools import count

    cnt = count(0)

    async def test():
        global cnt
        pool = await AsyncObjectPool.new_instance(cnt.__next__, 3)
        a = await pool.acquire()
        assert(a == 0)
        b = await pool.acquire()
        assert(b == 1)
        await pool.release(a)
        c = await pool.acquire()
        assert(c == 0)

    event_loop = asyncio.new_event_loop()
    task = event_loop.create_task(test())
    event_loop.run_until_complete(task)
