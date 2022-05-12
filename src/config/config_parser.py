#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2021-10-25 10:34:22
# @Author  : Your Name (you@example.org)
# @Link    : link
# @Version : 1.0.0

from configparser import ConfigParser
from functools import lru_cache
import os
from typing import Dict

@lru_cache(maxsize=1)
def read_config_file() -> Dict[str, str]:
    config_file = os.environ.get('CONFIG_FILE', '')
    if not config_file:
        return {}
    conf = ConfigParser()
    conf.read(config_file)
    env_arg = conf.get('ENV', 'ENV')
    config_dict = {}
    config_dict['db_host'] = conf.get(env_arg, 'Server', fallback=None)
    config_dict['db_user'] = conf.get(env_arg, 'UID', fallback=None)
    config_dict['db_pwd'] = conf.get(env_arg, 'SQL_PWD', fallback=None)
    config_dict['database'] = conf.get(env_arg, 'Database', fallback=None)
    config_dict['solr_host'] = conf.get(env_arg, 'SolrHost', fallback=None)
    config_dict['solr_port'] = conf.get(env_arg, 'SolrPort', fallback=None)
    config_dict['collection'] = conf.get(env_arg, 'SolrCollection', fallback=None)
    config_dict['app_domain'] = conf.get(env_arg, 'AppDomain', fallback=None)
    config_dict['web_domain'] = conf.get(env_arg, 'WebDomain', fallback=None)
    config_dict['server'] = conf.get(env_arg, 'Server', fallback=None)
    return config_dict