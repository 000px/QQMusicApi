from quart import Blueprint, jsonify, current_app
from qqmusic_api import Credential

credential_bp = Blueprint('credential', __name__)

@credential_bp.route('/refresh', methods=['GET', 'POST'])
async def refresh():
    """
    此函数用于刷新凭证，并更新凭证文件。
    """
    my_credential: Credential = current_app.config['my_credential']
    
    if my_credential is None: return jsonify({'state': 'error', 'message': '未登录'})
    
    if not await my_credential.can_refresh():
        return jsonify({'state': 'error', 'message': '凭证无法刷新'})

    if await my_credential.refresh():
        return jsonify({'state': 'sucess', 'message': '凭证刷新成功'})
    else:
        return jsonify({'state': 'error', 'message': '凭证刷新失败'})
