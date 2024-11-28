from typing import Coroutine
from asyncio import new_event_loop, get_event_loop

def sync(coroutine: Coroutine):
    try:
        loop = get_event_loop()
    except RuntimeError:
        loop = new_event_loop()
        
    loop.run_until_complete(coroutine)
        
        
        