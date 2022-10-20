from distutils.core import setup
from setuptools import setup

setup(
    name='gamejam',
    version='0.1',
    author='Charles Henden',
    author_email='charles@henden.com.au',
    packages=['gamejam'],
    url='http://pypi.python.org/pypi/gamejam/',
    license='LICENSE.txt',
    description='An OpenGL game jamming framework',
    long_description=open('README.md').read(),
    install_requires=[
        "freetype_py",
        "glfw",
        "numpy",
        "PyOpenGL",
        "pytest",
        "setuptools",
    ],
)