from distutils.core import setup
from setuptools import setup

setup(
    name='gamejam',
    version='0.1',
    author='Charles Henden',
    author_email='charles@henden.com.au',
    packages=['gamejam'],
    scripts=['bin/script1','bin/script2'],
    url='http://pypi.python.org/pypi/gamejam/',
    license='LICENSE.txt',
    description='An OpenGL game jamming framework',
    long_description=open('README.txt').read(),
    install_requires=[
        "freetype_py",
        "glfw",
        "numpy",
        "PyOpenGL",
        "pytest",
        "setuptools",
    ],
)