import asyncio
from llm_completions import complete_response


REQUEST_QUEUE = asyncio.Queue()
RESPONSE_QUEUE = asyncio.Queue()


async def queue_worker():
    while True:
        #do queueing
        item = await REQUEST_QUEUE.get()
        question, complete_only = item
        if complete_only:
            complete_output = await complete_response(question)
        else:
            complete_output = await complete_response(question)
        REQUEST_QUEUE.task_done()
        await RESPONSE_QUEUE.put(complete_output)

async def llm_complete_request(question, complete_only=False):
    item = (question, complete_only)
    await REQUEST_QUEUE.put(item)
    completion = await RESPONSE_QUEUE.get()
    RESPONSE_QUEUE.task_done()
    return completion

async def init_request_queue():
    await asyncio.create_task(queue_worker())
