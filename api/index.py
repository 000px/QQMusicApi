from logging import handlers, Formatter, INFO
from os import path
from quart import Quart, send_file, request, redirect, url_for, jsonify
from qqmusic_api import search, song
from qqmusic_api.login import QRCodeLogin, QQLogin, WXLogin, PhoneLogin, refresh_cookies
from io import BytesIO
# from PIL import Image
# from pyzbar.pyzbar import decode
# from qrcode.main import QRCode

app = Quart(__name__)
pwd = path.dirname(path.dirname(__file__))
# 配置日志记录器
handler = handlers.RotatingFileHandler(f'{pwd}/log/app.log', maxBytes=10485760, backupCount=2, encoding='utf-8')
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(INFO)

qrcode_login: QRCodeLogin = None
phone_login: PhoneLogin = None
credential = None

@app.route('/login')
async def login():
    global qrcode_login, phone_login
    type = request.args.get('type')
    match type:
        case 'QQ':
            qrcode_login = QQLogin()
        case 'WX':
            qrcode_login = WXLogin()
        case 'Phone':
            phone_login = PhoneLogin()
        case _:
            return '无效的登陆方式'
    
    return redirect(url_for('_getqrcode'))

@app.route('/qrshow')
async def _getqrcode():
    if not qrcode_login:
        return '未选择登陆方式'
    data = await qrcode_login.get_qrcode()
    # 制作二维码并在控制台展示
    img = BytesIO(data)
    # url = decode(img)[0].data.decode("utf-8")
    # qr = QRCode()
    # qr.add_data(url)
    # qr.print_ascii()
    return await send_file(img, mimetype='image/png')

@app.route('/qrstate')
async def _get_qrcode_state():
    global credential
    if not qrcode_login:
        return '未选择登陆方式'
    
    from qqmusic_api.login import QrCodeLoginEvents

    state = await qrcode_login.get_qrcode_state()
    message = ''
    match state:
        case QrCodeLoginEvents.REFUSE:
            message =  "拒绝登录"
        case QrCodeLoginEvents.TIMEOUT:
            message =  "二维码过期"
        case QrCodeLoginEvents.CONF:
            message =  "请确认登录"
        case QrCodeLoginEvents.SCAN:
            message = "请扫描二维码"
        case QrCodeLoginEvents.DONE:
            credential = await qrcode_login.authorize()
            message = "登录成功"
        
    return jsonify({'message': message})

@app.route('/refresh')
async def _refresh():
    global credential
    credential = await refresh_cookies(credential=credential)
    return jsonify({'state': 'sucess'})
    

@app.route('/getsong', methods=['GET'])
async def getsong():
    song_name = request.args.get('text')
    # 搜索歌曲
    result = await search.search_by_type(keyword=song_name, search_type=search.SearchType.SONG, num=1)
    # result = await search.quick_search(song_name)
    app.logger.info(result)
    # return result
    mid = ''
    id = ''
    # vs = ''
    # 打印结果
    mid = result[0].get('mid', '')
    _id = result[0].get('id', '')
    name = result[0].get('name', '')
    singer = result[0]['singer'][0].get('name', '')
    vs = result[0]['vs'][0]

    s = song.Song(mid=mid, id=_id)
    try_url = await song.get_try_url(mid, vs)
    url = await s.get_url(credential=credential)

    app.logger.info(f'name:{name}\nsinger:{singer}\ntry_url:{try_url}\nurl:{url}')
    
    return jsonify({'name': name, 'singer': singer, 'try_url': try_url, 'url': url})

if __name__ == '__main__':
    app.run()