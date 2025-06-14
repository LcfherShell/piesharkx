from setuptools import setup, find_packages
import os

# Membaca file README untuk long description
def read_readme():
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    return ""

setup(
    name="piesharkx",
    version="0.1.0",
    author="LcfherShell",
    author_email="lcfhershell@tutanota.com",
    description="Mini Framework for Human.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/LcfherShell/piesharkxs",
    project_urls={
        "Bug Tracker": "https://github.com/LcfherShell/piesharkx/issues",
        "Documentation": "https://github.com/LcfherShell/piesharkx#readme",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    package_dir={"": "app"}, 
    packages=find_packages(where="app"),
    python_requires=">=3.8",
    install_requires=[
        "webob>=1.8.7",
        "parse>=1.19.0",
        "colorama>=0.4.4",
        "Werkzeug>=2.0.0",
        "pycryptodome>=3.18.0",
        "beautifulsoup4>=4.12.0",
        "chardet>=5.1.0",
        "requests-html"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "piesharkx=app.piesharkx.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="web, framework, pieshark",
    license="MIT",
)