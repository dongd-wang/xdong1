#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2021-04-07 10:27:40
# @Author  : Your Name (you@example.org)
# @Link    : link
# @Version : 1.0.0

import os

import typer
from loguru import logger


app = typer.Typer()


@app.command()
def ping():
    logger.info('pong')

@app.command()
def version():
    pass

@app.command()
def runserver():
    from src.commands.webserver_command import webserver
    webserver()

if __name__ == "__main__":
    app()