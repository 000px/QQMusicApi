from loguru import logger
from quart import Blueprint, jsonify, request, current_app
from qqmusic_api import search, song, Credential


song_bp = Blueprint('song', __name__)

@song_bp.route('/getsong', methods=['GET'])
async def getsong():
    """
    获取歌曲信息并返回JSON格式的数据。
    text = songname/songname singer

    """
    
    my_credential: Credential = current_app.config['my_credential']
    
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
    # album_url: str = f'https://y.qq.com/music/photo_new/T002R300x300M000{album_mid}.jpg'

    # 获取歌曲的试听URL
    try_url = await song.get_try_url(song_mid, vs)
    
    # 获取歌曲的播放URL
    from qqmusic_api.exceptions import CredentialExpiredError
    try:
        url = (await song.get_song_urls([song_mid], song.SongFileType.MP3_320, my_credential))[song_mid]
    except CredentialExpiredError as e:
        logger.error(e)
        if await my_credential.refresh():
            url = (await song.get_song_urls([song_mid], song.SongFileType.MP3_320, my_credential))[song_mid]
        else:
            url = ''
    
    data = {
        'song_mid': song_mid,
        'song_id': song_id, 
        'name': song_name, 
        'singer': singer,
        'try_url': try_url, 
        'url': url,
        'album_mid': album_mid
    }
    
    # 记录日志
    logger.info(data)
    # 返回歌曲信息的JSON响应
    return jsonify(data)