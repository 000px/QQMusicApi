import json
from loguru import logger
from os import path
from quart import Quart, send_file, request, redirect, url_for, jsonify
from quart_cors import cors
from qqmusic_api import search, song
from qqmusic_api.login import QRCodeLogin, QQLogin, WXLogin, PhoneLogin, refresh_cookies, Credential
from io import BytesIO
# from PIL import Image
# from pyzbar.pyzbar import decode
# from qrcode.main import QRCode
from dataclasses import asdict

app = Quart(__name__)
# 添加 CORS 支持
app = cors(app, allow_origin="*")
pwd = path.dirname(__file__)
pwdd = path.dirname(pwd)
# 配置日志记录器
logger.remove()
logger.add(f'{pwdd}/log/app.log', retention='5 days')

qrcode_login: QRCodeLogin = None
phone_login: PhoneLogin = None
credential: Credential = None
# 尝试打开并读取credential.json文件中的内容
try:
    with open(f'{pwd}/credential.json', 'r', encoding='utf-8') as f:
        credential = Credential.from_cookies(json.load(f))
except FileNotFoundError:
    # 如果文件不存在，则创建新文件
    with open(f'{pwd}/credential.json', 'w', encoding='utf-8') as f:
        pass
except json.JSONDecodeError as e:
    # 如果文件内容为空或格式错误，记录错误信息
    logger.error('credential.json 文件为空或格式错误')


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
    song_mid: str = result[0].get('mid', '')
    song_id: int = result[0].get('id', '')
    song_name: str = result[0].get('name', '')
    singer: str = result[0]['singer'][0].get('name', '')
    vs = result[0]['vs'][0]
    album_mid: str = result[0]['album'].get('mid', '')
    # 获取专辑图片的URL
    album_url: str = f'https://y.qq.com/music/photo_new/T002R300x300M000{album_mid}.jpg'

    # 获取歌曲的试听URL
    try_url = await song.get_try_url(song_mid, vs)
    
    # 获取歌曲的播放URL
    url = (await song.get_song_urls([song_mid], song.SongFileType.MP3_320, credential))[song_mid]
    
    # 记录日志
    logger.info(f'name:{song_name}\nsinger:{singer}\ntry_url:{try_url}\nurl:{url}\nalbum_url:{album_url}')
    
    # 返回歌曲信息的JSON响应
    return jsonify({'song_mid': song_mid, 'song_id': song_id, 'name': song_name, 'singer': singer, 'try_url': try_url, 'url': url, 'album_url': album_url})


if __name__ == '__main__':
    app.run()
    # hypercorn --reload api.index:app
    # hypercorn api.index:app
    # hypercorn -b 0.0.0.0:8000 api.index:app