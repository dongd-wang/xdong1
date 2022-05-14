import base64
import re
import json
import requests
from fastapi.routing import APIRouter
from fastapi.responses import FileResponse
from loguru import logger
import time
import os


router = APIRouter()


@router.get("/xsrc")
def generate():
    headers = {
        # 'Accept-Encoding' : 'gzip, deflate, br',
        'Connection' : 'keep-alive',
        'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
        'Accept-Language' : 'en-US,en;q=0.9',
        'upgrade-insecure-requests': '1'
    }
    url = os.getenv('SS_URL')
    resp = requests.get(url, headers=headers)
    if resp.status_code >= 400:
        return "hello error"
    # logger.info(resp.content)
    try:
        vmess_url = re.findall('vmess://.*=', resp.content.decode('UTF-8'))
        jsonData = json.loads(base64.b64decode(vmess_url[0][8:]).decode('utf-8'))

        quanx_vmess = 'vmess=' + jsonData['add'] + ':' + jsonData['port'] + ', method=' \
            + jsonData['type'] + ', password=' + jsonData['id'] + ', obfs=wss, obfs-host=' \
                + jsonData['add'] + ', obfs-uri=' + jsonData['path'] \
                    + ', tls-verification=false, fast-open=false, udp-relay=false, aead=false, tag=ssfree_' \
                    + str(time.time())
        with open('.tmp/subscribe', 'w', encoding='utf-8') as f:
            f.write(quanx_vmess)
    except Exception as e:
        logger.exception(e)
        return "hello remote error"
    return "hello world"

@router.get('/sub')
async def get_sub():
    generate()
    return FileResponse(path='.tmp/subscribe', media_type='application/octet-stream', filename='subscribe')


@router.get('/show')
async def get_data():
    vless_uuid = os.getenv('Vless_UUID')
    vless_path = os.getenv('Vless_Path')
    vless_url = f'vless://{vless_uuid}@$***:443?path={vless_path}&security=tls&encryption=none&type=ws#te-Vless'
    return vless_url
