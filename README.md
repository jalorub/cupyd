# DATA ETL

Framework to easily create ETL processes.

Key features:

- Simple, flexible syntax.
- ETLs that will run on multiple workers without the need of writing multiprocessing code.
- High compatibility:
    - Works in Unix, Windows & MacOS.
    - Python >= 3.9
- Light: no dependencies required for its core version.
    - The API version will require [Falcon](https://falcon.readthedocs.io/en/stable/index.html),
      which is a minimalist ASGI/WSGI framework that doesn't require other packages to work.
    - The Dashboard version (full version) will require Falcon and [Dash](https://dash.plotly.com/).
