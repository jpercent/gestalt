
from setuptools import setup

packages = ['jestalt']

package_data = {
    '.' : ['README.md', '.gitignore', 'setup.cfg', 'LICENSE.txt']
}

setup(name='jestalt',
      version='0.1.0',
      packages=packages,
      package_data=package_data,
      author='James Percent',
      author_email='jpercent@shift5.net')
