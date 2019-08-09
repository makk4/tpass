#!/usr/bin/env python3
from src import trezor as trezorapi
from src import crypto as cryptomodul
import click
import os
import subprocess
import sys
import json
import csv
import tempfile
import pyperclip
import time
import pyotp
import re

ICONS = {'home': {'emoji': '🏠'}, 'person-stalker': {'emoji': '👩‍👩‍👦'}, 'social-bitcoin': {'emoji': '₿'}, 'person': {'emoji': '😀'}, 'star': {'emoji': '⭐'}, 'flag': {'emoji': '🏳️'}, 'heart':{'emoji':'❤'}, 'settings': {'emoji':'⚙️'}, 'email':{'emoji':'✉️'},'cloud': {'emoji': '☁️'}, 'alert-circled': {'emoji':'⚠️'}, 'android-cart': {'emoji': '🛒'}, 'image': {'emoji': '🖼️'}, 'card': {'emoji': '💳'}, 'earth': {'emoji': '🌐'}, 'wifi': {'emoji': '📶'}}
DROPBOX_PATH = os.path.join(os.path.expanduser('~'), 'Dropbox', 'Apps', 'TREZOR Password Manager')
GOOGLE_DRIVE_PATH = os.path.join(os.path.expanduser('~'), 'Google Drive', 'Apps', 'TREZOR Password Manager')
DEFAULT_PATH = os.path.join(os.path.expanduser('~'), '.tpassword-store')
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
DICEWARE_FILE = os.path.join(CONFIG_PATH, 'wordlist.txt')
TMP = os.path.join(tempfile.gettempdir())
DEV_SHM = os.path.join('/', 'dev', 'shm')
CLIPBOARD_CLEAR_TIME = 15

tag_new = {'':{'title': '', 'icon': 'home'}}
entry_new = {'':{'title': '', 'username': '', 'password': {'type': 'String', 'data': ''}, 'nonce': '', 'tags': [], 'safe_note': {'type': 'String', 'data': ''}, 'note': '', 'success': True, 'export': True}}
tags = {'0': {'title': 'All', 'icon': 'home'}, }
entries = {}
db_json = {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': tags, 'entries': entries}
config = {'file_name': '', 'store_path': DEFAULT_PATH, 'cloud_provider': 'dropbox', 'pinentry': False, 'clipboardClearTimeSec': CLIPBOARD_CLEAR_TIME, 'storeMetaDataOnDisk': True}
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
    if 'file_name' not in config or 'store_path' not in config or 'pinentry' not in config or 'clipboardClearTimeSec' not in config or 'storeMetaDataOnDisk' not in config:
        click.echo('config parse error: ' + CONFIG_PATH)
        sys.exit(-1)
    if not os.path.exists(config['store_path']):
        click.echo('config: path error' + config['store_path'])
        sys.exit(-1)

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
            encKey = keys[2]
        except:
            raise Exception('Error while getting keys from device')
        config['file_name'] = keys[0]

        db_file = os.path.join(config['store_path'], config['file_name'])
        try:
            db_json = cryptomodul.decryptStorage(db_file, encKey)
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
    encKey = keys[2]
    tmp_file = os.path.join(tmp_file, fileName + '.json')
    config['file_name'] = fileName
    db_file = os.path.join(config['store_path'], config['file_name'])

    try:
        cryptomodul.encryptStorage(db_json, db_file, encKey)
    except:
        raise Exception('Error while encrypting storage')

    if config['storeMetaDataOnDisk'] is True and os.path.isfile(db_file):
        with open(tmp_file, 'w') as f:
            json.dump(db_json, f)
    
    if config['cloud_provider'] == 'git':
        subprocess.call('git commit -m "update db"', cwd=config['store_path'], shell=True)
        subprocess.call('git add *.pswd', cwd=config['store_path'], shell=True)

def loadWordlist():
    wordlist_txt = DICEWARE_FILE
    if not os.path.isfile(DICEWARE_FILE):
        wordlist_txt = os.path.join('wordlist.txt')
    words = {}
    try:
        with open(wordlist_txt) as f:
            for line in f.readlines():
                if re.compile('^([1-6]){5}\t(.)+$').match(line):
                    key, value = line.rstrip('\n').split('\t')
                    if(not key in words):
                        words[key] = value
                    else:
                        return False
    except:
        raise IOError('error while processing wordlist.txt file')
    return words

def clearClipboard():
    with click.progressbar(length=config['clipboardClearTimeSec'], label='Clipboard will clear', show_percent=False, fill_char='=', empty_char=' ') as bar:
        for i in bar:
            time.sleep(1)
    pyperclip.copy('')

def getClient():
    global client
    if client is None:
        try:
            client = trezorapi.getTrezorClient()
        except:
            raise Exception('Error while accessing trezor device')

def parseName(input_str):
    tag = ''; note = ''; username = ''; entry_id = ''
    if not '/' in input_str and  not ':' in input_str and not '#' in input_str:
        tag = note = input_str
    if '/' in input_str:
        tag = input_str.split('/')[0]
        input_str = input_str.split('/')[1]
    if ':' in input_str:
        note = input_str.split(':')[0]
        username = input_str.split(':')[1]
        input_str = input_str.split(':')[1]
    if '#' in input_str:
        username = input_str.split('#')[0]
        entry_id = input_str.split('#')[1]
    return tag, note, username, entry_id

def getEntry(name):
    name = parseName(name)
    note = name[1]; username = name[2]; entry_id = name[3]
    if entry_id != '':
        return entry_id, entries[entry_id]
    for k, v in entries.items():
        if note.lower() == v['note'].lower():
            if username == '' or username.lower() == v['username'].lower():
                return k, v
    return None

def getTag(tag_name):
    tag_name = parseName(tag_name)[0]
    for k, v in tags.items():
        if tag_name.lower() == v['title'].lower():
            return k, v
    return None

def getEntriesByTag(tag_id):
    es = {}
    for k, v in entries.items():
        if int(tag_id) in v['tags'] or int(tag_id) == 0 and v['tags'] == []:
            es.update( {k : v} )  
    return es

def printEntries(es, includeTree=False):
    if includeTree:
        start = '  ├── ';start_end = '  └── '
    else:
        start = ''; start_end = ''
    i = 0
    for k,v in es.items():
        if i == len(es)-1:
            click.echo(start_end + v['note'] + ':' + click.style(v['username'], fg='green') + click.style('#' + k, fg='magenta'))
        else:
            click.echo(start + v['note'] + ':' + click.style(v['username'], fg='green') + click.style('#' + k, fg='magenta'))
        i = i + 1

def printTags(ts, includeEntries=False):
    tag_str = ''
    for k,v in ts.items():
        icon = ICONS.get(v['icon'])['emoji'] or '? '
        click.echo(icon + '  ' + click.style(v['title'] + '',bold=True , fg='blue'))
        if includeEntries:
            es = getEntriesByTag(k)
            printEntries(es, True)

def tagsToString(ts, includeIds=False):
    tags_str = ''
    for k,v in ts.items():
        icon = ICONS.get(v['icon'])['emoji'] or '? '
        if includeIds:
            tags_str = tags_str + k + ': ' + icon + '  ' + v['title'] + '     '
        else:
            tags_str = tags_str + icon + '  ' + v['title'] + '  '
    return tags_str

def iconsToString():
    icon_str = ''
    for k,v in ICONS.items():
        icon_str = icon_str + k + ':' + v['emoji'] + ', '
    return icon_str

def unlockEntry(e):
    entry_id = e[0]; entry = e[1]
    if e is None or entry['success'] is False or entry['export'] is True:
        return None
    entry['success'] = False; entry['export'] = True
    try:   
        getClient()
        keys = trezorapi.getTrezorKeys(client)
        plain_nonce = trezorapi.getDecryptedNonce(client, entry)
    except:
        raise Exception('Error while accessing trezor device')    
    try:
        entry['password']['data'] = cryptomodul.decryptEntryValue(plain_nonce, entry['password']['data'])
        entry['password']['type'] = 'String'
        entry['safe_note']['data'] = cryptomodul.decryptEntryValue(plain_nonce, entry['safe_note']['data'])
        entry['safe_note']['type'] = 'String'
    except:
        raise Exception('Error while decrypting entry')
    entry['success'] = True
    return entry_id, entry

def lockEntry(e):
    entry_id = e[0]; entry = e[1]
    if e is None or entry['success'] is False or entry['export'] is False:
        return None
    entry['success'] = False; entry['export'] = False
    try:
        getClient()
        keys = trezorapi.getTrezorKeys(client)
        entry['nonce'] = trezorapi.getEncryptedNonce(client, entry)
        plain_nonce = trezorapi.getDecryptedNonce(client, entry)
    except:
        raise Exception('Error while accessing trezor device')
    try:
        entry['password']['data'] = cryptomodul.encryptEntryValue(plain_nonce, json.dumps(entry['password']['data']))
        entry['safe_note']['data'] = cryptomodul.encryptEntryValue(plain_nonce, json.dumps(entry['safe_note']['data']))
    except:
        raise Exception('Error while decrypting entry')
    entry['password']['type'] = 'Buffer'; entry['safe_note']['type'] = 'Buffer'
    entry['success'] = True
    return entry_id, entry

def insertEntry(e):
    global db_json
    global entries
    if e is None:
        return False
    entry_id = e[0]; entry = e[1]
    if entry_id == '':
        entry_id = str(max(int(entries.keys()) + 1))
    if entry['success'] is True and entry['export'] is False:
        entries.update( {entry_id : entry} )
        return True
    else:
        raise Exception('Error detected while inserting Entry, aborted')

def editEntry(e):
    entry_id = e[0]; entry = e[1]
    if entry['export'] is False:
        e = unlockEntry(e)
    if entry['success'] is False:
        return None
    entry['success'] = False
    click.echo(tagsToString(tags, True))
    click.echo('Choose a tag')
    inputTag = click.prompt(click.style('[tag(s)] ', bold=True), type=click.Choice(tags), default=entry['tags'])
    if int(inputTag) == '0':
        entry['tags'] = []
    else:
        entry['tags'] = [int(inputTag)]
    edit_json = {'item/url*':entry['note'], 'title':entry['title'], 'username':entry['username'], 'password':entry['password']['data'], 'secret':entry['safe_note']['data']}
    edit_json = click.edit(json.dumps(edit_json, indent=4), require_save=True, extension='.json')
    if edit_json:
        try:
            edit_json = json.loads(edit_json)
        except:
            raise IOError('edit gone wrong')
        if edit_json['item/url*'] is None or edit_json['item/url*'] == '':
            click.echo('item/url* field is mandatory')
            return None
        entry['note'] = edit_json['item/url*'];entry['title'] = edit_json['title'];entry['username'] = edit_json['username'];entry['password']['data'] = edit_json['password'];entry['safe_note']['data'] = edit_json['secret']
        entry['success'] = True
        e = (entry_id, entry)
        return lockEntry(e)
    return None

def editTag(t):
    if t is None:
        return None
    tag_id = t[0]; tag = t[1]
    click.echo(iconsToString() + '\n' + 'Choose icon')
    tag['icon'] = click.prompt(click.style('[icon] ', bold=True), type=click.Choice(ICONS), default=tag['icon'])
    tag['title'] = click.prompt(click.style('[title]', bold=True), type=click.STRING, default=tag['title'])
    return tag_id, tag

def insertTag(t):
    global db_json
    if t is None:
        return False
    tag_id = t[0]; tag = t[1]
    if tag_id == '':
        tag_id = str(max(int(tags.keys()) + 1))
    db_json['tags'].update( {tag_id : tag} )
    return True

def removeTag(t):
    if t is None:
        return False
    tag_id = t[0]; tag = t[1]
    del db_json['tags'][tag_id]
    es = getEntriesByTag(tag_id)
    for e in es:
        entries[e]['tags'].remove(int(tag_id))
    return True

def tabCompletionEntries(ctx, args, incomplete):
    loadConfig()
    unlockStorage()
    tabs = []
    for k,v in tags.items():
        selEntries = getEntriesByTag(k)
        for kk,vv in selEntries.items():
            tabs.append(v['title'].lower() + '/' + vv['note'].lower() + ':' + vv['username'].lower() + '#' + kk)
    return [k for k in tabs if incomplete.lower() in k]

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
@click.option('-p', '--path', default=DEFAULT_PATH, type=click.Path(), help='path to database')
@click.option('-c', '--cloud', default='dropbox', type=click.Choice(['dropbox', 'googledrive', 'git']), help='cloud provider: <dropbox> <googledrive> <git>')
@click.option('-a', '--pinentry', is_flag=True, help='ask for password on device')
@click.option('-d', '--nodisk', is_flag=False, help='do not store metadata on disk')
def init(path, cloud, pinentry, nodisk):
    '''Initialize new password storage'''
    global config
    if cloud == 'googledrive':
        path = GOOGLE_DRIVE_PATH
    elif cloud == 'dropbox':
        path = DROPBOX_PATH
    if not os.path.exists(path):
        os.makedirs(path)
    if len(os.listdir(path)) != 0:
        click.echo(path + ' is not empty, not initialized', err=True)
        exit(-1)
    config['file_name'] = 'init'; config['store_path'] = path; config['cloud_provider'] = cloud; config['pinentry'] = pinentry; config['storeMetaDataOnDisk'] = nodisk
    if cloud == 'git':
        subprocess.call('git init', cwd=config['store_path'], shell=True)
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
    for k,v in entries.items():
        if name.lower() in v['note'].lower() or name.lower() in v['title'].lower() or name.lower() in v['username'].lower():
            es.update( {k : v} ) 
    for k,v in tags.items():
        if name.lower() in v['title'].lower():
            ts.update( {k : v} ) 
    printEntries(es)
    printTags(ts)
    sys.exit(0)

# TODO generalize with kk, vv
@cli.command()
@click.argument('name', type=click.STRING, nargs=1)
@click.option('-i', '--caseinsensitive', is_flag=True, help='not case sensitive search')
def grep(name, caseinsensitive):
    '''Search for pattern in decrypted entries'''
    unlockStorage()
    for k, v in entries.items():
        v = unlockEntry((k,v))[1]
        for kk, vv in v.items():
            if kk in ['note', 'title', 'username']:
                if name.lower() in vv.lower():
                    click.echo(click.style(v['note'] + ':', bold=True) + click.style(v['username'], bold=True, fg='green') + click.style('#' + k, bold=True, fg='magenta') + click.style('//<' + kk + '>//: ', fg='blue') + vv)
        if name.lower() in v['password']['data'].lower():    
            click.echo(click.style(v['note'] + ':', bold=True) + click.style(v['username'], bold=True, fg='green') + click.style('#' + k, bold=True, fg='magenta') + click.style('//<password>//: ', fg='blue') + v['password']['data'])
        if name.lower() in v['safe_note']['data'].lower():  
            click.echo(click.style(v['note'] + ':', bold=True) + click.style(v['username'], bold=True, fg='green') + click.style('#' + k, bold=True, fg='magenta') + click.style('//<secret>//: ', fg='blue') + v['safe_note']['data'])
    sys.exit(0)

@cli.command()
@click.argument('tag_name', default='', type=click.STRING, nargs=1, autocompletion=tabCompletionTags)
def ls(tag_name):# TODO alias
    '''List names of passwords from tag'''
    unlockStorage()
    if tag_name == '':
        printTags(tags, True)
    else:
        t = getTag(tag_name)
        printTags({t[0] : t[1]}, True)
    sys.exit(0)
    
@cli.command()
@click.argument('entry_name', type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
@click.option('-s', '--secrets', is_flag=True, help='show password and secret notes')
@click.option('-j', '--json', is_flag=True, help='json format')
def show(entry_name, secrets, json): # TODO alias
    '''Decrypt and print an entry'''
    unlockStorage()
    e = getEntry(entry_name)
    if e is None:
        return
    entry = e[1]; entry_id = e[0]

    if not secrets:
        pwd = '********'
        safeNote = '********'
    else:
        e = unlockEntry(e)
        pwd = entry['password']['data']
        safeNote = entry['safe_note']['data']
    if json:
        edit_json = {entry_id:{'item/url*':entry['note'], 'title':entry['title'], 'username':entry['username'], 'password':pwd, 'secret':safeNote, 'tags':entry['tags']}}
        click.echo(edit_json)
    else:
        ts = {}
        for i in entry['tags']:
            ts[i] = tags.get(str(i))

        click.echo(click.style('#' + entry_id, bold=True, fg='magenta') + '\n' +
            click.style('item/url*: ', bold=True) + entry['note'] + '\n' +
            click.style('title:     ', bold=True) + entry['title'] + '\n' +
            click.style('username:  ', bold=True) + entry['username'] + '\n' +
            click.style('password:  ', bold=True) + pwd + '\n' +
            click.style('secret:    ', bold=True) + safeNote  + '\n' +
            click.style('tags:      ', bold=True) + tagsToString(ts))
    sys.exit(0)

@cli.command()
@click.option('-u', '--user', is_flag=True, help='copy user')
@click.option('-i', '--url', is_flag=True, help='copy item/url*')
@click.option('-s', '--secret', is_flag=True, help='copy secret')
@click.argument('entry_name', type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
def clip(user, url, secret, entry_name):# TODO alias; TODO open browser
    '''Decrypt and copy line of entry to clipboard'''
    unlockStorage()
    e = getEntry(entry_name)[1]
    if e is None:
        sys.exit(-1)
    if user:
        pyperclip.copy(e['username'])
    elif url:
        pyperclip.copy(e['title'])
    else:
        e = unlockEntry(e)
        if secret:
            pyperclip.copy(e['password']['data'])
        else:
            pyperclip.copy(e['safe_note']['data'])
        clearClipboard()
    sys.exit(0)
    
@cli.command()
@click.argument('length', default=15, type=int)
@click.option('-i', '--insert', default=None, type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
@click.option('-c', '--clip', is_flag=True, help='copy to clipboard')
@click.option('-t', '--typeof', default='password', type=click.Choice(['password', 'wordlist', 'pin']), help='type of password')
@click.option('-s', '--seperator', default=' ', type=click.STRING, help='seperator for passphrase')
@click.option('-f', '--force', is_flag=True, help='force without confirmation')
@click.option('-d', '--entropy', is_flag=True, help='entropy from trezor device and host mixed')
def generate(length, insert, typeof, clip, seperator, force, entropy):
    '''Generate new password'''
    global db_json
    if (length < 6 and typeof is 'password') or (length < 3 and typeof is 'wordlist') or (length < 4 and typeof is 'pin'):
        if not click.confirm('Warning: ' + length + ' is too short for password with type ' + typeof + '. Continue?'):
            sys.exit(-1)
    if entropy:
        getClient()
        entropy = trezorapi.getEntropy(client, length)
    else:
        entropy = None
    if typeof == 'wordlist':
        words = loadWordlist()
        pwd = cryptomodul.generatePassphrase(length, words, seperator, entropy)
    elif typeof == 'pin':
        pwd = cryptomodul.generatePin(length)
    elif typeof == 'password':
        pwd = cryptomodul.generatePassword(length)
    if insert:
        unlockStorage()
        e = getEntry(insert)
        e = unlockEntry(e)
        e[1]['password']['data'] = pwd
        e = lockEntry(e)
        if insertEntry(e):
            if force or click.confirm('Insert password in entry ' + click.style(e[1]['title'], bold=True)):
                saveStorage()
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
        t = getTag(tag)
        if t[0] == '0':
            sys.exit(0)
        removeTag(t)
        if force or click.confirm('Delete tag: ' + click.style(t[1]['title'], bold=True)):
            saveStorage()
    else:
        entry_id = getEntry(entry_name)[0]
        del db_json['entries'][entry_id]
        if force or click.confirm('Delete entry ' + click.style(entries[entry_id]['title'], bold=True)):
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
    global entry_new
    if tag:
        t = editTag(tag_new)
        if insertTag(t):
            saveStorage()
    else:
        if tag_name != '':
            t = getTag(tag_name)
            if t is not None:
                entry_new['tag'] = [int(t[0])]
        e = editEntry(entry_new)
        if insertEntry(e):
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
        t = editTag(t)
        if insertTag(t):
            saveStorage()
    else:
        e = getEntry(entry_name)
        e = editEntry(e)
        if insertEntry(e):
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
def config(edit, reset, setting_name, setting_value):
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
        unlockStorage()
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
@click.option('-p', '--path', default=os.path.expanduser('~'), type=click.Path(), help='path for export')
@click.option('-f', '--fileformat', default='json', type=click.Choice(['json', 'csv','txt']), help='file format')
@cli.command()
def exportdb(tag_name, entry_name, path, fileformat):
    '''Export data base'''
    global entries
    unlockStorage()
    with click.progressbar(entries, label='Decrypt entries', show_eta=False, fill_char='#', empty_char='-') as bar:
        for e in bar:
            entries[e] = unlockEntry(e)[1]
    if fileformat == 'json':
        with open(os.path.join('.', 'export.json'), 'w', encoding='utf8') as f:
            json.dump(entries, f)
    elif fileformat == 'csv':
        with open(os.path.join('.', 'export.csv'), 'w') as f:
            writer = csv.writer(f, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for e in entries.items():
                writer.writerow({e['note'], e['title'], e['username'],e['password']['data'],e['safe_note']['data']})
    sys.exit(0)

# TODO CSV    
@cli.command()
@click.option('-p', '--path', type=click.Path(), help='path to import file')
def importdb(es):
    '''Import data base'''
    unlockStorage()
    for e in es.items():
        lockEntry(e)
        insert(e)
        saveStorage()
    sys.exit(0)
