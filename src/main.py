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

ICONS = {'home': {'emoji': '🏠'}, 'person-stalker': {'emoji': '👩‍👩‍👦'}, 'social-bitcoin': {'emoji': '₿ '}, 'person': {'emoji': '😀'}, 'star': {'emoji': '⭐'}, 'flag': {'emoji': '🏳️'}, 'heart':{'emoji':'❤'}, 'settings': {'emoji':'⚙️'}, 'email':{'emoji':'✉️'},'cloud': {'emoji': '☁️'}, 'alert-circled': {'emoji':'⚠️'}, 'android-cart': {'emoji': '🛒'}, 'image': {'emoji': '🖼️'}, 'card': {'emoji': '💳'}, 'earth': {'emoji': '🌐'}, 'wifi': {'emoji': '📶'}}
DROPBOX_PATH = os.path.join(os.path.expanduser('~'), 'Dropbox', 'Apps', 'TREZOR Password Manager')
GOOGLE_DRIVE_PATH = os.path.join(os.path.expanduser('~'), 'Google Drive', 'Apps', 'TREZOR Password Manager')
GIT_PATH = os.path.join(os.path.expanduser('~'), '.tpassword-store')
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
WORDLIST = os.path.join(CONFIG_PATH, 'wordlist.txt')
TMP = os.path.join(tempfile.gettempdir())
DEV_SHM = os.path.join('/', 'dev', 'shm')
CLIPBOARD_CLEAR_TIME = 15

newEntry_plain = {'title': '', 'username': '', 'password': '', 'note': '', 'tags': [], 'safe_note': '', 'nonce': '', 'success': True, 'export': True}
newEntry = {'title': '', 'username': '', 'password': {'type': 'Buffer', 'data': []}, 'nonce': '', 'tags': [], 'safe_note': {'type': 'Buffer', 'data': []}, 'nonce': '', 'success': True, 'export': False}
entries = {}
tags = {'0': {'title': 'All', 'icon': 'home'}, }
db_json = {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': tags, 'entries': entries}
config = {'file_name': '', 'store_path': DROPBOX_PATH, 'cloud_provider': 'dropbox', 'pinentry': False, 'clipboardClearTimeSec': CLIPBOARD_CLEAR_TIME}
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

def loadStorage():
    global entries
    global tags
    tmp_path = DEV_SHM
    if not os.path.exists(DEV_SHM):
        tmp_path = TMP
    tmp_file = os.path.join(tmp_path, config['file_name'] + '.json')
    if (os.path.isfile(tmp_file)):
        with open(tmp_file) as f:
            db_json = json.load(f)
            entries = db_json['entries']
            tags = db_json['tags']
 
def unlockStorage():
    global db_json
    global entries
    global tags
    db_file = os.path.join(config['store_path'], config['file_name'])
    tmp_path = DEV_SHM

    if config['file_name'] is '':
        return -1

    if not os.path.isfile(db_file):
        return -2

    if not os.path.exists(DEV_SHM):
        click.echo('warning: /dev/shm not found on host, using not as secure /tmp/ for plain metadata')
        tmp_path = TMP

    tmp_file = os.path.join(tmp_path, config['file_name'] + '.json')
    if not os.path.isfile(tmp_file) or (os.path.isfile(tmp_file) and (os.path.getmtime(tmp_file) < os.path.getmtime(db_file))):
        click.echo('unlocking storage')
        getClient()
        try:
            keys = trezorapi.getTrezorKeys(client)
        except:
            click.echo('Error while getting keys from device')
        config['file_name'] = keys[0]
        db_file = os.path.join(config['store_path'], config['file_name'])
        tmp_file = os.path.join(tmp_path, config['file_name'] + '.json')
        db_json = cryptomodul.decryptStorage(db_file, keys)

        with open(tmp_file, 'w') as f:  
            json.dump(db_json, f)

    with open(tmp_file) as f:
        db_json = json.load(f)
    entries = db_json['entries']
    tags = db_json['tags']
    return 0

def saveStorage():
    global config
    tmp_file = DEV_SHM

    getClient()
    
    if not os.path.exists(DEV_SHM):
        tmp_file = TMP
    try:
        keys = trezorapi.getTrezorKeys(client)
        fileName = keys[0]
        tmp_file = os.path.join(tmp_file, fileName + '.json')
        config['file_name'] = fileName
    except:
        click.echo('Error while accessing trezor device')

    db_file = os.path.join(config['store_path'], config['file_name'])

    try:
        cryptomodul.encryptStorage(db_json, db_file, keys)
    except:
        raise Exception('Encryption gone wrong')

    if os.path.isfile(db_file):
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
            click.echo('Error while accessing trezor device')

def getEntry(entry_name):
    if '/' in entry_name:
        entry_name = entry_name.split('/')[1]
    for e in entries:
        if entry_name.lower() == entries[e]['title'].lower():
            return str(e), entries[e]
        elif entry_name.lower() == entries[e]['note'].lower():
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
    if not tag_id:
        for t in tags:
            tag_id = str(int(t) + 1)
    if tag:
        db_json['tags'].update( {tag_id : tag} )
    else:
        click.echo('Error detected, aborted')

def getEntriesByTag(tag_id):
    result = {}
    for e in entries:
        ts = entries[e]['tags']
        if int(tag_id) == 0:
            result[e] = entries[e]
        for t in ts:
            if t == int(tag_id):
                result[e] = entries[e]        
    return result

def printEntries(es):
    for e in es:
        click.echo(es[e]['title'])

def printTags(ts, includeEntries=False):
    tag_str = ''
    for t in ts:
        tag_id = t
        t = tags.get(tag_id)
        icon = '# '
        icon = ICONS.get(t['icon'])['emoji']
        click.echo(icon + '  ' + t['title'])
        if includeEntries:
            es = getEntriesByTag(tag_id)
            click.echo('----------')
            printEntries(es)
            click.echo('----------')
    return tag_str.rstrip('\n')

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
    print(tags_str)
    return tags_str

def iconsToString():
    icon_str = ''
    for i in ICONS:
        icon_str = icon_str + i + ':' + ICONS.get(i)['emoji'] + ', '
    return icon_str

def unlockEntry(e):
    if e is None or e['success'] is not True:
        return None
    e['success'] = False
    e['export'] = True
    pwd = e['password']['data']
    safeNote = e['safe_note']['data']

    getClient()
    try:   
        keys = trezorapi.getTrezorKeys(client)
        plain_nonce = trezorapi.getDecryptedNonce(client, e)
    except:
        pass
        click.error('Error while accessing trezor device')
    try:
        pwd = cryptomodul.decryptEntryValue(plain_nonce, pwd)
        e['safe_note'] = cryptomodul.decryptEntryValue(plain_nonce, safeNote)
    except:
        pass
    e['success'] = True
    return {'title': e['title'], 'username': e['username'], 'password': pwd, 'nonce': e['nonce'], 'tags': e['tags'], 'safe_note': e['safe_note'], 'note': e['note'], 'success': True, 'export': True}


def lockEntry(e): 
    if e is None or e['success'] is not True:
        return None
    e['success'] = False
    e['export'] = False
    pwd = e['password']
    safeNote = e['safe_note']

    getClient()
    try:
        keys = trezorapi.getTrezorKeys(client)
        e['nonce'] = trezorapi.getEncryptedNonce(client, e)
        plain_nonce = trezorapi.getDecryptedNonce(client, e)
    except:
        raise Exception('Error while accessing trezor device')

    try:
        pwd = cryptomodul.encryptEntryValue(str(pwd), str(plain_nonce))
        safeNote = cryptomodul.encryptEntryValue(str(safeNote), str(plain_nonce))
    except:
        raise Exception('Error while encrypting entry')
    return {'title': e['title'], 'username': e['username'], 'password': {'type': 'Buffer', 'data': pwd}, 'nonce': e['nonce'], 'tags': e['tags'], 'safe_note': {'type': 'Buffer', 'data': safeNote}, 'note': e['note'], 'success': True, 'export': False}

def saveEntry(entry, entry_id=None):
    global db_json
    if not entry_id:
        for e in entries:
            entry_id = str(int(e) + 1)
    if entry and entry['success'] is True and entry['export'] is False:
        db_json['entries'].update( {entry_id : entry} )
        return True
    else:
        return False
        click.echo('Error detected, aborted')

def editEntry(e):
    edited_txt = click.edit('Save to apply changes, all text after ">:" will be read \n' + '\n[title] >:' + e['title'] + '\n[item/url*] >:' + e['note'] + '\n[username] >:' + e['username'] + '\n[password] >:' + e['password'] + '\n[secret] >:' + e['safe_note'], require_save=True)
    if edited_txt:
        e['success'] = False
        for line in edited_txt.split('\n'):
            if re.compile(r'\[title\] >:(.*?)').match(line):
                e['title'] = re.split(r'\[title\] >:', line)[1]
            elif re.compile(r'\[item/url\*\] >:(.*?)').match(line):
                e['note'] = re.split(r'\[item/url\*\] >:', line)[1]
            elif re.compile(r'\[username\] >:(.*?)').match(line):
                e['username'] = re.split(r'\[username\] >:', line)[1]
            elif re.compile(r'\[password\] >:(.*?)').match(line):
                e['password'] = re.split(r'\[password\] >:', line)[1]
            elif re.compile(r'\[secret\] >:(.*?)').match(line):
                e['safe_note'] = re.split(r'\[secret\] >:', line)[1]
    click.echo(tagsToString(tags, True))
    click.echo('Choose tag(s)')
    inputTag = click.prompt(click.style('[tag(s)] ', bold=True), default=e['tags'], type=click.Choice(tags))
    e['tags'] = [int(inputTag)]
    e['success'] = True
    return e

def editTag(t, tag_id):
    t['title'] = click.prompt('[title] ', default=t['title'])
    click.echo(iconsToString())
    t['icon'] = click.prompt(click.style('[tag(s)] ', bold=True), default=t['icon'], type=click.Choice(ICONS))
    return t

def tabCompletionEntries(ctx, args, incomplete):
    loadConfig()
    loadStorage()
    tabs = []
    for t in tags:
        selEntries = getEntriesByTag(t)
        for e in selEntries:
            tabs.append(tags[t]['title'].lower() + '/' + selEntries[e]['note'].lower())
    return [k for k in tabs if incomplete.lower() in k]

def tabCompletionTags(ctx, args, incomplete, printEntries=False):
    loadConfig()
    loadStorage()
    tabs = []
    for t in tags:
        tabs.append(tags[t]['title'].lower() + '/')
    return [k for k in tabs if incomplete.lower() in k]


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
    unlockStorage()
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

    config = {'file_name': 'init', 'store_path': path, 'cloud_provider': cloud, 'pinentry': pinentry}

    if cloud == 'git':
        subprocess.call('init', cwd=config['store_path'], shell=True)
        click.echo('password store initialized with git in ' + path)
        
    if saveStorage():
        writeConfig()
        click.echo('Warining: /DEV/SHM not found on system, using not as secure TMP for metadata')
        click.echo('password store initialized in ' + path)
        exit(0)
    else:
        exit(-2)

@cli.command()
@click.argument('name', type=click.STRING, nargs=1)
def find(name):# TODO alias
    '''List names of passwords and tags that match names'''
    es = {}
    ts = {}
    for e in entries:
        e = getEntry(e)[1]
        if name.lower() in e['title'].lower():
            es[str(e)] = e
        elif name.lower() in e['note'].lower():
            es[str(e)] = e
    for t in tags:
        t = getTag(t)[1]
        if name.lower() in t['title'].lower():
            ts[str(t)] = t
    printEntries(es)
    printTags(ts)
    sys.exit(0)

def grep(name):
    '''Search for pattern in decrypted entries'''
    for e in entries:
        e = unlockEntry(entries[e])
        if name.lower() in e['title'].lower():
            click.echo(click.style('[' + e['title'] + ']//field: <title>//: ', bold=True) + e['title'].lower())
        elif name.lower() in e['note'].lower():
            click.echo(click.style('[' + e['note'] + ']//field: <note>//: ', bold=True) + e['note'].lower())
        elif name.lower() in e['username'].lower():
            click.echo(click.style('[' + e['username'] + ']//field: <username>//: ', bold=True) + e['username'].lower())
        elif name.lower() in e['password'].lower():
            click.echo(click.style('[' + e['password'] + ']//field: <password>//: ', bold=True) + e['password'].lower())
        elif name.lower() in e['safe_note'].lower():
            click.echo(click.style('[' + e['safe_note'] + ']//field: <titsafe_notele>//: ', bold=True) + e['safe_note'].lower())
    sys.exit(0)

@cli.command()
@click.argument('tag_name', default='', type=click.STRING, nargs=1, autocompletion=tabCompletionTags)
def ls(tag_name):# TODO alias
    '''List names of passwords from tag'''
    ts = {}
    if tag_name == '':
        ts = tags
    else:
        t = getTag(tag_name)
        ts[t[0]] =t[1]

        if t[1] is None:
            return
    printTags(ts, True)
    sys.exit(0)
    
@cli.command()
@click.argument('entry_name', type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
@click.option('-s', '--secrets', is_flag=True, help='show password and secret notes')
@click.option('-j', '--json', is_flag=True, help='json format')
def cat(entry_name, secrets, json): # TODO alias
    '''Decrypt and print an entry'''
    e = getEntry(entry_name)[1]
    if e is None:
        return

    if not secrets:
        pwd = '********'
        safeNote = '********'
    else:
        e = unlockEntry(e)
        pwd = e['password']
        safeNote = e['safe_note']
    if json:
        click.echo(e)
    else:
        tag = ''
        icons = ICONS

        ts = {}
        for i in e['tags']:
            ts[i] = tags.get(str(i))

        tag = tagsToString(ts)

        click.echo('~~+~#~+~~+~#~+~~+~#~+~~+~#~+' + '\n' +
            click.style('\t' + e['note'], bold=True) + '\n' +
            '+~#~+~~+~#~+~~+~#~+~~+~#~+~~' + '\n' +
            click.style('username: ', bold=True) + e['username'] + '\n' +
            click.style('password: ', bold=True) + pwd + '\n' +
            click.style('item/url: ', bold=True) + e['title'] + '\n' +
            click.style('secret:   ', bold=True) + safeNote  + '\n' +
            click.style('tags:     ', bold=True) + tag)
    sys.exit(0)

@cli.command()
@click.option('-u', '--user', is_flag=True, help='copy user')
@click.option('-i', '--url', is_flag=True, help='copy item/url*')
@click.option('-s', '--secret', is_flag=True, help='copy secret')
@click.argument('entry_name', type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
def clip(user, url, secret, entry_name):# TODO alias; TODO open browser
    '''Decrypt and copy line of entry to clipboard'''
    e = getEntry(entry_name)[1]
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
    
    #click.launch('https://www.' + e['title'])
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
        e = getEntry(insert)
        entry_id = e[0]
        e = e[1]
        if e is None:
            return
        e = unlockEntry(e)
        e['password'] = pwd
        e = lockEntry(e)
        if force or click.confirm('Insert password in entry ' + click.style(entries[entry_id]['title'], bold=True)):
            saveEntry(e, entry_id)
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
@click.argument('entry_name', type=click.STRING, nargs=1, autocompletion=tabCompletionEntries)
def rm(entry_name, tag, force):# TODO alias
    '''Remove entry or tag'''
    global db_json
    if tag:
        tag_id = getTag(tag)[0]
        if not tag_id or tag_id == '0':
            sys.exit(-1)
        if force or click.confirm('Delete tag: ' + click.style(tags[tag_id]['title'], bold=True)):
            del db_json['tags'][tag_id]
            saveStorage()
    else:
        entry_id = getEntry(entry_name)[0]
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
    global db_json
    if tag is True:
        tag_id = getTag(tag_name)[0]
        if tag_id:
            sys.exit(-1)
        t = {'title': '', 'icon': ''}
        t = editTag(t, tag_id)
        saveTag(t)
        saveStorage()
    else:
        tag_id = getTag(tag_name)[0]
        if tag_id is None:
            sys.exit(-1)

        if tag_name is not 'all' and getTag(tag_name)[1]:
            t = getTag(tag_name)[0]
            tag = [t]
        else:
            tag = []

        e = {'title': entry_name, 'username': '', 'password': '', 'nonce': '', 'tags': tag, 'safe_note': '', 'note': '', 'success': False, 'export': True}
        e = editEntry(e)
        e = lockEntry(e)
        saveEntry(e)
        saveStorage()
    sys.exit(0)

@cli.command()
@click.argument('entry_name', type=click.STRING, default='', nargs=1, autocompletion=tabCompletionEntries)
@click.option('-t', '--tag', type=click.STRING, default='', nargs=1, help='edit tag', autocompletion=tabCompletionTags)
def edit(entry_name, tag):
    '''Edit entry or tag'''
    if tag:
        t = getTag(tag)
        tag_id = t[0]
        t = t[1]
        if t is None:
            sys.exit(-1)
        t = editTag(t, tag_id)
        saveTag(t, tag_id)
        saveStorage()
    else:
        entry_id = getEntry(entry_name)[0]
        e = getEntry(entry_name)[1]
        if e is None:
            sys.exit(-1)

        e = unlockEntry(e)
        e = editEntry(e)
        e = lockEntry(e)
        saveEntry(e, entry_id)
        saveStorage()
    sys.exit(0)

@cli.command()
@click.argument('commands', type=click.STRING, nargs=-1)
def git(commands):
    '''Call git commands on db storage'''
    subprocess.call('git '+ ' '.join(commands), cwd=config['store_path'], shell=True)
    sys.exit(0)

@cli.command()
@click.argument('argument', type=click.Choice(['reset', 'edit']), nargs=1, autocompletion=tabCompletionEntries)
def conf(argument):
    '''Configuration settings'''
    if argument == 'reset':
        if os.path.isfile(CONFIG_FILE):
            os.remove(CONFIG_FILE)
    if argument == 'edit':
        click.edit(filename=CONFIG_FILE)
    sys.exit(0)

@cli.command()
def lock():
    '''Remove Plain Metadata file from disk'''
    os.remove(os.path.join(TMP, config['file_name'] + '.json'))
    os.remove(os.path.join(DEV_SHM, config['file_name'] + '.json'))
    sys.exit(0)

# TODO CSV
@click.argument('tag_name', default='all', type=click.STRING, nargs=1, autocompletion=tabCompletionTags)
@click.argument('entry_name', type=click.STRING, nargs=-1, autocompletion=tabCompletionEntries)
@click.option('-p', '--path', default=os.path.expanduser('Downloads'), type=click.Path(), help='path for export')
@click.option('-f', '--fileformat', default='json', type=click.STRING, help='file format')
@cli.command()
def exportdb(tag_name, entry_name, path, fileformat):
    '''Export data base'''
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
    for e in es:
        lockEntry(e)
    sys.exit(0)
