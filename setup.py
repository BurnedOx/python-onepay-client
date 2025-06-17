from setuptools import setup, find_packages

setup(
    name="onepay_client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    author="Mainak Debnath",
    author_email="mainak.debnath@icloud.com",
    description="Python client for OnePay API",
    url="https://github.com/BurnedOx/nest-tcp.git",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
