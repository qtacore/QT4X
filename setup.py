# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
# 
# https://opensource.org/licenses/BSD-3-Clause
# 
# Unless required by applicable law or agreed to in writing, software distributed 
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#

import os
from setuptools import setup, find_packages

BASE_DIR = os.path.realpath(os.path.dirname(__file__))

def generate_version():
    version = "1.0.0"
    if os.path.isfile(os.path.join(BASE_DIR, "version.txt")):
        with open("version.txt", "r") as fd:
            content = fd.read().strip()
            if content:
                version = content
    return version
  
def parse_requirements(exclude=["test"]):
    reqs = []
    if os.path.isfile(os.path.join(BASE_DIR, "requirements.txt")):
        with open(os.path.join(BASE_DIR, "requirements.txt"), 'r') as fd:
            for line in fd.readlines():
                line = line.strip()
                if line:
                    reqs.append(line)
    return reqs

if __name__ == "__main__":

    setup(
      version=generate_version(),
      name="qt4x",
      cmdclass={},
      packages=find_packages(),
      include_package_data=True,
      package_data={'':['*.txt', '*.TXT']},
      author="Tencent",
      license="Copyright(c)2010-2018 Tencent All Rights Reserved. ",
      install_requires=parse_requirements()
      )
