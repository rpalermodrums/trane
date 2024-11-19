import click
import requests
import os
import time
from pathlib import Path
from .auth import (
    get_api_url,
    login, 
    ensure_authenticated, 
    get_token, 
    load_config, 
    save_config
)

@click.group()
def cli():
    """Transcribe CLI for audio source separation"""
    pass

@cli.command(name='login')
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def login_command(username, password):
    """Login to the Transcribe service"""
    if login(username, password):
        click.echo('Login successful')
    else:
        click.echo('Login failed')

@cli.command(name='process')
@ensure_authenticated
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output directory path')
@click.option('--model', default='htdemucs', help='Demucs model version')
@click.option('--instruments', multiple=True, help='Specific instruments to separate')
def process(input_file, output, model, instruments):
    """Process audio file for source separation.

    INPUT_FILE: Path to the audio file to process
    """
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    files = {'audio_file': open(input_file, 'rb')}
    data = {
        'model': model,
        'instruments': instruments,
    }

    api_url = get_api_url()
    click.echo(f'API URL: {api_url}')
    response = requests.post(
        f'{api_url}/api/entries/process_cli/',
        headers=headers,
        files=files,
        data=data
    )
    click.echo(f'Response: {response.text}')

    if response.status_code == 200:
        result = response.json()
        click.echo(f"Task started with ID: {result['task_id']}")
    else:
        click.echo('Failed to start processing task')

@cli.command(name='status')
@ensure_authenticated
@click.argument('task_id')
def status(task_id):
    """Check the status of a processing task"""
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    api_url = get_api_url()
    response = requests.get(
        f'{api_url}/api/entries/{task_id}/task_status/',
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        click.echo(f"Task {task_id} status: {result['status']}")
    else:
        click.echo('Failed to get task status')

@cli.command(name='progress')
@ensure_authenticated
@click.argument('task_id')
def progress(task_id):
    """Monitor the progress of a processing task in real-time"""
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    api_url = get_api_url()
    with click.progressbar(length=100, label='Processing') as bar:
        last_progress = 0
        while True:
            response = requests.get(
                f'{api_url}/api/entries/{task_id}/task_status/',
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                current_progress = result.get('progress', last_progress)
                status = result.get('status')

                if current_progress > last_progress:
                    bar.update(current_progress - last_progress)
                    last_progress = current_progress

                if status in ['completed', 'failed']:
                    click.echo(f"\nTask {status}")
                    break
            else:
                click.echo('Failed to get task status')
                break

            time.sleep(1)

@cli.command(name='config')
@click.option('--api-url', help='API endpoint URL')
def config(api_url):
    """Configure CLI settings"""
    current_config = load_config()

    if api_url:
        current_config['api_url'] = api_url
        save_config(current_config)
        click.echo(f"API URL set to: {api_url}")
    else:
        click.echo(f"Current API URL: {current_config.get('api_url', 'http://localhost:8000')}")

if __name__ == '__main__':
    cli()
