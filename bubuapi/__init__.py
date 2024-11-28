import json

from loguru import logger
from quart import Quart
from quart_cors import cors
from qqmusic_api import Credential

from .qqmusic import login_bp, credential_bp, song_bp
from .weather import weather_bp


def create_app():
    app = Quart(__name__)
    # 添加 CORS 支持
    app = cors(app, allow_origin="*")
    
    app.register_blueprint(login_bp)
    app.register_blueprint(credential_bp)
    app.register_blueprint(song_bp)
    
    app.register_blueprint(weather_bp, url_prefix='/weather')    

    app.config['my_credential'] = None
    init_credential(app)    
    
    return app

    
def init_credential(app):
    # 获取上次登录储存的credential
    try:
        with open('bubuapi/qqmusic/credential.json', 'r', encoding='utf-8') as f:
            app.config['my_credential'] = Credential.from_cookies_dict(json.load(f))
    except FileNotFoundError:
        # 如果文件不存在，则创建新文件
        with open('bubuapi/qqmusic/credential.json', 'w', encoding='utf-8') as f:
            pass
    except json.JSONDecodeError as e:
        # 如果文件内容为空或格式错误，记录错误信息
        logger.error('credential.json 文件为空或格式错误')