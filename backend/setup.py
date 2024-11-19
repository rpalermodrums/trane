from setuptools import setup, find_packages

setup(
    name='transcribe-cli',
    version='0.1.0',
    packages=find_packages(include=['cli', 'cli.*']),
    include_package_data=True,
    install_requires=[
        'Click',
        'requests',
        'PyJWT',
    ],
    entry_points={
        'console_scripts': [
            'transcribe=cli.transcribe_cli:cli',
        ],
    },
) 