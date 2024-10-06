import json

from loguru import logger
from quart import Quart
from quart_cors import cors
from src.routes import login_bp, credential_bp, song_bp
from qqmusic_api import Credential

# 配置日志记录器
logger.remove()
logger.add('log/app.log', retention='5 days')

app = Quart(__name__)
# 添加 CORS 支持
app = cors(app, allow_origin="*")

app.register_blueprint(login_bp)
app.register_blueprint(credential_bp)
app.register_blueprint(song_bp)

app.config['my_credential'] = None

# 获取上次登录储存的credential
try:
    with open('src/credential.json', 'r', encoding='utf-8') as f:
        app.config['my_credential'] = Credential.from_cookies_dict(json.load(f))
except FileNotFoundError:
    # 如果文件不存在，则创建新文件
    with open('src/credential.json', 'w', encoding='utf-8') as f:
        pass
except json.JSONDecodeError as e:
    # 如果文件内容为空或格式错误，记录错误信息
    logger.error('credential.json 文件为空或格式错误')
        
def check_credential_state():    
    """
    检查凭证状态并自动刷新过期凭证。
    """
    from time import sleep
    from src.utils import sync
    while True:
        my_credential: Credential = app.config['my_credential']
        if my_credential is None:
            # logger.info('未登录...')
            sleep(100)
            continue
        if sync(my_credential.is_expired()):
            logger.info('凭证已过期，正在尝试刷新...')
            try:
                sync(my_credential.refresh())
            except Exception as e:
                logger.error(e)
        
        sleep(100)
    
import threading
threading.Thread(target=check_credential_state, daemon=True).start()    

if __name__ == '__main__':
    app.run()
    # pdm run hypercorn index:app
    # pdm run hypercorn -b 0.0.0.0:8000 index:app