# cupyd

[![PyPI - Version](https://img.shields.io/pypi/v/cupyd)](https://pypi.org/project/cupyd/)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fjalorub%2Fcupyd%2Frefs%2Fheads%2Fmain%2Fpyproject.toml&style=flat-square)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jalorub/cupyd/ci.yaml?style=flat-square)](https://github.com/jalorub/cupyd/actions/workflows/ci.yaml?query=branch%3Amain++)
[![Coverage Status](https://coveralls.io/repos/github/jalorub/cupyd/badge.svg)](https://coveralls.io/github/jalorub/cupyd)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/cupyd?style=flat-square)](https://pypistats.org/packages/cupyd)

                                                      __     
                                                     /\ \    
      ___       __  __      _____       __  __       \_\ \   
     /'___\    /\ \/\ \    /\ '__`\    /\ \/\ \      /'_` \  
    /\ \__/    \ \ \_\ \   \ \ \L\ \   \ \ \_\ \    /\ \L\ \ 
    \ \____\    \ \____/    \ \ ,__/    \/`____ \   \ \___,_\
     \/____/     \/___/      \ \ \/      `/___/> \   \/__,_ /
                              \ \_\         /\___/           
                               \/_/         \/__/

Python framework to create your own ETLs.

## Features

- Simple but powerful syntax.
- Modular approach that encourages re-using components across different ETLs.
- Parallelism out-of-the-box without the need of writing multiprocessing code.
- Very compatible:
    - Runs on Unix, Windows & MacOS.
    - Python >= 3.9
- Lightweight:
    - No dependencies for its core version.
    - [WIP] API version will require [Falcon](https://falcon.readthedocs.io/en/stable/index.html),
      which is a minimalist ASGI/WSGI framework that doesn't require other packages to work.
    - [WIP] The Dashboard (full) version will require Falcon and [Dash](https://dash.plotly.com/).
