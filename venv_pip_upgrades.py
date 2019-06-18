
import sys, os
import platform
from subprocess import call

with open('requirements.txt', 'r') as file:
    requirements = file.read().split("\n")
    file.close()

# Let's pul out the packages in the requirements file to upgrade
if isinstance(requirements, list):
    packages = [p.split('==')[0] for p in requirements]
elif isinstance(requirements, str):
    packages = [requirements.split('==')[0]]

if platform.platform().lower().find('windows') >= 0:
    venv_cmd = os.path.join(os.getcwd(), "venv\\Scripts\\activate")
elif platform.platform().lower().find('linux') >= 0:
    venv_cmd = "source {}".format(os.path.join(os.getcwd(), "venv/bin/activate"))

pip_cmd = "pip install --upgrade --no-cache-dir " + ' '.join(packages)
lib_frz_cmd = "pip freeze > requirements.txt"
call("{} && {} && {}".format(venv_cmd, pip_cmd, lib_frz_cmd), shell=True, stdout=sys.stdout)

with open('requirements.txt', 'r') as file:
    requirements = file.read().split("\n")
    file.close()

# Recreated the requirements file but that will have a lot more extr packages that were installed from
# parent packages. The requirement file should match the original with the new version number

# Let's pull out the packages in the requirements file to upgrade
if isinstance(requirements, list):
    new_packages = [p for p in requirements]
elif isinstance(requirements, str):
    new_packages = [requirements]


out_packages = []
for package in new_packages:
    if package:
        name, version = package.split("==")
        if name in packages:
            out_packages.append(package)

with open('requirements.txt', 'w') as file:
    file.writelines(out_packages)
    file.close
