# -*- coding: utf-8 -*-
from setuptools import setup

modules = \
['mcpy']
install_requires = \
['base36>=0.1.1,<0.2.0',
 'nbtlib>=2.0.4,<3.0.0',
 'pyglet>=2.0.16,<3.0.0',
 'pyglm>=2.7.1,<3.0.0']

setup_kwargs = {
    'name': 'mcpy',
    'version': '0.13.0',
    'description': 'Minecraft clone written in Python',
    'long_description': '',
    'author': 'obiwac',
    'author_email': 'None',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'py_modules': modules,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}
from build import *
build(setup_kwargs)

setup(**setup_kwargs)
