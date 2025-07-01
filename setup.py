from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in supportdesk/__init__.py
from supportdesk import __version__ as version

setup(
	name="supportdesk",
	version=version,
	description="Your guide to unlocking full potential of ERPNext",
	author="Bizmap Technologies Pvt. Ltd.",
	author_email="",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
