# setup.py
from setuptools import setup, find_packages

setup(
    name="feishu-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Flask==2.1.0",
        "requests==2.27.1",
    ],
    entry_points={
        "console_scripts": [
            "feishu-bot=feishu_bot.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A Feishu bot that responds to group and private messages",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/feishu-bot",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)