from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in notibell/__init__.py
from notibell import __version__ as version

setup(
	name="notibell",
	version=version,
	description="This app will add features through mobile App NotiBell with Push Notifications, Entry Approval-Rejection, applying aand ",
	author="NestorBird",
	author_email="info@nestorbird.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
