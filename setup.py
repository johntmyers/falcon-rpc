from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='falcon-rpc',
    version='0.5.0',
    description='RPC API based on the Falcon Framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=['falcon==2.0.0', 'falcon_cors']
)
