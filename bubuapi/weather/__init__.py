from .base.qweather import QWEATHER
from quart import Blueprint, request, send_file
from io import BytesIO
    
weather_bp = Blueprint("weather", __name__)

qweather = QWEATHER()
key = 'b588acf3ef584912b1959af0b2dbd8e9'

@weather_bp.get('/get_weather_card')
async def get_weather_img():
    city_name: str = request.args.get('location')
    
    res = await qweather.qweather_get_weather(city_name, key)
    if res[0] != 'error':
        img = BytesIO(res[1])
        return await send_file(img, mimetype='image/png')
    else:
        return res[0]
            
