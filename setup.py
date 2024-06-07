from setuptools import setup, find_packages
import os

# get the cwd where the setup.py file is located
file_path = os.path.dirname(os.path.realpath(__file__))

long_description = ""
with open(os.path.join(file_path, "README.md"), "r") as fh:
    long_description = fh.read()
    long_description = long_description.split("\n")
    long_description = [line for line in long_description if not "<img" in line]
    long_description = "\n".join(long_description)

with open(os.path.join(file_path, "version.txt"), "r") as fh:
    version_content = fh.read()
    version = version_content.split("\n")[0].strip()

with open(os.path.join(file_path, "requirements.txt"), "r") as fh:
    install_requires = fh.read()
    install_requires = install_requires.split("\n")
    install_requires = [
        line.split("=")[0].split(">")[0].split("<")[0] for line in install_requires
    ]

setup(
    name="distributaur",
    version=version,
    description="Simple task manager and job queue for distributed rendering. Built on celery and redis.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RaccoonResearch/distributaur",
    author="Raccoon Research",
    author_email="shawmakesmagic@gmail.com",
    license="MIT",
    packages=find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
