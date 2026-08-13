import asyncio
import logging

# i plan to expand this later
class TaskManager:
    def __init__(self):
        pass

    def add_task(self, coro, *args, **kwargs):
        task = asyncio.create_task(coro(*args, **kwargs))
        task.set_name(f"Task-{coro.__name__}")
        logging.info(f"[TaskManager] Executing task: {task.get_name()}")
        task.add_done_callback(lambda t: logging.info(f"[TaskManager] Task {t.get_name()} completed with result: {t.result()}"))
        return task

    def add_periodic_task(self, coro, interval, *args, **kwargs):
        async def wrapper():
            while True:
                logging.info(f"[TaskManager] Executing periodic task: {coro.__name__}")
                try:
                    await coro(*args, **kwargs)
                except Exception:
                    logging.exception(f"[TaskManager] Periodic task {coro.__name__} failed")
                await asyncio.sleep(interval)

        task = asyncio.create_task(wrapper())
        task.set_name(f"Periodic-{coro.__name__}")
        return task


