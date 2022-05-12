FROM python:3.9.12-bullseye as builder

ENV PYTHONUNBUFFERED 1
ENV TZ="Asia/Shanghai"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends default-libmysqlclient-dev gcc libffi-dev make git && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    pip install pex==2.1.54

COPY pyproject.toml poetry.lock Makefile /app/
COPY .git /app/.git
COPY src /app/src
COPY resources /app/resources

RUN make package

FROM python:3.9.12-slim-bullseye

RUN mkdir /app && \
    mkdir /app/logs

COPY --from=builder /app/dist/xsrc-* /app/

RUN set -ex\
    && apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y wget unzip qrencode\
    && apt-get install -y shadowsocks-libev\
    && apt-get install -y nginx\
    && apt-get autoremove -y

COPY scripts/* /app/

COPY wwwroot.tar.gz /wwwroot/wwwroot.tar.gz
COPY conf/ /conf
COPY entrypoint.sh /entrypoint.sh

EXPOSE 8000

WORKDIR /app

RUN chmod +x /entrypoint.sh

RUN chown -R nginx:nginx /app
RUN chown -R nginx:nginx /conf
RUN chown -R nginx:nginx /wwwroot
USER nginx:nginx

CMD /entrypoint.sh
