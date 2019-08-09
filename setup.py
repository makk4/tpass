from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='tpass',
    version='0.1.1',
    author="Manuel Klapapcher",
    author_email="manuel.kl900@gmail.com",
    description="cli password manager",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/makk4/tpass",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'click',
        'trezor',
        'cryptography',
        'pyperclip',
        'pyotp',
    ],
    entry_points={
        'console_scripts': ['tpass=src.main:cli'],
    },
    test_suite='nose.collector',
)