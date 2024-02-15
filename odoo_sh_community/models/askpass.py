#!/usr/bin/env python3
#
# Short & sweet script for use with git clone and fetch credentials.
# Requires REPO_USERNAME and REPO_PASSWORD environment variables,
# intended to be called by Git via GIT_ASKPASS.
#

from os import environ
from sys import argv

if 'username' in argv[1].lower():
    print(environ['REPO_USERNAME'])
    exit()

if 'password' in argv[1].lower():
    print(environ['REPO_PASSWORD'])
    exit()

exit(1)
