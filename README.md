# homelypy
A thin wrapper for the Homely alarm company API

# Data dump
This can be used to easily extract a data dump from the API. Simply clone the repository or install from pypi (pip install homelypy) and run
```shell
python3 -m homelypy.homely <username>
```
You will be prompted for a password, then it will dump all the locations and associated sensors in the system. It is gathered inappropriate location_<location_name>.json for convenience.

# Building and packaging
```shell
rm -R dist
python3 -m build
python3 -m twine upload dist/* --verbose
```