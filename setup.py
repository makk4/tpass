from setuptools import setup, find_packages

setup(
    name='tpass',
    version='0.1.3',
    author='Manuel Klapapcher',
    author_email='manuel.kl900@gmail.com',
    description='cli password manager',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/makk4/tpass',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
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
    test_suite='nose.collector',
)