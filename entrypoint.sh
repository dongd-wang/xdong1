#!/bin/bash

#Xray版本
if [[ -z "${VER}" ]]; then
  VER="latest"
fi
echo ${VER}

if [[ -z "${Vless_Path}" ]]; then
  Vless_Path="/s233"
fi
echo ${Vless_Path}

if [[ -z "${Vless_UUID}" ]]; then
  Vless_UUID="5c301bb8-6c77-41a0-a606-4ba11bbab084"
fi
echo ${Vless_UUID}

if [[ -z "${Vmess_Path}" ]]; then
  Vmess_Path="/s244"
fi
echo ${Vmess_Path}

if [[ -z "${Vmess_UUID}" ]]; then
  Vmess_UUID="5c301bb8-6c77-41a0-a606-4ba11bbab084"
fi
echo ${Vmess_UUID}

if [[ -z "${Share_Path}" ]]; then
  Share_Path="/share233"
fi
echo ${Share_Path}

if [ "$VER" = "latest" ]; then
  VER=`wget -qO- "https://api.github.com/repos/XTLS/Xray-core/releases/latest" | sed -n -r -e 's/.*"tag_name".+?"([vV0-9\.]+?)".*/\1/p'`
  [[ -z "${VER}" ]] && VER="v1.2.2"
else
  VER="v$VER"
fi


# mkdir /xraybin
# cd /xraybin

# RAY_URL="https://github.com/XTLS/Xray-core/releases/download/${VER}/Xray-linux-64.zip"
# echo ${RAY_URL}
# wget --no-check-certificate ${RAY_URL}
# unzip Xray-linux-64.zip
# rm -f Xray-linux-64.zip
# chmod +x ./xray
# ls -al

# ==================================
PLATFORM=$1
if [ -z "$PLATFORM" ]; then
    ARCH="amd64"
else
    case "$PLATFORM" in
        linux/386)
            ARCH="386"
            ;;
        linux/amd64)
            ARCH="amd64"
            ;;
        linux/arm/v6)
            ARCH="arm6"
            ;;
        linux/arm/v7)
            ARCH="arm7"
            ;;
        linux/arm64|linux/arm64/v8)
            ARCH="arm64"
            ;;
        linux/ppc64le)
            ARCH="ppc64le"
            ;;
        linux/s390x)
            ARCH="s390x"
            ;;
        *)
            ARCH=""
            ;;
    esac
fi
[ -z "${ARCH}" ] && echo "Error: Not supported OS Architecture" && exit 1
# Download binary file
XRAY_FILE="xray_linux_${ARCH}"

echo "Downloading binary file: ${XRAY_FILE}"
wget -O /usr/bin/xray https://dl.lamp.sh/files/${XRAY_FILE} > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Failed to download binary file: ${XRAY_FILE}" && exit 1
fi
echo "Download binary file: ${XRAY_FILE} completed"

chmod +x /usr/bin/xray
# ==================================






cd /wwwroot
tar xvf wwwroot.tar.gz
rm -rf wwwroot.tar.gz


sed -e "/^#/d"\
    -e "s/\${Vless_UUID}/${Vless_UUID}/g"\
    -e "s|\${Vless_Path}|${Vless_Path}|g"\
    -e "s/\${Vmess_UUID}/${Vmess_UUID}/g"\
    -e "s|\${Vmess_Path}|${Vmess_Path}|g"\
    /conf/Xray.template.json >  /etc/xray/config.json
echo /etc/xray/config.json
cat /etc/xray/config.json

if [[ -z "${ProxySite}" ]]; then
  s="s/proxy_pass/proxy_pass/g"
  echo "site:use local wwwroot html"
else
  s="s|\${ProxySite}|${ProxySite}|g"
  echo "site: ${ProxySite}"
fi

sed -e "/^#/d"\
    -e "s/\${PORT}/${PORT}/g"\
    -e "s|\${Vless_Path}|${Vless_Path}|g"\
    -e "s|\${Vmess_Path}|${Vmess_Path}|g"\
    -e "s|\${Share_Path}|${Share_Path}|g"\
    -e "$s"\
    /conf/nginx.template.conf > /etc/nginx/conf.d/ray.conf
echo /etc/nginx/conf.d/ray.conf
cat /etc/nginx/conf.d/ray.conf

[ ! -d /wwwroot/${Share_Path} ] && mkdir -p /wwwroot/${Share_Path}
sed -e "/^#/d"\
    -e "s|\${_Vless_Path}|${Vless_Path}|g"\
    -e "s|\${_Vmess_Path}|${Vmess_Path}|g"\
    -e "s/\${_Vless_UUID}/${Vless_UUID}/g"\
    -e "s/\${_Vmess_UUID}/${Vmess_UUID}/g"\
    -e "$s"\
    /conf/share.html > /wwwroot${Share_Path}/index.html
echo /wwwroot${Share_Path}/index.html
cat /wwwroot${Share_Path}/index.html

mkdir /app/.tmp
ls -al /app

mkdir /var/log/supervisor

# cd /xraybin
# ./xray run -c ./config.json &
/usr/bin/xray run -c /etc/xray/config.json  &
cd /app
./start runserver & 
rm -rf /etc/nginx/sites-enabled/default
nginx -V
nginx -t
nginx -g 'daemon off;'
# nginx -t
# supervisord -c /etc/supervisord.conf
