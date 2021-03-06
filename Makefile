TEST_PATH=./test

clean-pyc:
    find . -name '*.pyc' -exec rm --force {} +
    find . -name '*.pyo' -exec rm --force {} +
    name '*~' -exec rm --force  {} 

clean-build:
    rm --force --recursive build/
    rm --force --recursive dist/
    rm --force --recursive *.egg-info

test: clean-pyc
    py.test --verbose --color=yes $(TEST_PATH)

install:
    source env/bin/activate
    pip3 install --editable .
    eval "$(_TPASS_COMPLETE=source_zsh tpass)"
