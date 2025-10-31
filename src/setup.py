#!/usr/bin/python3

# Author: Dan Walsh <dwalsh@redhat.com>
from setuptools import setup


setup(name="setroubleshoot",
      version="3.3.33",
      description="Python SELinux Troubleshooter",
      author="Dan Walsh", author_email="dwalsh@redhat.com",
      url='https://gitlab.com/setroubleshoot/setroubleshoot/',
      download_url='https://gitlab.com/setroubleshoot/setroubleshoot/-/releases/',
      license='GPLv3+',
      platforms='posix',
      keywords=['selinux', 'setroubleshoot'],
      packages=["setroubleshoot"])
