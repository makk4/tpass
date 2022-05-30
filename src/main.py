#!/usr/bin/env python3
import click
import collections
import csv
import logging
import operator
import os
import pyperclip
import re
import subprocess
import sys
import tempfile
import time
import uuid
try:
    import simplejson as json
except:
    import json
from src import crypto
from src import trezor

'''
Config variables
'''
# Paths
DEFAULT_PATH = os.path.join(os.path.expanduser('~'), '.tpassword-store')
DROPBOX_PATH = os.path.join(os.path.expanduser('~'), 'Dropbox', 'Apps', 'TREZOR Password Manager')
GOOGLE_DRIVE_PATH = os.path.join(os.path.expanduser('~'), 'Google Drive', 'Apps', 'TREZOR Password Manager')
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
TMP_PATH = os.path.join('/', 'dev', 'shm')
# File Locations
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
DICEWARE_FILE = os.path.join(CONFIG_PATH, 'wordlist.txt')
LOG_FILE = os.path.join(CONFIG_PATH, 'tpass.log')
LOCK_FILE = os.path.join(CONFIG_PATH, 'lockfile')
# Actual Files
ICONS = {'home':u'\U0001f3e0', 'person-stalker':u'\U0001F469\u200D\U0001F467', 'social-bitcoin':'₿', 'person':u'\U0001F642', 'star':u'\u2B50', 'flag':u'\U0001F3F3', 'heart':u'\u2764', 'settings':u'\u2699', 'email':u'\u2709', 'cloud':u'\u2601', 'alert-circled':u'\u26a0', 'android-cart':u'\U0001f6d2', 'image':u'\U0001F5BC', 'card':u'\U0001f4b3', 'earth':u'\U0001F310', 'wifi':u'\U0001f4f6'}
CONFIG = {'fileName': '', 'path': DEFAULT_PATH, 'useGit': False, 'clipboardClearTimeSec': 15, 'storeMetaDataOnDisk': True, 'orderType': 'date', 'showIcons': False}
LOCK = {'uuid':uuid.uuid4().int}
# Constants
ENC_ENTROPY_BYTES = 12
NONCE_ENTROPY_BYTES = 32

'''
Instance variables
'''
tags = {'0': {'title': 'All', 'icon': 'home'},}
entries = {}
db_json = {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': tags, 'entries': entries}
client = trezor.TrezorDevice()
pwd_last_change_time = 0
pwd_file = None
tmp_file = None

'''
Helper Methods
'''

def write_lockfile():
    if os.path.isfile(LOCK_FILE):
        sys.exit('Error: password store is locked by another instance, remove lockfile to proceed: ' + LOCK_FILE)
    with open(LOCK_FILE, 'w', encoding='utf8') as f:
        json.dump(LOCK, f)

def load_config():
    global CONFIG; global tmp_file; global pwd_file
    if not os.path.isfile(CONFIG_FILE):
        write_config()
    with open(CONFIG_FILE) as f:
        CONFIG = json.load(f)
    if 'fileName' not in CONFIG or 'path' not in CONFIG or 'storeMetaDataOnDisk' not in CONFIG or 'orderType' not in CONFIG:
        handle_exception('CONFIG_PARSE_ERROR')
    pwd_file = os.path.join(CONFIG['path'], CONFIG['fileName'])
    if CONFIG['storeMetaDataOnDisk'] is True:
        tmp_file = os.path.join(TMP_PATH, CONFIG['fileName'] + '.json')
        if not os.path.exists(TMP_PATH):
            tmp_file = os.path.join(tempfile.gettempdir(), CONFIG['fileName'] + '.json')
            logging.warning('/dev/shm not found on host, using not as secure /tmp for metadata')

def write_config():
    if not os.path.exists(CONFIG_PATH):    
        os.mkdir(CONFIG_PATH)
    with open(CONFIG_FILE, 'w', encoding='utf8') as f:
        json.dump(CONFIG, f, indent=4)
 
def unlock_storage():
    global db_json; global entries; global tags; global pwd_last_change_time
    if CONFIG['fileName'] == '' or not os.path.isfile(pwd_file):
        handle_exception('NOT_INITIALIZED')
    
    tmp_need_update = not os.path.isfile(tmp_file) or (os.path.isfile(tmp_file) and (os.path.getmtime(tmp_file) < os.path.getmtime(pwd_file)))
    if CONFIG['storeMetaDataOnDisk'] is False or ( CONFIG['storeMetaDataOnDisk'] is True and tmp_need_update ):
        try:
            keys = client.getTrezorKeys()
            encKey = keys[2]
        except Exception as ex:
            handle_exception('TREZOR_KEY_ERROR', ex)
        try:
            db_json = crypto.decryptStorage(pwd_file, encKey)
        except Exception as ex:
            handle_exception('PASSWORD_UNLOCK_READ_ERROR', ex)
        entries = db_json['entries']; tags = db_json['tags']; db_json['config']['orderType'] = CONFIG['orderType'] 
        if CONFIG['storeMetaDataOnDisk'] is True:
            with open(tmp_file, 'w') as f:
                json.dump(db_json, f)
    
    if CONFIG['storeMetaDataOnDisk'] is True:
        with open(tmp_file) as f:
            db_json = json.load(f)
            entries = db_json['entries']; tags = db_json['tags']
    if CONFIG['orderType'] == 'title':
        entries = collections.OrderedDict(sorted(entries.items(), key=lambda v: v[1]['title']))
        tags = collections.OrderedDict(sorted(tags.items(), key=lambda v: v[1]['title']))
    elif CONFIG['orderType'] == 'date':
        entries = collections.OrderedDict(sorted(entries.items()))
        tags = collections.OrderedDict(sorted(tags.items()))
    pwd_last_change_time = os.path.getmtime(pwd_file)

def save_storage():
    global CONFIG
    if not os.path.isfile(LOCK_FILE):
        handle_exception('LOCKFILE_DELETED')
    with open(LOCK_FILE) as f:
        lock = json.load(f)
    if lock['uuid'] != LOCK['uuid']:
        handle_exception('LOCKFILE_CHANGED')
    if not os.path.isfile(pwd_file) or os.path.getmtime(pwd_file) != pwd_last_change_time:
        handle_exception('PASSWORD_FILE_CHANGED')
    try:
        keys = client.getTrezorKeys()
        encKey = keys[2]
        iv = client.getEntropy(ENC_ENTROPY_BYTES)
    except Exception as ex:
        handle_exception('TREZOR_DEVICE_ERROR', ex)
    try:
        crypto.encryptStorage(db_json, pwd_file, encKey, iv)
    except Exception as ex:
        handle_exception('PASSWORD_FILE_ENCRYPT_ERROR', ex)
    if CONFIG['storeMetaDataOnDisk'] is True:
        with open(tmp_file, 'w') as f:
            json.dump(db_json, f)
    if CONFIG['useGit'] is True:
        subprocess.call('git commit -am "sync password-store"', cwd=CONFIG['path'], shell=True)
        
def load_wordlist():
    wordlist = DICEWARE_FILE
    if not os.path.isfile(wordlist):
        wordlist = os.path.join('.', 'wordlist.txt')
    words = {}
    try:
        with open(wordlist) as f:
            for line in f.readlines():
                if re.compile('^([1-6]){5}\t(.)+$').match(line):
                    key, value = line.rstrip('\n').split('\t')
                    if(not key in words):
                        words[key] = value
    except Exception as ex:
        handle_exception('DICEWARE_FILE_PARSE_ERROR', ex)
    return words

def clear_clipboard():
    with click.progressbar(length=CONFIG['clipboardClearTimeSec'], \
         label='Clipboard will clear', show_percent=False, \
              fill_char='#', empty_char='-') as bar:
        for i in bar:
            time.sleep(1)
    pyperclip.copy('')

def handle_exception(error, ex=None):
    logging.error(ERROR_CODES[error]['message'])
    if ex is not None:
        logging.debug(ex)
    clean_exit(ERROR_CODES[error]['code'])

def clean_exit(exit_code=0):
    if os.path.isfile(LOCK_FILE):
        os.remove(LOCK_FILE)
    sys.exit(exit_code)

def start_logging(debug):
    logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, filemode='w', \
         format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', \
             datefmt='%m-%d %H:%M')
    console = logging.StreamHandler()
    if debug:
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info('tpass started')

'''
Password Store Methods
'''

def get_entry(names):# TODO compare tags given
    tag = names[0]; title = names[1]; username = names[2]; entry_id = names[3]
    if entry_id != '' and entries.get(entry_id):
        return entry_id, entries[entry_id]
    for k, v in entries.items():
        if title == v['title']:
            if username == '' or username == v['username']:
                return k, v
    click.echo(click.style(' '.join(names), bold=True) + ' is not in the password store')
    return None

def get_tag(tag_string):
    for k, v in tags.items():
        if tag_string == v['title']:
            return k, v
    click.echo(click.style(tag_string, bold=True) + ' is not a tag in the password store')
    return None

def get_entries_by_tag(tag_id):
    return dict(filter(lambda e: int(tag_id) in e[1]['tags'] \
         or (int(tag_id) == 0 and  e[1]['tags'] == []), entries.items()))

def get_tags_from_entry(e):
    return dict(filter(lambda t: int(t[0]) in e[1]['tags'], tags.items()))

def print_entries(es, includeTree=False):
    if includeTree:
        start = '  ' + u'\u251C' + u'\u2500' + u'\u2500' + ' '
        start_end = '  ' + u'\u2514' + u'\u2500' + u'\u2500' + ' '
    else:
        start = ''; start_end = ''
    i = 0
    for k,v in es.items():
        if i == len(es)-1:
            click.echo(start_end + click.style(v['title'], fg='green') + ' :' + v['username'] + click.style(' #' + k, fg='yellow'))
        else:
            click.echo(start + click.style(v['title'], fg='green') + ' :' + v['username'] + click.style(' #' + k, fg='yellow'))
        i = i + 1

def print_tags(ts, includeEntries=False):
    for k,v in ts.items():
        if CONFIG['showIcons'] is True:
            icon = ICONS.get(v['icon']) + ' ' or '? '
        else:
            icon = ''
        click.echo(icon + click.style(v['title'], bold=True , fg='blue'))
        if includeEntries:
            es = get_entries_by_tag(k)
            print_entries(es, True)

def tags_to_string(ts, showIcons=False):
    tags_str = ''
    for k,v in ts.items():
        if showIcons:
            icon = ICONS.get(v['icon']) + ' ' or '? '
        else:
            icon = ''
        tags_str = tags_str + icon + v['title'] + ' '
    return tags_str.strip()

def unlock_entry(e):
    entry_id = e[0]; entry = e[1]
    if entry['export'] is True:
        handle_exception('UNLOCK_ENTRY_ERROR')
    entry['export'] = True
    try:   
        plain_nonce = client.getDecryptedNonce(entry)
    except Exception as ex:
        handle_exception('TREZOR_DEVICE_ERROR', ex)    
    try:
        entry['password']['data'] = crypto.decryptEntryValue(plain_nonce, entry['password']['data'])
        entry['safe_note']['data'] = crypto.decryptEntryValue(plain_nonce, entry['safe_note']['data'])
    except Exception as ex:
        handle_exception('DECRYPT_ENTRY_ERROR', ex)
    return e

def lock_entry(e):
    entry_id = e[0]; entry = e[1]
    if entry['export'] is False:
        handle_exception('LOCK_ENTRY_ERROR')
    entry['export'] = False
    try:
        entropy = client.getEntropy(NONCE_ENTROPY_BYTES)
        entry['nonce'] = client.getEncryptedNonce(entry, entropy)
        plain_nonce = client.getDecryptedNonce(entry)
    except Exception as ex:
        handle_exception('TREZOR_DEVICE_ERROR', ex)
    try:
        iv_pwd = client.getEntropy(ENC_ENTROPY_BYTES)
        entry['password']['data'] = crypto.encryptEntryValue(plain_nonce, json.dumps(entry['password']['data']), iv_pwd)
        iv_secret = client.getEntropy(ENC_ENTROPY_BYTES)
        entry['safe_note']['data'] = crypto.encryptEntryValue(plain_nonce, json.dumps(entry['safe_note']['data']), iv_secret)
    except Exception as ex:
        handle_exception('ENCRYPT_ENTRY_ERROR', ex)
    return e

def insert_entry(e):
    global entries
    entry_id = e[0]; entry = e[1]
    if entry['export'] is True:
        e = lock_entry(e)
    if entry_id == '':
        for k in entries.keys():
            entry_id = str(int(k) + 1)
        if entry_id == '':
            entry_id = '0'
    entries.update( {entry_id : entry} )

def edit_entry(e):#TODO don't show <All>
    entry = e[1]
    if entry['export'] is False:
        e = unlock_entry(e)
    edit_json = {'item/url*':entry['title'], 'title':entry['note'], \
         'username':entry['username'], 'password':entry['password']['data'], \
             'secret':entry['safe_note']['data'], 'tags': {'inUse': \
                    [v.get('title') for k,v in get_tags_from_entry(e).items()], \
                        'chooseFrom': [v.get('title') for k,v in tags.items()]}}
    edit_json = click.edit(json.dumps(edit_json, indent=4), require_save=True, extension='.json')
    if edit_json:
        try:
            edit_json = json.loads(edit_json)
        except Exception as ex:
            handle_exception('EDIT_ERROR', ex)
        if 'title' not in edit_json or 'item/url*' not in edit_json or 'username' not in edit_json or 'password' not in edit_json or 'secret' not in edit_json or 'tags' not in edit_json or 'inUse' not in edit_json['tags']:
            handle_exception('EDIT_ERROR')
        if not isinstance(edit_json['item/url*'],str) or not isinstance(edit_json['title'],str) or not isinstance(edit_json['username'],str) or not isinstance(edit_json['password'],str) or not isinstance(edit_json['secret'],str):
            handle_exception('EDIT_ERROR')
        if edit_json['item/url*'] == '':
            handle_exception('ITEM_FIELD_ERROR')
        entry['title'] = edit_json['item/url*']; entry['note'] = edit_json['title']; entry['username'] = edit_json['username']; entry['password']['data'] = edit_json['password']; entry['safe_note']['data'] = edit_json['secret']
        entry['tags'] = []
        for t in edit_json['tags']['inUse']:
            for k, v in tags.items():
                if t == v['title'] and t != 'All':
                    entry['tags'].append(int(k))
        #TODO dict(filter(lambda t: t in tags['title'] and t != 'All', ts))
        return lock_entry(e)
    handle_exception('ABORTED')

def edit_tag(t):
    tag_id = t[0]; tag = t[1]
    edit_json = {'title': tag['title'], 'icon': {'inUse':tag['icon'], 'chooseFrom:':[k for k,v in ICONS.items()]}}
    edit_json = click.edit(json.dumps(edit_json, indent=4), require_save=True, extension='.json')
    if edit_json:
        try:
            edit_json = json.loads(edit_json)
        except Exception as ex:
            handle_exception('EDIT_ERROR', ex)
        if 'title' not in edit_json or edit_json['title'] == '' or not isinstance(edit_json['title'],str):
            handle_exception('TITLE_FIELD_ERROR')
        if 'icon' not in edit_json or 'inUse' not in edit_json['icon'] or edit_json['icon']['inUse'] not in ICONS or not isinstance(edit_json['icon']['inUse'],str):
            handle_exception('WRONG_ICON_ERROR', edit_json['icon']['inUse'])
        tag['title'] = edit_json['title']; tag['icon'] = edit_json['icon']['inUse'] 
        return t
    handle_exception('ABORTED')

def insert_tag(t):
    global tags
    tag_id = t[0]; tag = t[1]
    if tag_id == '':
        for k in tags.keys():
            tag_id = str(int(k) + 1)
        if tag_id == '':
            tag_id = '0'
    tags.update( {tag_id : tag} )

def remove_tag(t, recursiv=False):
    global db_json; global entries
    tag_id = t[0]; tag = t[1]
    if tag_id == '0':
        handle_exception('REMOVE_ALL_TAG_ERROR')
    del db_json['tags'][tag_id]
    es = get_entries_by_tag(tag_id)
    for e in es:
        if recursiv is True:
            del db_json['entries'][e[0]]
        else:   
            entries[e]['tags'].remove(int(tag_id))


'''
CLI Helper Methods
'''

def tab_completion_entries(ctx, args, incomplete):
    load_config()
    unlock_storage() # TODO read tmp file
    tabs = []
    for k,v in tags.items():
        es = get_entries_by_tag(k)
        for kk,vv in es.items():
            tabs.append(v['title'] + '/' + vv['title'] + ':' + vv['username'] + '#' + kk)
    return [k for k in tabs if incomplete.lower() in k.lower()]

def tab_completion_tags(ctx, args, incomplete):
    load_config()
    unlock_storage() # TODO read tmp file
    tabs = []
    for t in tags:
        tabs.append(tags[t]['title'] + '/')
    return [k for k in tabs if incomplete.lower() in k.lower()]

def tab_completion_config(ctx, args, incomplete):
    load_config()
    return [k for k in CONFIG if incomplete.lower() in k]

class EntryName(click.ParamType):
    def convert(self, value, param, ctx):
        tag = ''; title = ''; username = ''; entry_id = ''
        if not isinstance(value,str):
            return (tag, title, username, entry_id)
        if value.startswith('#') or '#' in value:
            entry_id = value.split('#')[1]
        elif not '/' in value:
            tag = title = value
        else:
            if not ':' in value:
                tag = value.split('/')[0]
                title = value.split('/')[1]
            else:
                tag = value.split('/')[0]
                username = value.split(':')[1]
                title = value.split('/')[1].split(':')[0]
        return (tag, title, username, entry_id)

class TagName(click.ParamType):
    def convert(self, value, param, ctx):
        tag = value.split('/')[0]
        if not isinstance(value,str):
            return ''
        return tag

class SettingValue(click.ParamType):
    def convert(self, value, param, ctx):
        if not isinstance(value,str):
            raise IOError()
        return value

class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)


'''
CLI Commands
'''

@click.group(cls=AliasedGroup, invoke_without_command=True)
@click.option('--debug', is_flag=True, help='Show debug info')
@click.version_option()
@click.pass_context
def cli(ctx, debug):
    '''
    ------------------------------------\n
            tpass\n  
    ------------------------------------\n
    CLI for Trezor Password Manager\n

    WARNING:
    Untested Beta Software! - Do not use it\n
    Not from Satoshilabs!

    @author: makk4 <manuel.kl900@gmail.com>\n
    https://github.com/makk4/tpass
    '''

    write_lockfile()
    start_logging(debug)
    load_config()
    if ctx.invoked_subcommand is None:
        ctx = list_cmd()

@cli.command(name='init')
@click.option('--path', '-p', default=DEFAULT_PATH, type=click.Path(), help='path to database')
@click.option('--cloud', '-c', default='offline', type=click.Choice(['dropbox', 'googledrive', 'git', 'offline']), help='cloud provider: <dropbox> <googledrive> <git>')
@click.option('--no-disk', '-n', is_flag=True, help='do not store metadata on disk')
def init_cmd(path, cloud, no_disk):
    '''Initialize new password store'''
    global CONFIG; global pwd_file; global tmp_file
    CONFIG['path'] = path; CONFIG['storeMetaDataOnDisk'] = not no_disk
    click.echo('Untested Beta Software! - Do not use it')
    if cloud == 'googledrive':
        CONFIG['path'] = GOOGLE_DRIVE_PATH
    elif cloud == 'dropbox':
        CONFIG['path'] = DROPBOX_PATH
    if not os.path.exists(CONFIG['path']):
        os.makedirs(CONFIG['path'])
    if len(os.listdir(CONFIG['path'])) != 0 or CONFIG['fileName'] != '':
        handle_exception('INIT_ERROR', CONFIG['path'] + ' is not empty, not initialized')
    if cloud == 'git':
        CONFIG['useGit'] = True
        subprocess.call('git init', cwd=CONFIG['path'], shell=True)
    try:
        keys = client.getTrezorKeys()
        iv = client.getEntropy(ENC_ENTROPY_BYTES)
        CONFIG['fileName'] = keys[0]; encKey = keys[2]
    except Exception as ex:
        handle_exception('TREZOR_KEY_ERROR', ex)
    pwd_file = os.path.join(CONFIG['path'], CONFIG['fileName'])
    write_config()
    load_config()
    try:
        crypto.encryptStorage(db_json, pwd_file, encKey, iv)
    except Exception as ex:
        handle_exception('PASSWORD_FILE_ENCRYPT_ERROR', ex)
    unlock_storage()
    if cloud == 'git':
        subprocess.call('git add *.pswd', cwd=CONFIG['path'], shell=True)
        subprocess.call('git commit -m "initial commit"', cwd=CONFIG['path'], shell=True)
    click.echo('password store initialized in ' + CONFIG['path'])
    clean_exit()

@cli.command(name='find')
@click.argument('search-string', type=click.STRING, nargs=1)
def find_cmd(search_string):
    '''List entries and tags that match names'''
    unlock_storage()
    es = dict(filter(lambda e: search_string.lower() in e[1]['title'].lower() or search_string.lower() in e[1]['note'].lower() or search_string.lower() in e[1]['username'].lower(), entries.items()))
    ts = dict(filter(lambda t: search_string.lower() in t[1]['title'].lower(), tags.items()))
    print_entries(es)
    print_tags(ts)
    clean_exit()

@cli.command(name='grep')
@click.option('--case-insensitive', '-i', is_flag=True, help='not case sensitive search')
@click.argument('search-string', type=click.STRING, nargs=1)
def grep_cmd(search_string, case_insensitive):
    '''Search for search_strings in decrypted entries'''
    unlock_storage()
    for k, v in entries.items():
        v = unlock_entry((k,v))[1]
        for kk, vv in v.items():
            if kk in ['title', 'note', 'usersearch_string']:
                if search_string.lower() in vv.lower():
                    click.echo(click.style(v['title'] + ':', bold=True) + click.style(v['usersearch_string'], bold=True, fg='green') + click.style('#' + k, bold=True, fg='magenta') + click.style('//<' + kk + '>//: ', fg='blue') + vv)
        if search_string.lower() in v['password']['data'].lower():    
            click.echo(click.style(v['title'] + ':', bold=True) + click.style(v['usersearch_string'], bold=True, fg='green') + click.style('#' + k, bold=True, fg='magenta') + click.style('//<password>//: ', fg='blue') + v['password']['data'])
        if search_string.lower() in v['safe_note']['data'].lower():  
            click.echo(click.style(v['title'] + ':', bold=True) + click.style(v['usersearch_string'], bold=True, fg='green') + click.style('#' + k, bold=True, fg='magenta') + click.style('//<secret>//: ', fg='blue') + v['safe_note']['data'])
    clean_exit()

@cli.command(name='list')
@click.argument('tag-string', default='', type=TagName(), nargs=1, autocompletion=tab_completion_tags)
def list_cmd(tag_string):
    '''List entries by tag'''
    unlock_storage()
    if tag_string == '':
        print_tags(tags, True)
    else:
        t = get_tag(tag_string)
        if t is not None:
            print_tags({t[0] : t[1]}, True)
    clean_exit()
    
@cli.command(name='show')
@click.option('--secrets', '-s', is_flag=True, help='show password and secret notes')
@click.option('--json', '-j', is_flag=True, help='json format')
@click.argument('entry-strings', type=EntryName(), nargs=-1, autocompletion=tab_completion_entries)
def show_cmd(entry_strings, secrets, json):
    '''Show entries'''
    unlock_storage()
    for name in entry_strings:
        e = get_entry(name)
        if e is None:
            continue
        entry = e[1]; entry_id = e[0]

        if not secrets:
            pwd = '********'
            safeNote = '********'
        else:
            e = unlock_entry(e)
            pwd = entry['password']['data']
            safeNote = entry['safe_note']['data']
        if json:
            click.echo(e)
        else:
            ts = {}
            for i in entry['tags']:
                ts[i] = tags.get(str(i))

            click.echo('-------------------'+ click.style(' (' + entry_id + ')', bold=True, fg='magenta') + '\n' +
                click.style('item/url*: ', bold=True) + entry['title'] + '\n' +
                click.style('title:     ', bold=True) + entry['note'] + '\n' +
                click.style('username:  ', bold=True) + entry['username'] + '\n' +
                click.style('password:  ', bold=True) + pwd + '\n' +
                click.style('secret:    ', bold=True) + safeNote  + '\n' +
                click.style('tags:      ', bold=True) + tags_to_string(get_tags_from_entry(e), CONFIG['showIcons']))
    clean_exit()

@cli.command(name='clip')
@click.option('--user', '-u', is_flag=True, help='copy user')
@click.option('--url', '-i', is_flag=True, help='copy item/url*')
@click.option('--secret', '-s', is_flag=True, help='copy secret')
@click.argument('entry-string', type=EntryName(), nargs=1, autocompletion=tab_completion_entries)
def clip_cmd(user, url, secret, entry_string):
    '''Decrypt and copy line of entry to clipboard'''
    unlock_storage()
    e = get_entry(entry_string)
    if e is None:
        clean_exit()
    entry = e[1]; entry_id = e[0]
    if user:
        pyperclip.copy(entry['username'])
    elif url:
        pyperclip.copy(entry['title'])
    else:
        e = unlock_entry(e)
        if secret:
            pyperclip.copy(entry['safe_note']['data'])
        else:
            pyperclip.copy(entry['password']['data'])
        clear_clipboard()
    clean_exit()     
    
@cli.command(name='generate')# TODO callback eager options
@click.option('--insert', '-i', default=None, type=EntryName(), nargs=1, autocompletion=tab_completion_entries)
@click.option('--clip', '-c', is_flag=True, help='copy to clipboard')
@click.option('--type', '-t', 'type_', default='password', type=click.Choice(['password', 'wordlist', 'pin']), help='type of password')
@click.option('--seperator', '-s', default=' ', type=click.STRING, help='seperator for passphrase')
@click.option('--force', '-f', is_flag=True, help='force without confirmation')
@click.option('--entropy', '-d', is_flag=True, help='entropy from trezor device and host mixed')
@click.argument('length', default=15, type=int)
def generate_cmd(length, insert, type_, clip, seperator, force, entropy):
    '''Generate new password'''
    global db_json
    if (length < 6 and type_ == 'password') or (length < 3 and type_ == 'wordlist') or (length < 4 and type_ == 'pin'):
        if not click.confirm('Warning: ' + length + ' is too short for password with type ' + type_ + '. Continue?'):
            handle_exception('ABORTED')
    if entropy:
        entropy = client.getEntropy(length)
    else:
        entropy = None
    if type_ == 'wordlist':
        words = load_wordlist()
        pwd = crypto.generatePassphrase(length, words, seperator)
    elif type_ == 'pin':
        pwd = crypto.generatePin(length)
    elif type_ == 'password':
        pwd = crypto.generatePassword(length)
    if insert:
        unlock_storage()
        e = get_entry(insert)
        if e is None:
            clean_exit()
        e = unlock_entry(e)
        e[1]['password']['data'] = pwd
        e = edit_entry(e)
        insert_entry(e)
        if force or click.confirm('Insert password in entry ' + click.style(e[1]['title'], bold=True)):
            save_storage()
    if clip:
        pyperclip.copy(pwd)
        clear_clipboard()
    else:
        click.echo(pwd)
    clean_exit()

@cli.command(name='remove')
@click.option('--tag', '-t', type=TagName(), help='remove tag', nargs=1, autocompletion=tab_completion_tags)
@click.option('--recursive', '-r', is_flag=True, help='recursive remove entries within tag')
@click.option('--force', '-f', is_flag=True, help='force without confirmation')
@click.argument('entry-strings', type=EntryName(), nargs=-1, autocompletion=tab_completion_entries)
def remove_cmd(entry_strings, tag, recursive, force):# TODO make options TRU/FALSE tag
    '''Remove entry or tag'''
    unlock_storage()
    global db_json
    if tag:
        t = get_tag(tag)
        if t is not None:
            remove_tag(t, recursive)
            if force or click.confirm('Delete tag: ' + click.style(t[1]['title'], bold=True)):
                save_storage()
    else:
        names = []
        for name in entry_strings:
            e = get_entry(name)
            if e is not None:
                names.append(entries[e[0]]['title'])
                del db_json['entries'][e[0]]
        if force or click.confirm('Delete entries ' + click.style(', '.join(names), bold=True)):
            save_storage()
    clean_exit()

@cli.command(name='insert')
@click.option('--tag', '-t', is_flag=True, help='insert tag')
@click.option('--direct', '-d', is_flag=True, help='insert without open editor')
@click.option('--title', default='',  type=click.STRING, help='title')
@click.option('--user', default='', type=click.STRING, help='user')
@click.option('--pwd', default='', type=click.STRING, help='password')
@click.option('--secret', default='', type=click.STRING, help='secret')
def insert_cmd(tag, direct, title, user, pwd, secret):
    '''Insert entry or tag'''
    unlock_storage()
    if tag:
        t = ('',{'title': title, 'icon': 'home'})
        if direct is False:
            t = edit_tag(t)
        insert_tag(t)
        save_storage()
    else:
        e = ('',{'title': title, 'username': user, 'password': {'type': 'Buffer', 'data': pwd}, 'nonce': '', 'tags': [], 'safe_note': {'type': 'Buffer', 'data': secret}, 'note': '', 'success': True, 'export': True})
        if direct is False:
            e = edit_entry(e)
        insert_entry(e)
        save_storage()
    clean_exit()

@cli.command(name='edit')
@click.option('--tag', '-t', type=TagName(), default='', nargs=1, help='edit tag', autocompletion=tab_completion_tags)
@click.argument('entry-string', type=EntryName(), default='', nargs=1, autocompletion=tab_completion_entries)
def edit_cmd(entry_string, tag):#TODO option --entry/--tag with default
    '''Edit entry or tag'''
    unlock_storage()
    if tag:
        t = get_tag(tag)
        if t is not None:
            t = edit_tag(t)
            insert_tag(t)
            save_storage()
    else:
        e = get_entry(entry_string)
        if e is not None:
            e = edit_entry(e)
            insert_entry(e)
            save_storage()
    clean_exit()

@cli.command(name='git')
@click.argument('commands', type=click.STRING, nargs=-1)
def git_cmd(commands):
    '''Call git commands on password store'''
    if CONFIG['useGit'] is True:
        subprocess.call('git '+ ' '.join(commands), cwd=CONFIG['path'], shell=True)
    else:
        click.echo('Git is not enabled')
    clean_exit()

@cli.command(name='config')
@click.option('--edit', '-e', is_flag=True, help='edit config')
@click.option('--reset', '-r', is_flag=True, help='reset config')
@click.argument('setting-name', type=click.STRING, default='', nargs=1, autocompletion=tab_completion_config)
@click.argument('setting-value', type=SettingValue(), default='', nargs=1) # TODO autocompletion based on setting-name
def config_cmd(edit, reset, setting_name, setting_value):
    '''Configuration settings'''
    global CONFIG
    if edit:
        click.edit(filename=CONFIG_FILE, require_save=True)
    elif reset:
        if os.path.isfile(CONFIG_FILE):
            if click.confirm('Reset config?'):
                os.remove(CONFIG_FILE)
    else:
        if CONFIG.get(setting_name):
            CONFIG[setting_name] = setting_value
            write_config()
    clean_exit()

@cli.command(name='unlock')
def unlock_cmd():
    '''Unlock and write metadata to disk'''
    unlock_storage()
    clean_exit()

@cli.command(name='lock')
def lock_cmd():
    '''Remove metadata from disk'''
    if os.path.isfile(tmp_file):
        os.remove(tmp_file)
        click.echo(click.style('metadata deleted: ', bold=True) + tmp_file)
    else:
        click.echo(click.style('nothing to delete', bold=True)) 
    clean_exit()

@cli.command(name='export')# TODO CSV
@click.option('--path', '-p', default=os.path.expanduser('~'), type=click.Path(), help='path for export')
@click.option('--file-format', '-f', default='json', type=click.Choice(['json', 'csv']), help='file format')
def export_cmd(path, file_format):
    '''Export password store'''
    global entries
    unlock_storage()
    export_passwords = {}
    with click.progressbar(entries.items(), label='Decrypt entries', show_eta=False, fill_char='#', empty_char='-') as bar:
        for e in bar:
            e = unlock_entry(e)
            export_passwords.update( {str(e[0]) : {'item/url*':e[1]['title'], 'title':e[1]['note'], 'username':e[1]['username'], 'password':e[1]['password']['data'], 'secret':e[1]['safe_note']['data'], 'tags':tags_to_string(get_tags_from_entry(e), False)} } )
    if file_format == 'json':
        with open(os.path.join(CONFIG_PATH, 'export.json'), 'w', encoding='utf8') as f:
            json.dump(export_passwords, f)
    elif file_format == 'csv':
        edit_json = {'0': 'item/url*', '1': 'title', '2:':'username', '3:':'password', '4:':'username', '5:':'secret', '6:':'tags'}
        edit_json = click.edit(json.dumps(edit_json, indent=4), require_save=True, extension='.json')
    clean_exit()

@cli.command(name='import')# TODO CSV; check for file extension before parsing
@click.argument('path-to-file', type=click.Path(), nargs=1)
def import_cmd(path_to_file):
    '''Import password store'''
    unlock_storage()
    try:
        if os.path.isfile(path_to_file):
            with open(path_to_file) as f:
                es = json.load(f)
    except Exception as ex:
        handle_exception('IMPORT_ERROR', ex)
    with click.progressbar(es.items(), label='Decrypt entries', show_eta=False, fill_char='#', empty_char='-') as bar:    
        for k,v in bar:
            if 'item/url*' not in v or 'username' not in v or 'password' not in v or 'secret' not in v:
                handle_exception('IMPORT_ERROR')
            if not isinstance(v['item/url*'],str) or not isinstance(v['username'],str) or not isinstance(v['password'],str) or not isinstance(v['secret'],str):
                handle_exception('IMPORT_ERROR')
            if v['item/url*'] == '':
                handle_exception('ITEM_FIELD_ERROR')
            e = ('',{'title': v['item/url*'], 'username': v['username'], 'password': {'type': 'Buffer', 'data': v['password']}, 'nonce': '', 'tags': [], 'safe_note': {'type': 'Buffer', 'data': v['secret']}, 'note': v['title'], 'success': True, 'export': True})
            insert_entry(e)
            # TODO insert new tags from entries 
    save_storage()
    clean_exit()


ALIASES = {
    'cp': clip_cmd,
    'copy': clip_cmd,
    'conf': config_cmd,
    'search': find_cmd,
    'create': insert_cmd,
    'ins': insert_cmd,
    'ls': list_cmd,
    'del': remove_cmd,
    'delete': remove_cmd,
    'rm': remove_cmd,
    'cat': show_cmd,
}

ERROR_CODES = {
    'CONFIG_READ_ERROR':{
        'message':'Config read error: ' + CONFIG_PATH,
        'code':1
    },
    'CONFIG_PARSE_ERROR':{
        'message':'Config parse error: ' + CONFIG_PATH,
        'code':2
    },
    'CONFIG_WRITE_ERROR':{
        'message':'Config write error: ' + CONFIG_PATH,
        'code':3
    },
    'NOT_INITIALIZED':{
        'message':'Password store is not initialized',
        'code':4
    },
    'PASSWORD_UNLOCK_READ_ERROR':{
        'message':'Password store unlocking error',
        'code':5
    },
    'LOCKFILE_DELETED':{
        'message':'Lockfile deleted, aborted',
        'code':6
        },
    'LOCKFILE_CHANGED':{
        'message':'Lockfile changed, aborted',
        'code':7
    },
    'PASSWORD_FILE_CHANGED':{
        'message':'Password file changed, aborted',
        'code':8
    },
    'DICEWARE_FILE_PARSE_ERROR':{
        'message':'Wordlist parse error: ' + DICEWARE_FILE,
        'code':9
    },
    'TREZOR_DEVICE_ERROR':{
        'message':'Error while accessing trezor device',
        'code':10
    },
    'TREZOR_KEY_ERROR':{
        'message':'Error while getting keys from trezor device',
        'code':11
    },
    'EDIT_ERROR':{
        'message':'Edit gone wrong',
        'code':12
    },
    'ITEM_FIELD_ERROR':{
        'message':'item/url* field is mandatory',
        'code':13
    },
    'WRONG_TAG_ERROR':{
        'message':'Tag not exist: ',
        'code':14
    },
    'TITLE_FIELD_ERROR':{
        'message':'Title* field is mandatory',
        'code':15
    },
    'WRONG_ICON_ERROR':{
        'message':'Icon not exists: ',
        'code':16
    },
    'ABORTED':{
        'message':'Aborted',
        'code':17
    },
    'IMPORT_ERROR':{
        'message':'Import gone wrong',
        'code':18
    },
    'INIT_ERROR':{
        'message':'Directory not empty, not initialized',
        'code':19
    },
    'UNLOCK_ENTRY_ERROR':{
        'message':'Error while unlocking entry',
        'code':20
    },
    'PASSWORD_FILE_ENCRYPT_ERROR':{
        'message':'Error while encrypting password store',
        'code':21
    },
    'INSERT_ENTRY_ERROR':{
        'message':'Error while inserting entry',
        'code':22
    },
    'ENCRYPT_ENTRY_ERROR':{
        'message':'Error while encrypting entry',
        'code':23
    },
    'DECRYPT_ENTRY_ERROR':{
        'message':'Error while decrypting entry',
        'code':24
    },
    'LOCK_ENTRY_ERROR':{
        'message':'Error while locking entry',
        'code':25
    },
    'REMOVE_ALL_TAG_ERROR':{
        'message':'Cannot remove <all> tag',
        'code':26
    },
}