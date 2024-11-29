from bubuapi import create_app
from loguru import logger
# from time import sleep
# from bubuapi.utils import sync
# from qqmusic_api import Credential

logger.add('log/app.log', retention='5 days')
app = create_app()

# def check_credential_state():    
#     """
#     检查凭证状态并自动刷新过期凭证。
#     """
    
#     while True:
#         my_credential: Credential = app.config['my_credential']
#         if my_credential is None:
#             # logger.info('未登录...')
#             sleep(1000)
#             continue
#         if sync(my_credential.is_expired()):
#             logger.info('凭证已过期，正在尝试刷新...')
#             try:
#                 sync(my_credential.refresh())
#             except Exception as e:
#                 logger.error(e)
        
#         sleep(1000)
    
# import threading
# threading.Thread(target=check_credential_state, daemon=True).start()    

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info")
    # pdm run hypercorn run:app
    # pdm run hypercorn -b 0.0.0.0:8000 run:app