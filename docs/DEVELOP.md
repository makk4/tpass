#### depencies
```
python -m pip install --upgrade pip setuptools wheel
```
#### pull from git
update
```
git pull --recurse-submodules
```

#### unittests
depencies
```
sudo apt-get install scons libsdl2-dev libsdl2-image-dev
```
download emulator
```
git clone --recursive https://github.com/trezor/trezor-firmware.git
cd trezor-firmware/core
make vendor
./build-docker.sh
```
update
```
git pull --recurse-submodules
```
#### upload to pypi
```
rm -r dist/
python3 setup.py sdist bdist_wheel
twine check dist/*
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```