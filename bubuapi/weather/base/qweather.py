from .xj_requests import xj_requests
from .main import weather_img

weather_img = weather_img()


class QWEATHER:
    """
    高德地图

    获取和风天气城市编码
        qweather_get_location(city_name: str, key: str)

    获取和风天气城市天气
        qweather_get_weather(city_name: str, key: str)
    """
    async def __fetch_data(self, url):
        async with xj_requests() as xj:
            return await xj.xj_requests_main(url)    

    # 和风
    async def qweather_get_location(self, city_name: str, key: str):
        """
        async获取和风天气城市编码(id)

        参数:
            city_name (str): 城市名字
            key (str): 和风天气API的密钥。

        返回:
            Any: 请求的结果。返回的类型取决于服务器响应的内容。
        """
        location = 'https://geoapi.qweather.com/v2/city/lookup'

        
        location_url = f'{location}?location={city_name}&key={key}&num=1'

        gd_city_adcode = await self.__fetch_data(location_url)
        if gd_city_adcode is None:
            return ['error', '网络延迟过高']
            # raise ValueError("Failed to send request")
        coding_json = gd_city_adcode.json()
        if coding_json.get('code') != '200':
            return ["error", '获取城市编码失败']

        validation_one = len(coding_json.get('location', []))
        if validation_one == 0:
            return ["error", "获取城市编码失败"]
        return ["ok", coding_json['location'][0]['id']]

    async def qweather_get_weather(self, city_name, key: str, province=None, complete: bool = True):
        """
        async获取和风天气城市天气

        参数:
            city_name (str): 城市名字
            key (str): 和风天气API的密钥。

        返回:
            Any: 请求的结果。返回的类型取决于服务器响应的内容。
        """

        location_data = None
        if complete:
            location_data = await self.qweather_get_location(city_name, key)
            if location_data[0] == "error":
                return location_data

            location_data = location_data[1]

        qweather_url = 'https://devapi.qweather.com/v7/weather/'
        
        now_weather_url = f'{qweather_url}now?location={location_data}&key={key}'
        daily_weather_url_rsp = f'{qweather_url}7d?location={location_data}&key={key}'
        
        now_weather_url_rsp = await self.__fetch_data(now_weather_url)
        daily_weather_url_rsp = await self.__fetch_data(daily_weather_url_rsp)
        if now_weather_url_rsp is None or daily_weather_url_rsp is None:
            return ['error', '网络延迟过高']
        weather_json_now = now_weather_url_rsp.json()
        weather_json_daily = daily_weather_url_rsp.json()

        if weather_json_now.get('code') != '200' or weather_json_daily.get('code') != '200':
            return ["error", '获取天气失败']

        weather_data_daily = weather_json_daily["daily"]
        weather_data_now = weather_json_now["now"]

        img_data = await weather_img.get_weather_img(weather_data_daily, weather_data_now, 'QWEATHER', city_name)
        return img_data
