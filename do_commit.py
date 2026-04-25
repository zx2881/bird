# -*- coding: utf-8 -*-
import subprocess

subprocess.run(['git', 'config', 'core.autocrlf', 'true'], cwd=r'D:\bird\bird')

result = subprocess.run(
    ['git', 'commit', '-m', 'Update bird coordinates'],
    cwd=r'D:\bird\bird',
    capture_output=True,
    text=True,
    shell=True
)
print(result.stdout)
print(result.stderr)