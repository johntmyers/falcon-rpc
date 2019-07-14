from setuptools import setup, find_packages


setup(
    name='falcon-rpc',
    version='0.4.0',
    description='RPC API based on the Falcon Framework',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=['falcon==2.0.0', 'falcon_cors']
)
