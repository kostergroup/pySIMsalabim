import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pySIMsalabim", # Replace with your own username
    version="v1.02",
    author="Vincent M. Le Corre, Sander Heester, L. Jan Anton Koster",
    author_email="",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GPLv3',
    url="https://github.com/kostergroup/pySIMsalabim",
    download_url="https://github.com/kostergroup/pySIMsalabim/v1.02.tar.gz",
    packages=setuptools.find_packages(),
    readme = "README.md",
    keywords=['Drift-diffusion', 'semiconductor', 'solar cells'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    python_requires='>=3.12',
    install_requires = [
        'numpy>=1.2, <=2.0',
        'pandas>=1.4',
        'matplotlib>=3.5',
        'jupyterlab>=3.4',
        'seaborn>=0.11',
        'scipy>=1.0',
        'gitpython>=3.1',
        'openpyxl>=3.0',
    ],
    extras_require = {
        'dev': [
            'pytest',
            'twine',
        ],
    },
    include_package_data=True,
        
)