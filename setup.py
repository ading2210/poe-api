import setuptools, glob
from pathlib import Path

#note: build this package with the following command:
#pip wheel --no-deps -w dist .

base_path = Path(__file__).parent
long_description = (base_path / "README.md").read_text()

setuptools.setup(
  name="poe-api",
  version="0.4.13",
  author="ading2210",
  license="GPLv3",
  description="A reverse engineered API wrapper for Quora's Poe",
  long_description=long_description,
  long_description_content_type="text/markdown",
  packages=["poe_graphql"],
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Operating System :: OS Independent"
  ],
  python_requires=">=3.7",
  package_dir={
    "": "poe-api/src"
  },
  package_data={
    "poe_graphql": ["*.graphql"]
  },
  py_modules=["poe"],
  include_package_data=True,
  install_requires=[
    "websocket-client",
    "requests[socks]",
    "python-socks",
    "tls_client",
    "quickjs"
  ],
  url="https://github.com/ading2210/poe-api"
)