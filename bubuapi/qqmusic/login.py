from quart import jsonify, Blueprint, request, redirect, url_for, send_file, current_app
from qqmusic_api.login import QQLogin, WXLogin, PhoneLogin, QRCodeLogin, Credential


login_bp = Blueprint("login", __name__)

qrcode_login: QRCodeLogin = None
phone_login: PhoneLogin = None

@login_bp.route("/login", methods=["GET"])
async def login():
    """
    登录，三种方式。type = QQ/WX/Phone 

    Returns:
        对于有效的登录类型，通过重定向到'_getqrcode'页面进行下一步处理。
    """
    
    global qrcode_login, phone_login
        
    type = request.args.get('type')  # 从请求参数中获取登录类型
    
    # 根据登录类型实例化相应的登录类
    match type:
        case 'QQ':
            qrcode_login = QQLogin()  # 实例化QQ登录
        case 'WX':
            qrcode_login = WXLogin()  # 实例化微信登录
        case 'Phone':
            # phone_login = PhoneLogin()  # 实例化手机登录
            return jsonify({'state': 'error', 'message': 'unimplemented'})
        case _:
            return jsonify({'state': 'error', 'message': '无效的登陆方式'})
    
    return redirect(url_for('login.qrshow'))  # 对于有效类型，重定向到二维码获取页面

@login_bp.route('/qrshow')
async def qrshow():
    """
    获取二维码图片。

    """
    global qrcode_login, phone_login
    # 如果未选择二维码登录方式，则返回错误信息
    if not qrcode_login:
        return jsonify({'state': 'error', 'message': '未选择登陆方式'})
    # 获取二维码数据
    data = await qrcode_login.get_qrcode()
    # 将二维码数据转换为图像并保存在内存中
    from io import BytesIO
    img = BytesIO(data)
    # 下面的代码用于在控制台中解码并打印二维码
    # url = decode(img)[0].data.decode("utf-8")
    # qr = QRCode()
    # qr.add_data(url)
    # qr.print_ascii()
    # 发送二维码图像文件给客户端，文件类型为PNG
    return await send_file(img, mimetype='image/png')

@login_bp.route('/qrstate')
async def _get_qrcode_state():
    """
    获取二维码登录状态。
    登录成功将会更新保存凭证到本地credential.json文件中。
    """
    global qrcode_login
    
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
            my_credential: Credential = await qrcode_login.authorize()
            current_app.config['my_credential'] = my_credential
            with open('bubuapi/qqmusic/credential.json', 'w', encoding='utf-8') as f:
                from json import dump
                dump(my_credential.as_dict(), f, ensure_ascii=False, indent=4)
            message = "登录成功"
    
    # 返回登录状态和对应信息
    return jsonify({'state': 'success', 'message': message})