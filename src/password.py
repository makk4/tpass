import click
import os
try:
    import simplejson as json
except:
    import json
from src import trezor
from src import crypto

ICONS = {'home':u'\U0001f3e0', 'person-stalker':u'\U0001F469\u200D\U0001F467', 'social-bitcoin':'₿', 'person':u'\U0001F642', 'star':u'\u2B50', 'flag':u'\U0001F3F3', 'heart':u'\u2764', 'settings':u'\u2699', 'email':u'\u2709', 'cloud':u'\u2601', 'alert-circled':u'\u26a0', 'android-cart':u'\U0001f6d2', 'image':u'\U0001F5BC', 'card':u'\U0001f4b3', 'earth':u'\U0001F310', 'wifi':u'\U0001f4f6'}
ENC_ENTROPY = 12
NONCE_ENTROPY = 32

class PasswordStore(object):
    tags = {'0': {'title': 'All', 'icon': 'home'},}
    entries = {}
    db_json = {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': tags, 'entries': entries}
    client = None

    def __init__(self, entries, tags):#TODO true init
        self.entries = entries
        self.tags = tags
        self.db_json['entries'] = entries; self.db_json['tags'] = tags

    @classmethod
    def fromPwdFile(cls, filepath):
        '''init from locked password file'''
        get_client()
        keys = trezor.getTrezorKeys(self.client)
        file_name = keys[0]; encKey = keys[2]
        file_path = os.path.join(file_path , file_name)
        db_json = crypto.decryptStorage(filepath, encKey)
        if 'entries' not in db_json or 'tags' not in db_json:
            raise ValueError('Parse error while loading password file')
        return cls(db_json['entries'], db_json['tags'])
    
    @classmethod
    def fromInit(cls):#TODO from tmp file
        '''init from unlocked tmp file'''
        get_client()
        keys = trezor.getTrezorKeys(self.client)
        file_name = keys[0]; encKey = keys[2]
        return cls(cls.db_json['entries'], cls.db_json['tags']), file_name

    def write_pwd_file(self, file_path):
        get_client()
        keys = trezor.getTrezorKeys(self.client)
        file_name = keys[0]; encKey = keys[2]
        file_path = os.path.join(file_path , file_name)
        iv = trezor.getEntropy(self.client, ENC_ENTROPY)
        crypto.encryptStorage(self.db_json, file_path, encKey, iv)

    def get_entry(self, names):
        tag = names[0]; note = names[1]; username = names[2]; entry_id = names[3]
        if entry_id != '' and self.entries.get(entry_id):
            return entry_id, self.entries[entry_id]
        for k, v in self.entries.items():
            if note == v['note']:
                if username == '' or username == v['username']:
                    return k, v
        click.echo(' '.join(names) + 'not in the password store')
        return None

    def get_tag(self, tag_name):
        for k, v in self.tags.items():
            if tag_name == v['title']:
                return k, v
        click.echo(tag_name + 'is not a tag in the password store')
        return None
    
    def get_tags_from_entry(self, e):
        ts = {}
        for i in e[1]['tags']:
            ts[i] = tags.get(str(i))
        return ts

    def get_entries_by_tag(self, tag_id):#TODO optimze
        es = {}
        for k, v in self.entries.items():
            if int(tag_id) in v['tags'] or int(tag_id) == 0 and v['tags'] == []:
                es.update( {k : v} )  
        return es

    def print_entries(self, es, includeTree=False):#TODO optimze
        if includeTree:
            start = '  ' + u'\u251C' + u'\u2500' + u'\u2500' + ' '; start_end = '  ' + u'\u2514' + u'\u2500' + u'\u2500' + ' '
        else:
            start = ''; start_end = ''
        i = 0
        for k,v in es.items():
            if i == len(es)-1:
                click.echo(start_end + v['note'] + ':' + click.style(v['username'], fg='green') + click.style('#' + k, fg='magenta'))
            else:
                click.echo(start + v['note'] + ':' + click.style(v['username'], fg='green') + click.style('#' + k, fg='magenta'))
            i = i + 1

    def print_tags(self, ts, showIcons=False, includeEntries=False):#TODO optimze
        for k,v in ts.items():
            if showIcons:
                icon = ICONS.get(v['icon']) + ' ' or '? '
            else:
                icon = ''
            click.echo(icon + click.style(v['title'], bold=True , fg='blue'))
            if includeEntries:
                es = self.get_entries_by_tag(k)
                self.print_entries(es, True)

    def tags_to_string(self, ts, includeIds=False, showIcons=False):
        tags_str = ''
        for k,v in ts.items():
            if showIcons:
                icon = ICONS.get(v['icon']) + ' ' or '? '
            else:
                icon = ''
            if includeIds:
                tags_str = tags_str + k + ':' + icon + v['title'] + ' '
            else:
                tags_str = tags_str + icon + v['title'] + ' '
        return tags_str.strip()

    def unlock_entry(self, e):
        get_client()
        entry_id = e[0]; entry = e[1]
        if entry['success'] is False or entry['export'] is True:
            raise ValueError('Error while unlocking entry', 15)
        entry['success'] = False; entry['export'] = True 
        plain_nonce = trezor.getDecryptedNonce(self.client, entry)
        entry['password']['data'] = crypto.decryptEntryValue(plain_nonce, entry['password']['data'])
        entry['safe_note']['data'] = crypto.decryptEntryValue(plain_nonce, entry['safe_note']['data'])
        entry['password']['type'] = 'String'; entry['safe_note']['type'] = 'String'
        entry['success'] = True
        return e

    def lock_entry(self, e):
        get_client()
        entry_id = e[0]; entry = e[1]
        if entry['success'] is False or entry['export'] is False:
            raise ValueError('Error while locking entry')
        entry['success'] = False; entry['export'] = False
        entropy = getEntropy(self.client, NONCE_ENTROPY)
        entry['nonce'] = trezor.getEncryptedNonce(self.client, entry, entropy)
        plain_nonce = trezor.getDecryptedNonce(self.client, entry)
        iv_pwd = trezor.getEntropy(self.client, ENC_ENTROPY)
        entry['password']['data'] = crypto.encryptEntryValue(plain_nonce, json.dumps(entry['password']['data']), iv_pwd)
        iv_secret = trezor.getEntropy(self.client, ENC_ENTROPY)
        entry['safe_note']['data'] = crypto.encryptEntryValue(plain_nonce, json.dumps(entry['safe_note']['data']), iv_secret)
        entry['password']['type'] = 'Buffer'; entry['safe_note']['type'] = 'Buffer'
        entry['success'] = True
        return e

    def insert_entry(self, e):
        entry_id = e[0]; entry = e[1]
        if entry['export'] is True:
            self.lock_entry(e)
        if entry['success'] is False or entry['export'] is True:
            raise ValueError('Error while inserting entry', 19)
        if entry_id == '':
            for k in self.entries.keys():
                entry_id = str(int(k) + 1)
            if entry_id == '':
                entry_id = '0'
        self.entries.update( {entry_id : entry} )

    def insert_tag(self, t):
        tag_id = t[0]; tag = t[1]
        if tag_id == '0':
            return False
        if tag_id == '':
            for k in self.tags.keys():
                tag_id = str(int(k) + 1)
            if tag_id == '':
                tag_id = '0'
        self.tags.update( {tag_id : tag} )

    def remove_tag(self, t, recursive=False):
        tag_id = t[0]; tag = t[1]
        if tag_id == '0':
            click.echo('Cannot remove <all> tag', err=True)
            return False
        del self.db_json['tags'][tag_id]
        es = get_entries_by_tag(tag_id)
        for e in es:
            if recursive:
                del self.db_json['entries'][e[0]]
            else:   
                self.entries[e]['tags'].remove(int(tag_id))
    
    def remove_entrie(self, e):
        del self.db_json['entries'][e[0]]

    def edit_entry(e):#TODO parse tags as string, not number; don't show <All>; TODO raise custom Exceptions for all failures
        entry = e[1]
        if entry['export'] is False:
            e = self.unlock_entry(e)
        if entry['success'] is False:
            raise ValueError('EDIT_ERROR')
        entry['success'] = False
        edit_json = {'item/url*':entry['note'], 'title':entry['title'], 'username':entry['username'], 'password':entry['password']['data'], 'secret':entry['safe_note']['data'], 'tags': {'inUse':entry['tags'], 'chooseFrom': tags_to_string(tags, True, False)}}
        edit_json = click.edit(json.dumps(edit_json, indent=4), require_save=True, extension='.json')
        if edit_json:
            try:
                edit_json = json.loads(edit_json)
            except Exception as ex:
                raise ValueError(ex)
            if 'title' not in edit_json or 'item/url*' not in edit_json or 'username' not in edit_json or 'password' not in edit_json or 'secret' not in edit_json or 'tags' not in edit_json or 'inUse' not in edit_json['tags']:
                raise ValueError('EDIT_ERROR')
            if not isinstance(edit_json['item/url*'],str) or not isinstance(edit_json['title'],str) or not isinstance(edit_json['username'],str) or not isinstance(edit_json['password'],str) or not isinstance(edit_json['secret'],str):
                raise ValueError('EDIT_ERROR')
            if edit_json['item/url*'] == '':
                raise ValueError('ITEM_FIELD_ERROR')
            entry['note'] = edit_json['item/url*']; entry['title'] = edit_json['title']; entry['username'] = edit_json['username']; entry['password']['data'] = edit_json['password']; entry['safe_note']['data'] = edit_json['secret']
            for i in edit_json['tags']['inUse']:
                if str(i) not in tags:
                    raise ValueError('WRONG_TAG_ERROR')
            if 0 in edit_json['tags']['inUse']:
                edit_json['tags']['inUse'].remove(0)
            entry['tags'] = edit_json['tags']['inUse']
            entry['success'] = True
            return self.lock_entry(e)
        return None # TODO handle exit on main module

    def edit_tag(t):
        tag_id = t[0]; tag = t[1]
        if tag_id == '0':
            raise ValueError('All not editable')
        edit_json = {'title*': tag['title'], 'icon': {'inUse':tag['icon'], 'chooseFrom:':', '.join(ICONS)}}
        edit_json = click.edit(json.dumps(edit_json, indent=4), require_save=True, extension='.json')
        if edit_json:
            try:
                edit_json = json.loads(edit_json)
            except Exception as ex:
                raise ValueError('EDIT_ERROR')
            if 'title*' not in edit_json or edit_json['title*'] == '' or not isinstance(edit_json['title*'],str):
                raise ValueError('TITLE_FIELD_ERROR')
            if 'icon' not in edit_json or 'inUse' not in edit_json['icon'] or edit_json['icon']['inUse'] not in ICONS or not isinstance(edit_json['icon']['inUse'],str):
                raise ValueError('WRONG_ICON_ERROR')
            tag['title'] = edit_json['title*']; tag['icon'] = edit_json['icon']['inUse'] 
            return t
        return None
    
    def get_client():
        if self.client is None:
            self.client = trezor.getTrezorClient()