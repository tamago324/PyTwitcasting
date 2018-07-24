import setuptools
import os

here = os.path.abspath(os.path.dirname(__file__))

with open('README.md') as f:
    long_description = f.read()

about = {}

with open(os.path.join(here, 'pytwitcasting', '__version__.py')) as f:
    exec(f.read(), about)

setuptools.setup(
    name='pytwitcasting',
    version=about['__version__'],
    author='tamago324',
    author_email='tamago324.tky@gmail.com',
    description='TwitcastingのAPI2(β)のライブラリ',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/tamago324/PyTwitcasting',
    packages=setuptools.find_packages(),
    install_requires=['requests>=2.0.1,<3.0.0'],
    python_requires='!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*'
)
