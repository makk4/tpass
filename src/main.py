#!/usr/bin/env python3
from src import trezor as trezorapi
from src import crypto as cryptomodul
import click
import os
import subprocess
import sys
import json
import tempfile
import pyperclip
import time
import pyotp
import re

ICONS = {'home': {'emoji': '🏠'}, 'person-stalker': {'emoji': '👩‍👩‍👦'}, 'social-bitcoin': {'emoji': '₿'}, 'person': {'emoji': '😀'}, 'star': {'emoji': '⭐'}, 'flag': {'emoji': '🏳️'}, 'heart':{'emoji':'❤'}, 'settings': {'emoji':'⚙️'}, 'email':{'emoji':'✉️'},'cloud': {'emoji': '☁️'}, 'alert-circled': {'emoji':'⚠️'}, 'android-cart': {'emoji': '🛒'}, 'image': {'emoji': '🖼️'}, 'card': {'emoji': '💳'}, 'earth': {'emoji': '🌐'}, 'wifi': {'emoji': '📶'}}
DROPBOX_PATH = os.path.join(os.path.expanduser('~'), 'Dropbox', 'Apps', 'TREZOR Password Manager')
GOOGLE_DRIVE_PATH = os.path.join(os.path.expanduser('~'), 'Google Drive', 'Apps', 'TREZOR Password Manager')
GIT_PATH = os.path.join(os.path.expanduser('~'), '.tpassword-store')
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
WORDLIST = os.path.join(CONFIG_PATH, 'wordlist.txt')
TMP = os.path.join(tempfile.gettempdir())
DEV_SHM = os.path.join('/', 'dev', 'shm')
CLIPBOARD_CLEAR_TIME = 15

newEntry = {'title': '', 'username': '', 'password': {'type': 'String', 'data': ''}, 'nonce': '', 'tags': [], 'safe_note': {'type': 'String', 'data': ''}, 'note': '', 'success': True, 'export': True}
entries = {}
tags = {'0': {'title': 'All', 'icon': 'home'}, }
db_json = {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': tags, 'entries': entries}
config = {'file_name': '', 'store_path': DROPBOX_PATH, 'cloud_provider': 'dropbox', 'pinentry': False, 'clipboardClearTimeSec': CLIPBOARD_CLEAR_TIME, 'storeMetaDataOnDisk': True}
client = None

'''
Core Methods
'''
def loadConfig():
    global config
    if not os.path.isfile(CONFIG_FILE):
        writeConfig()
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    if 'file_name' not in config or 'store_path' not in config or 'pinentry' not in config:
        click.echo('config error: ' + CONFIG_PATH)
        sys.exit(-1)
    return 0

def writeConfig():
    if not os.path.exists(CONFIG_PATH):    
        os.mkdir(CONFIG_PATH)
    with open(CONFIG_FILE, 'w', encoding='utf8') as f:
        json.dump(config, f, indent=4)
 
def unlockStorage():
    global db_json
    global entries
    global tags
    db_file = os.path.join(config['store_path'], config['file_name'])

    if config['file_name'] == '' or not os.path.isfile(db_file):
        sys.exit(-1)
    tmp_path = DEV_SHM
    tmp_file = os.path.join(tmp_path, config['file_name'] + '.json')

    if not os.path.exists(DEV_SHM):
        click.echo('warning: /dev/shm not found on host, using not as secure /tmp/ for plain metadata')
        tmp_file = os.path.join(TMP, config['file_name'] + '.json')
    cond_old_tmp_file = not os.path.isfile(tmp_file) or (os.path.isfile(tmp_file) and (os.path.getmtime(tmp_file) < os.path.getmtime(db_file)))
    cond_not_saving = config['storeMetaDataOnDisk'] is False
    if cond_not_saving or cond_old_tmp_file:
        try:
            getClient()
            keys = trezorapi.getTrezorKeys(client)
        except:
            raise Exception('Error while getting keys from device')
        config['file_name'] = keys[0]

        db_file = os.path.join(config['store_path'], config['file_name'])
        try:
            db_json = cryptomodul.decryptStorage(db_file, keys)
        except:
            raise Exception('Error while decrypting storage')
        entries = db_json['entries']
        tags = db_json['tags']

        if config['storeMetaDataOnDisk'] is True:
            with open(tmp_file, 'w') as f:  
                json.dump(db_json, f)

    if config['storeMetaDataOnDisk'] is True:
        with open(tmp_file) as f:
            db_json = json.load(f)
            entries = db_json['entries']
            tags = db_json['tags']


def saveStorage():
    global config
    tmp_file = DEV_SHM

    getClient()
    
    if not os.path.exists(DEV_SHM):
        tmp_file = TMP
    try:
        keys = trezorapi.getTrezorKeys(client)
    except:
        raise Exception('Error while accessing trezor device')
        
    fileName = keys[0]
    tmp_file = os.path.join(tmp_file, fileName + '.json')
    config['file_name'] = fileName
    db_file = os.path.join(config['store_path'], config['file_name'])

    try:
        cryptomodul.encryptStorage(db_json, db_file, keys)
    except:
        raise Exception('Error while encrypting storage')

    if config['storeMetaDataOnDisk'] is True and os.path.isfile(db_file):
        with open(tmp_file, 'w') as f:
            json.dump(db_json, f)
    
    if config['cloud_provider'] == 'git':
        subprocess.call('git commit -m "update db"', cwd=config['store_path'], shell=True)
        subprocess.call('git add *.pswd', cwd=config['store_path'], shell=True)

    return True

def clearClipboard():
    with click.progressbar(length=CLIPBOARD_CLEAR_TIME, label='Clipboard will clear', show_percent=False, fill_char='=', empty_char=' ') as bar:
        for i in bar:
            time.sleep(1)
    pyperclip.copy('')

def getClient():
    global client
    pinentry = False
    if config['pinentry'] == 'true':
        pinentry = True
    if client is None:
        try:
            client = trezorapi.getTrezorClient()
        except:
            raise Exception('Error while accessing trezor device')

def parseName(input_str):
    tag = ''; titleOrNote = ''; username = ''
    if '/' in input_str:
        tag = input_str.split('/')[0]
        titleOrNote = input_str.split('/')[1]
    if ':' in input_str:
        titleOrNote = input_str.split('/')[1].split(':')[0]
        username = input_str.split(':')[1]
    return tag, titleOrNote, username

def getEntry(titleOrNote,username=None):
    for e in entries:
        if titleOrNote.lower() == entries[e]['title'].lower() or titleOrNote.lower() == entries[e]['note'].lower():
            if username.lower() == entries[e]['username'].lower() or username is None:
                return str(e), entries[e]
    return None, None

def getTag(tag_name):
    tag_name = tag_name.split('/')[0]
    for t in tags:
        if tag_name.lower() == tags[t]['title'].lower():
            return str(t), tags[t]
    return None, None

def saveTag(tag, tag_id=None):
    global db_json
    if tag_id is None:
        for t in tags:
            tag_id = str(int(t) + 1)
    if tag:
        db_json['tags'].update( {tag_id : tag} )
    else:
        click.echo('Error detected, aborted')

def getEntriesByTag(tag_id):
    es = {}
    for e in entries:
        ts = entries[e]['tags']
        if tag_id == '0' and ts == []:
            es[e] = entries[e]
        else:
            for t in ts:
                if t == int(tag_id):
                    es[e] = entries[e]        
    return es

def printEntries(es):
    for e in es:
        click.echo(es[e]['title'] + ':' + es[e]['username'])

def printTags(ts, includeEntries=False):
    tag_str = ''
    for t in ts:
        tag_id = t
        t = tags.get(tag_id)
        icon = '# '
        icon = ICONS.get(t['icon'])['emoji']
        click.echo(icon + '  ' + t['title'] + '/')
        if includeEntries:
            es = getEntriesByTag(tag_id)
            click.echo('----------')
            printEntries(es)
            click.echo('----------')

def tagsToString(ts, includeIds=False):
    tags_str = ''
    for t in ts:
        tag = ts.get(t)
        i = ICONS.get(tag['icon'])['emoji']
        if not i:
            i = '# '
        if includeIds:
            tags_str = tags_str + t + ': ' + i + '  ' + tag['title'] + '     '
        else:
            tags_str = tags_str + i + '  ' + tag['title'] + '  '
    return tags_str

def iconsToString():
    icon_str = ''
    for i in ICONS:
        icon_str = icon_str + i + ':' + ICONS.get(i)['emoji'] + ', '
    return icon_str

def unlockEntry(e):
    if e is None or e['success'] is False or e['export'] is True:
        return None
    e['success'] = False
    e['export'] = True
    try:   
        getClient()
        keys = trezorapi.getTrezorKeys(client)
        plain_nonce = trezorapi.getDecryptedNonce(client, e)
    except:
        raise Exception('Error while accessing trezor device')    
    try:
        e['password']['data'] = cryptomodul.decryptEntryValue(plain_nonce, e['password']['data'])
        e['password']['type'] = 'String'
        e['safe_note']['data'] = cryptomodul.decryptEntryValue(plain_nonce, e['safe_note']['data'])
        e['safe_note']['type'] = 'String'
    except:
        raise Exception('Error while decrypting entry')
    e['success'] = True
    return e

def lockEntry(e): 
    if e is None or e['success'] is False or e['export'] is False:
        return None
    e['success'] = False
    e['export'] = False
    try:
        getClient()
        keys = trezorapi.getTrezorKeys(client)
        e['nonce'] = trezorapi.getEncryptedNonce(client, e)
        plain_nonce = trezorapi.getDecryptedNonce(client, e)
    except:
        raise Exception('Error while accessing trezor device')
    try:
        e['password']['data'] = cryptomodul.encryptEntryValue(json.dumps(e['password']['data']), plain_nonce)
        e['password']['type'] = 'Buffer'
        e['safe_note']['data'] = cryptomodul.encryptEntryValue(json.dumps(e['safe_note']['data']), plain_nonce)
        e['safe_note']['type'] = 'Buffer'
    except:
        raise Exception('Error while decrypting entry')
    e['success'] = True
    return e

def insertEntry(entry, entry_id=None):
    global db_json
    global entries

    if not entry_id:
        for e in entries:
            entry_id = str(int(e) + 1)
            print(entry_id)
    if entry and entry['success'] is True and entry['export'] is False:
        entries.update( {entry_id : entry} )
        print(db_json['entries'][entry_id])
        return True
    else:
        raise Exception('Error detected while inserting Entry, aborted')

def editEntry(e):
    if e['export'] is False:
        e = unlockEntry(e)
    if e['success'] is False:
        return None
    e['success'] = False
    edit_json = {'item/url*':e['note'], 'title':e['title'], 'username':e['username'], 'password':e['password']['data'], 'secret':e['safe_note']['data'], 'tags':e['tags']}
    edit_json = click.edit(json.dumps(edit_json, indent=4), require_save=True, extension='.json')
    if edit_json:
        try:
            edit_json = json.loads(edit_json)
        except:
            raise IOError('edit gone wrong')
        e['title'] = edit_json['title']
        e['note'] = edit_json['item/url*']
        e['username'] = edit_json['username']
        e['password']['data'] = edit_json['password']
        e['safe_note']['data'] = edit_json['secret']
        e['tags'] = edit_json['tags']
        e['success'] = True
        e['export'] = True
        return lockEntry(e)
    e['success'] = True
    return None

def editTag(t):
    edited_json = click.edit(json.dumps(t, indent=4), require_save=True)
    if edited_json:
        try:
            edited_json = json.loads(edited_json)
        except:
            raise IOError('edit gone wrong')
        t['title'] = edited_json['title']
        t['icon'] = edited_json['icon']
        return t
    else:
        return None

# TODO print icons; get only from All if nothing else, call All=''
def tabCompletionEntries(ctx, args, incomplete):
    loadConfig()
    unlockStorage()
    tabs = []
    for t in tags:
        selEntries = getEntriesByTag(t)
        for e in selEntries:
            tabs.append(tags[t]['title'].lower() + '/' + selEntries[e]['note'].lower() + ':' + selEntries[e]['username'])
    return [k for k in tabs if incomplete.lower() in k]

# TODO print icons
def tabCompletionTags(ctx, args, incomplete):
    loadConfig()
    unlockStorage()
    tabs = []
    for t in tags:
        tabs.append(tags[t]['title'].lower() + '/')
    return [k for k in tabs if incomplete.lower() in k]

def tabCompletionConfig(ctx, args, incomplete):
    loadConfig()
    return [k for k in config if incomplete.lower() in k]
'''
CLI Methods
'''

@click.group()
@click.version_option()
def cli():
    '''
    ~+~#~+~~+~#~+~~+~#~+~~+~#~+~~+~#~+~\n
            tpass\n
    +~#~+~~+~#~+~~+~#~+~~+~#~+~~+~#~+~~\n

    CLI for Trezor Password Manager inspired by pass\n
    Untested Beta Software! - Do not use it\n
        
    @author: makk4 <manuel.kl900@gmail.com>\n
    version: 0.1.0\n
    https://github.com/makk4/tpass
    '''

    loadConfig()
    pass

@cli.command()
@click.option('-p', '--path', default=DROPBOX_PATH, type=click.Path(), help='path to database')
@click.option('-c', '--cloud', default='dropbox', type=click.Choice(['dropbox', 'googledrive', 'git']), help='cloud provider: <dropbox> <googledrive> <git>')
@click.option('-a', '--pinentry', is_flag=True, help='ask for password on device')
def init(path, cloud, pinentry):
    '''Initialize new password storage'''
    global config
    if not os.path.exists(path):    
        os.makedirs(path)
    if len(os.listdir(path)) != 0:
        click.echo(path + ' is not empty, not initialized')
        exit(-1)
    config['file_name'] = 'init'; config['store_path'] = path; config['cloud_provider'] = cloud; config['pinentry'] = pinentry
    if cloud == 'git':
        subprocess.call('init', cwd=config['store_path'], shell=True)
        click.echo('password store initialized with git in ' + path)
    saveStorage()
    writeConfig()
    click.echo('password store initialized in ' + path)
    exit(0)

@cli.command()
@click.argument('name', type=click.STRING, nargs=1)
def find(name):# TODO alias
    '''List names of passwords and tags that match names'''
    unlockStorage()
    es = {}; ts = {}
    for e in entries:
        e = entries[e] # TODO
        if name.lower() in e['title'].lower() or name.lower() in e['note'].lower() or name.lower() in e['username'].lower():
            es[str(e)] = e
    for t in tags:
        if name.lower() in tags[t]['title'].lower():
            ts[str(t)] = tags[t]
    printEntries(es)
    printTags(ts)
    sys.exit(0)

@cli.command()
def grep(name):
    '''Search for pattern in decrypted entries'''
    unlockStorage()
    for e in entries:
        e = unlockEntry(entries[e])
        if name.lower() in e['title'].lower():
            click.echo(click.style('[' + e['title'] + ']//field: <title>//: ', bold=True) + e['title'].lower())
        elif name.lower() in e['note'].lower():
            click.echo(click.style('[' + e['note'] + ']//field: <note>//: ', bold=True) + e['note'].lower())
        elif name.lower() in e['username'].lower():
            click.echo(click.style('[' + e['username'] + ']//field: <username>//: ', bold=True) + e['username'].lower())
        elif name.lower() in e['password']['data'].lower():
            click.echo(click.style('[' + e['password']['data'] + ']//field: <password>//: ', bold=True) + e['password']['data'].lower())
        elif name.lower() in e['safe_note']['data'].lower():
            click.echo(click.style('[' + e['safe_note']['data'] + ']//field: <titsafe_notele>//: ', bold=True) + e['safe_note']['data'].lower())
    sys.exit(0)

@cli.command()
@click.argument('tag_name', default='', type=click.STRING, nargs=1, autocompletion=tabCompletionTags)
def ls(tag_name):# TODO alias
    '''List names of passwords from tag'''
    unlockStorage()
    ts = {}
    if tag_name == '':
        ts = tags
    else:
        t = getTag(tag_name)
        ts[t[0]] = t[1]

        if t[1] is None:
            return
    printTags(ts, True)
    sys.exit(0)
    
@cli.command()
@click.argument('entry_name', type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
@click.option('-s', '--secrets', is_flag=True, help='show password and secret notes')
@click.option('-j', '--json', is_flag=True, help='json format')
def show(entry_name, secrets, json): # TODO alias
    '''Decrypt and print an entry'''
    unlockStorage()
    entry_name = parseName(entry_name)
    print(entry_name[1] + ' ' + entry_name[2])
    e = getEntry(entry_name[1], entry_name[2])[1]
    print(e)
    if e is None:
        return

    if not secrets:
        pwd = '********'
        safeNote = '********'
    else:
        e = unlockEntry(e)
        pwd = e['password']['data']
        safeNote = e['safe_note']['data']
    if json:
        click.echo(e)
    else:
        ts = {}
        for i in e['tags']:
            ts[i] = tags.get(str(i))

        click.echo('~~+~#~+~~+~#~+~~+~#~+~~+~#~+' + '\n' +
            click.style('\t' + e['note'], bold=True) + '\n' +
            '+~#~+~~+~#~+~~+~#~+~~+~#~+~~' + '\n' +
            click.style('username: ', bold=True) + e['username'] + '\n' +
            click.style('password: ', bold=True) + pwd + '\n' +
            click.style('item/url: ', bold=True) + e['title'] + '\n' +
            click.style('secret:   ', bold=True) + safeNote  + '\n' +
            click.style('tags:     ', bold=True) + tagsToString(ts))
    sys.exit(0)

@cli.command()
@click.option('-u', '--user', is_flag=True, help='copy user')
@click.option('-i', '--url', is_flag=True, help='copy item/url*')
@click.option('-s', '--secret', is_flag=True, help='copy secret')
@click.argument('entry_name', type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
def clip(user, url, secret, entry_name):# TODO alias; TODO open browser
    '''Decrypt and copy line of entry to clipboard'''
    unlockStorage()
    entry_name = parseName(entry_name)
    e = getEntry(entry_name[1], entry_name[2])[1]
    if e is None:
        sys.exit(-1)
    if user:
        pyperclip.copy(e['username'])
    elif url:
        pyperclip.copy(e['title'])
    else:
        secrets = unlockEntry(e)
        if secret:
            pyperclip.copy(secrets[1])
        else:
            pyperclip.copy(secrets[0])
        clearClipboard()
    sys.exit(0)
    
@cli.command()
@click.argument('length', default=15, type=int)
@click.option('-i', '--insert', default=None, type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
@click.option('-c', '--clip', is_flag=True, help='copy to clipboard')
@click.option('-t', '--typeof', default='password', type=click.Choice(['password', 'wordlist', 'pin']), help='type of password')
@click.option('-s', '--seperator', default=' ', type=click.STRING, help='seperator for passphrase')
@click.option('-f', '--force', is_flag=True, help='force without confirmation')
def generate(insert, typeof, clip, seperator, force, length):
    '''Generate new password'''
    unlockStorage()
    global db_json
    if (length < 6 and typeof is 'password') or (length < 3 and typeof is 'wordlist') or (length < 4 and typeof is 'pin'):
        click.echo(length + ' is too short for password with type ' + typeof)
        sys.exit(-1)
    if typeof == 'wordlist': # TODO TXT
        words = {}
        try:
            with open(WORDLIST) as f:
                for line in f.readlines():
                    if re.compile('^([1-6]){5}\t(.)+$').match(line):
                        key, value = line.rstrip('\n').split('\t')
                        if(not key in words):
                            words[key] = value
                        else:
                            sys.exit(-1)
        except:
            click.echo('error while processing wordlist.txt file')
        pwd = cryptomodul.generatePassphrase(length, words, seperator)
    elif typeof == 'pin':
        pwd = cryptomodul.generatePin(length)
    else:
        pwd = cryptomodul.generatePassword(length)

    if insert:

        entry_name = parseName(entry_name)
        e = getEntry(entry_name[1], entry_name[2])
        entry_id = e[0]
        e = e[1]
        if e is None:
            return
        e = unlockEntry(e)
        e['password']['data'] = pwd
        e = lockEntry(e)
        if force or click.confirm('Insert password in entry ' + click.style(entries[entry_id]['title'], bold=True)):
            insertEntry(e, entry_id)
    if clip:
        pyperclip.copy(pwd)
        clearClipboard()
    else:
        click.echo(pwd)
    sys.exit(0)

# TODO make options TRU/FALSE tag and -1 all args
@cli.command()
@click.option('--tag', '-t', type=click.STRING, help='remove tag', nargs=1, autocompletion=tabCompletionTags)
@click.option('--force', '-f', is_flag=True, help='force without confirmation')
@click.argument('entry_name', type=click.STRING, default='', nargs=1, autocompletion=tabCompletionEntries)
def rm(entry_name, tag, force):# TODO alias
    '''Remove entry or tag'''
    unlockStorage()
    global db_json
    if tag:
        tag_id = getTag(tag)[0]
        if not tag_id or tag_id == '0':
            sys.exit(-1)
        if force or click.confirm('Delete tag: ' + click.style(tags[tag_id]['title'], bold=True)):
            del db_json['tags'][tag_id]
            saveStorage()
    else:
        entry_name = parseName(entry_name)
        entry_id = getEntry(entry_name[1], entry_name[2])[0]
        if not entry_id:
            sys.exit(-1)
        if force or click.confirm('Delete entry ' + click.style(entries[entry_id]['title'], bold=True)):
            del db_json['entries'][entry_id]
            saveStorage()
    sys.exit(0)

@cli.command()
@click.argument('tag_name', default='', type=click.STRING, nargs=1, autocompletion=tabCompletionTags)
@click.argument('entry_name', default='', type=click.STRING, nargs=1)
@click.option('--tag', '-t', is_flag=True, help='insert tag')
def insert(tag_name, entry_name, tag):
    '''Insert entry or tag'''
    unlockStorage()
    global db_json
    if tag is True:
        if getTag(tag_name)[1]:
            sys.exit(-1)
        t = {'title': '', 'icon': ''}
        t = editTag(t)
        if t is not None:
            saveTag(t)
            saveStorage()
    else:
        if tag_name != '':
            t = getTag(tag_name)
            if t[1] is None:
                sys.exit(-1)
            tag = [t[0]]
        else:
            tag = []

        e = editEntry(newEntry)
        if e is not None:
            insertEntry(e)
            saveStorage()
    sys.exit(0)

@cli.command()#TODO option --entry/--tag with default
@click.argument('entry_name', type=click.STRING, default='', nargs=1, autocompletion=tabCompletionEntries)
@click.option('-t', '--tag', type=click.STRING, default='', nargs=1, help='edit tag', autocompletion=tabCompletionTags)
def edit(entry_name, tag):
    '''Edit entry or tag'''
    unlockStorage()
    if tag:
        t = getTag(tag)
        tag_id = t[0]
        t = t[1]
        if t is None:
            sys.exit(-1)
        t = editTag(t)
        if t is not None:
            saveTag(t, tag_id)
            saveStorage()
    else:
        entry_name = parseName(entry_name)
        e = getEntry(entry_name[1], entry_name[2])
        entry_id = e[0]
        e = e[1]
        if e is None:
            sys.exit(-1)

        e = editEntry(e)
        if e is not None:
            insertEntry(e, entry_id)
            saveStorage()
    sys.exit(0)

@cli.command()
@click.argument('commands', type=click.STRING, nargs=-1)
def git(commands):
    '''Call git commands on db storage'''
    subprocess.call('git '+ ' '.join(commands), cwd=config['store_path'], shell=True)
    sys.exit(0)

@cli.command()
@click.option('-e','edit', is_flag=True, help='edit config')
@click.option('-r','reset', is_flag=True, help='reset config')
@click.argument('setting_name', type=click.STRING, default='', nargs=1, autocompletion=tabCompletionConfig)
@click.argument('setting_value', type=click.STRING, default='None', nargs=1)
def conf(edit, reset, setting_name, setting_value):
    '''Configuration settings'''
    global config
    if edit:
        click.edit(filename=CONFIG_FILE, require_save=True)
    elif reset:
        if os.path.isfile(CONFIG_FILE):
            os.remove(CONFIG_FILE)
    else:
        writeConfig()
    sys.exit(0)

@cli.command()
@click.option('-f', '--force', is_flag=True, help='omnit dialog')
def unlock(force):
    '''Unlock Storage and writes plain metadata to disk'''
    if force or click.confirm('Unlock storage?'):
        unlock()
    sys.exit(0)

@cli.command()
def lock():
    '''Remove Plain Metadata file from disk'''
    tmp_file = os.path.join(DEV_SHM, config['file_name'] + '.json')
    if not os.path.exists(DEV_SHM):
        tmp_file = os.path.join(TMP, config['file_name'] + '.json')
    if os.path.isfile(tmp_file):
        os.remove(tmp_file)
        click.echo(click.style('metadata deleted: ', bold=True) + tmp_file)
    else:
        click.echo(click.style('nothing to delete', bold=True)) 
    sys.exit(0)

# TODO CSV
@click.argument('tag_name', default='all', type=click.STRING, nargs=1, autocompletion=tabCompletionTags)
@click.argument('entry_name', type=click.STRING, nargs=-1, autocompletion=tabCompletionEntries)
@click.option('-p', '--path', default=os.path.expanduser('Downloads'), type=click.Path(), help='path for export')
@click.option('-f', '--fileformat', default='json', type=click.STRING, help='file format')
@cli.command()
def exportdb(tag_name, entry_name, path, fileformat):
    '''Export data base'''
    unlockStorage()
    if fileformat == 'json':
        with click.progressbar(entries, label='Exporting DB', show_eta=False, fill_char='#', empty_char='-') as bar:
            for e in bar:
                entries[e] = unlockEntry(e)
        with open(os.path.join(path, 'export.json'), 'w', encoding='utf8') as f:
            json.dump(entries, f)
    sys.exit(0)

# TODO CSV    
@cli.command()
@click.option('-p', '--path', type=click.Path(), help='path to import file')
def importdb(es):
    '''Import data base'''
    unlockStorage()
    for e in es:
        lockEntry(e)
    sys.exit(0)
