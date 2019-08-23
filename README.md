# tpass - Trezor Password Manager CLI Interface

Simple Trezor Password Manager interface for command line, inspired by pass.

Untested Beta Software! - Do not use it

## Table of contents
* [Install](#Install)
* [Usage](#Usage)
* [Features](#Features)
* [Contribute](#Contribute)
* [Docs](#Docs)
* [Releases](#Releases)

## **Install**

```
pip3 install --user -i https://test.pypi.org/simple/ tpass
```
or manual with git
```
git clone git@github:makk4/tpass.git
python3 setup.py install --user
```
### **Tab autocompletion**
#### **Bash**
```
_TPASS_COMPLETE=source tpass > tpass-complete.sh
```
and add this to your **.bashrc**
```
. /path/to/tpass-complete.sh
```
#### **zsh**
```
_TPASS_COMPLETE=source_zsh tpass > tpass-complete.sh
```
and add this to your **.zshrc**
```
. /path/to/tpass-complete.sh
```
#### **oh-my-zsh**
```
_TPASS_COMPLETE=source_zsh tpass > ~/.oh-my-zsh/plugins/tpass/tpass-complete.sh
```
and add this to your **.zshrc**
```
.  ~/.oh-my-zsh/plugins/tpass/tpass-complete.sh
```
## **Usage**

Read the [docs](https://makk4.github.io/tpass/manual) section for more 
information.

```
Options:

--debug    Show debug info
--version  Show the version and exit.
--help     Show this message and exit.

Commands:

clip      Decrypt and copy line of entry to clipboard
config    Configuration settings
edit      Edit entry or tag
export    Export data base
find      List names of passwords and tags that match names
generate  Generate new password
git       Call git commands on db storage
grep      Search for pattern in decrypted entries
import    Import data base
init      Initialize new password storage
insert    Insert entry or tag
lock      Remove Plain Metadata file from disk
list      List names of passwords from tag
remove    Remove entry or tag. 
show      Decrypt and print an entry
unlock    Unlock Storage and writes plain metadata to disk
```
## **Features**

- Trezor Password Manager Compatible
- Supports Trezor One and Trezor Model T
- Cross plattform. Windows, Linux, MacOS
- Dropbox, Google Drive, Git synchronisation
- Offline usage
- Generate random Passwords and Passphrases
- Use your own Wordlists of choice, default is EFF large
- List, insert, delete, show, edit entries
- Copy passwords to clipboard or show
- Export, import database in JSON, CSV
- Do not store metadata on disk mode
- Combine entropy from device and os.random for all crypto functions
- Bash and zsh auto completion

## **Contribute**

Read the [docs](https://makk4.github.io/tpass/contribute) section for more 
information.

## **Docs**

[tpass guide](https://makk4.github.io/tpass/)

## **Releases**

Read the [changelog](CHANGELOG.md) for information about versions.