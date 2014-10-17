
from setuptools import setup, find_packages

def read(filename):
    with open(filename) as fp:
        return fp.read()

long_description = read('README.md')

setup(
    name='nr.strex',
    version='1.0.0',
    description='string processing',
    long_description=long_description,
    author='Niklas Rosenstein',
    author_email='rosensteinniklas@gmail.com',
    url='https://github.com/nr-libs/py-nr.strex',
    install_requires=[
        'setuptools',
        ],
    py_modules=['nr.strex'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['nr'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    license="MIT License",
    )
