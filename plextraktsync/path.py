from __future__ import annotations

from plextraktsync.util.Path import Path

p = Path()

cache_dir = p.cache_dir
config_dir = p.config_dir
log_dir = p.log_dir

module_path = p.module_path
default_config_file = p.default_config_file
config_file = p.config_file
config_yml = p.config_yml
servers_config = p.servers_config
pytrakt_file = p.pytrakt_file
env_file = p.env_file
