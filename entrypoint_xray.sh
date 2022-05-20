sed -e "/^#/d"\
    -e "s|\${Vless_UUID}|${Vless_UUID}|g"\
    -e "s|\${Vless_Path}|${Vless_Path}|g"\
    -e "s|\${Vmess_UUID}|${Vmess_UUID}|g"\
    -e "s|\${Vmess_Path}|${Vmess_Path}|g"\
    /conf/Xray.template.json >  /etc/xray/config.json
 
    
cat /etc/xray/config.json

/usr/bin/xray -config /etc/xray/config.json
