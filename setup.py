from setuptools import setup, find_packages

setup(
    name='tpass',
    version='0.1.8',
    author='makk4',
    author_email='manuel.kl900@gmail.com',
    description='cli password manager for trezor',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/makk4/tpass',
    packages=find_packages(),
    include_package_data=True,
    licence='GNU LGPL',
    keywords='trezor password',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'click',
        'trezor',
        'cryptography',
        'pyperclip',
        'simplejson',
    ],
    entry_points={
        'console_scripts': ['tpass=src.main:cli'],
    },
    data_files=[('man/tpass1', ['/docs/tpass.1/'])],
    test_suite='nose.collector',
)