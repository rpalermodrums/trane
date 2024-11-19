from functools import wraps
import os
import json
import click
import requests
from pathlib import Path

CONFIG_DIR = Path.home() / '.transcribe'
CONFIG_FILE = CONFIG_DIR / 'config.json'

def ensure_config_dir():
    """Ensure config directory exists"""
    CONFIG_DIR.mkdir(exist_ok=True)

def save_config(config):
    """Save configuration to file"""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def load_config():
    """Load configuration from file"""
    if not CONFIG_FILE.exists():
        ensure_config_dir()
        save_config({})
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def get_token():
    config = load_config()
    return config.get('access_token')

def get_api_url():
    config = load_config()
    return config.get('api_url', 'http://localhost:8000')

def login(username: str, password: str) -> bool:
    """Authenticate user and save token"""
    api_url = get_api_url()
    response = requests.post(
        f'{api_url}/api/auth/token/',
        json={'username': username, 'password': password}
    )
    
    if response.status_code == 200:
        data = response.json()
        save_config({
            'access_token': data['access'],
            'refresh_token': data['refresh']
        })
        return True
    return False

def ensure_authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = get_token()
        if not token:
            click.echo('You are not logged in. Please run `transcribe login`.')
            exit(1)
        return func(*args, **kwargs)
    return wrapper
