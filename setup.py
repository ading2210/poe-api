import setuptools
from pathlib import Path

base_path = Path(__file__).parent
long_description = (base_path / "README.md").read_text()

setuptools.setup(
  name="poe-api",
  version="0.0.1",
  author="ading2210",
  description="A reverse engineered API wrapper for Quora's Poe",
  long_description=long_description,
  long_description_content_type="text/markdown",
  packages=setuptools.find_packages(),
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Operating System :: OS Independent"
  ],
  python_requires=">=3.7",
  py_modules=["poe"],
  package_dir={"": "poe-api/src"},
  install_requires=["websocket-client"],
  url="https://github.com/ading2210/poe-api"
)