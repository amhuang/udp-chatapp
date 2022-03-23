from setuptools import setup

setup(
    name='chatapp',
    py_modules=['chatapp'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'chatapp = chatapp:cli',
        ],
    },
)