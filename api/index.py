import json
from loguru import logger
from os import path
from quart import Quart, send_file, request, redirect, url_for, jsonify
from qqmusic_api import search, song
from qqmusic_api.login import QRCodeLogin, QQLogin, WXLogin, PhoneLogin, refresh_cookies, Credential
from io import BytesIO
# from PIL import Image
# from pyzbar.pyzbar import decode
# from qrcode.main import QRCode
from dataclasses import asdict

app = Quart(__name__)
pwd = path.dirname(__file__)
pwdd = path.dirname(pwd)
# 配置日志记录器
logger.remove()
logger.add(f'{pwdd}/log/app.log', retention='5 days')

qrcode_login: QRCodeLogin = None
phone_login: PhoneLogin = None
credential: Credential = None
with open(f'{pwd}/credential.json', 'r', encoding='utf-8') as f:
    try:
        credential = Credential.from_cookies(json.load(f))
    except Exception as e:
        logger.error(e)

@app.route('/login')
async def login():
    """
    登录页面路由函数，支持多种登录方式。

    此函数根据请求中的类型参数，选择不同的登录方式，包括QQ登录、微信登录和手机登录。
    对于每种登录类型，实例化相应的登录类，并进行相应的跳转或处理。

    参数:
    - 无

    返回:
    - 对于无效的登录类型，直接返回提示字符串。
    - 对于有效的登录类型，通过重定向到'_getqrcode'页面进行下一步处理。
    """
    global qrcode_login, phone_login  # 声明全局变量以存储登录实例
    
    type = request.args.get('type')  # 从请求参数中获取登录类型
    
    # 根据登录类型实例化相应的登录类
    match type:
        case 'QQ':
            qrcode_login = QQLogin()  # 实例化QQ登录
        case 'WX':
            qrcode_login = WXLogin()  # 实例化微信登录
        case 'Phone':
            phone_login = PhoneLogin()  # 实例化手机登录
        case _:
            return jsonify({'state': 'error', 'message': '无效的登陆方式'})
    
    return redirect(url_for('_getqrcode'))  # 对于有效类型，重定向到二维码获取页面

@app.route('/qrshow')
async def _getqrcode():
    """
    获取二维码图片。

    """
    # 如果未选择二维码登录方式，则返回错误信息
    if not qrcode_login:
        return jsonify({'state': 'error', 'message': '未选择登陆方式'})
    # 获取二维码数据
    data = await qrcode_login.get_qrcode()
    # 将二维码数据转换为图像并保存在内存中
    img = BytesIO(data)
    # 下面的代码用于在控制台中解码并打印二维码
    # url = decode(img)[0].data.decode("utf-8")
    # qr = QRCode()
    # qr.add_data(url)
    # qr.print_ascii()
    # 发送二维码图像文件给客户端，文件类型为PNG
    return await send_file(img, mimetype='image/png')

@app.route('/qrstate')
async def _get_qrcode_state():
    """
    获取二维码登录状态。
    
    此函数用于检查二维码的登录状态，并根据状态返回相应的信息。如果二维码登录未被选择，
    则返回错误信息。匹配不同的登录状态，返回不同的状态信息，如二维码过期、请扫描二维码、
    请确认登录、登录成功等，并在登录成功后更新凭证文件。
    """
    global credential
    # 检查是否选择了二维码登录方式
    if not qrcode_login:
        return jsonify({'state': 'error', 'message': '未选择登陆方式'})
    
    # 导入二维码登录事件枚举类
    from qqmusic_api.login import QrCodeLoginEvents

    # 获取当前二维码登录状态
    state = await qrcode_login.get_qrcode_state()
    message = ''
    # 根据不同的登录状态，返回不同的状态信息
    match state:
        case QrCodeLoginEvents.REFUSE:
            message = "拒绝登录"
        case QrCodeLoginEvents.TIMEOUT:
            message = "二维码过期"
        case QrCodeLoginEvents.CONF:
            message = "请确认登录"
        case QrCodeLoginEvents.SCAN:
            message = "请扫描二维码"
        case QrCodeLoginEvents.DONE:
            # 登录成功后，获取凭证并保存到文件中
            credential = await qrcode_login.authorize()
            with open(f'{pwd}/credential.json', 'w', encoding='utf-8') as f:
                json.dump(asdict(credential), f, ensure_ascii=False, indent=4)
            message = "登录成功"
    
    # 返回登录状态和对应信息
    return jsonify({'state': 'success', 'message': message})

@app.route('/refresh')
async def _refresh():
    """
    此函数用于刷新凭证，并更新凭证文件。

    """
    global credential
    credential = await refresh_cookies(credential=credential)
    # 将刷新后的凭证保存到本地文件中，以便后续使用
    with open(f'{pwd}/credential.json', 'w', encoding='utf-8') as f:
            json.dump(asdict(credential), f, ensure_ascii=False, indent=4)
    
    return jsonify({'state': 'sucess'})

@app.route('/getsong', methods=['GET'])
async def getsong():
    """
    获取歌曲信息并返回JSON格式的数据。

    """
    global credential
    
    # 从请求参数中获取歌曲名称
    if (song_name := request.args.get('text')) is None:
        return jsonify({'state': 'error', 'message': '请输入歌曲名称'})
    
    result = await search.search_by_type(keyword=song_name, search_type=search.SearchType.SONG, num=1)
    # 提取搜索结果中的歌曲信息
    mid = result[0].get('mid', '')
    _id = result[0].get('id', '')
    name = result[0].get('name', '')
    singer = result[0]['singer'][0].get('name', '')
    vs = result[0]['vs'][0]
    
    # 创建Song对象
    s = song.Song(mid=mid, id=_id)
    
    # 获取歌曲的试听URL
    try_url = await song.get_try_url(mid, vs)
    
    # 获取歌曲的播放URL
    url = await s.get_url(credential=credential)
    
    # 记录日志，输出歌曲信息
    logger.info(f'name:{name}\nsinger:{singer}\ntry_url:{try_url}\nurl:{url}')
    
    # 返回歌曲信息的JSON响应
    return jsonify({'name': name, 'singer': singer, 'try_url': try_url, 'url': url})


if __name__ == '__main__':
    app.run()
    # hypercorn --reload api.index:app
    # hypercorn api.index:app