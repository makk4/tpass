import click
from src import trezor
from src import crypto

ICONS = {'home':u'\U0001f3e0', 'person-stalker':u'\U0001F469\u200D\U0001F467', 'social-bitcoin':'₿', 'person':u'\U0001F642', 'star':u'\u2B50', 'flag':u'\U0001F3F3', 'heart':u'\u2764', 'settings':u'\u2699', 'email':u'\u2709', 'cloud':u'\u2601', 'alert-circled':u'\u26a0', 'android-cart':u'\U0001f6d2', 'image':u'\U0001F5BC', 'card':u'\U0001f4b3', 'earth':u'\U0001F310', 'wifi':u'\U0001f4f6'}
client = None

def get_client():
    global client
    if client is None:
        client = trezor.getTrezorClient()

class PasswordStore(object):
    tags = {}
    entries = {}
    db_json = {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': tags, 'entries': entries}

    def __init__(self, entries={}, tags={'0': {'title': 'All', 'icon': 'home'},}):
        self.entries = entries
        self.tags = tags
        self.db_json['entries'] = entries; self.db_json['tags'] = tags

    @classmethod
    def fromFile(cls, filepath):
        get_client()
        keys = trezor.getTrezorKeys(client)
        db_json = crypto.decryptStorage(filepath, keys[2])
        if 'entries' not in db_json or 'tags' not in db_json:
            raise ValueError('Parse error while loading password file')
        return cls(db_json['entries'], db_json['tags'])

    def get_encrypted_db(self, filepath):
        get_client()
        keys = trezor.getTrezorKeys(client)
        encKey = keys[2]
        iv = trezor.getEntropy(client, 12)
        crypto.encryptStorage(self.db_json, filepath, encKey, iv)

    def get_entry(self, names):
        tag = names[0]; note = names[1]; username = names[2]; entry_id = names[3]
        if entry_id != '' and self.entries.get(entry_id):
            return entry_id, self.entries[entry_id]
        for k, v in self.entries.items():
            if note == v['note']:
                if username == '' or username == v['username']:
                    return k, v
        logging.info(', '.join(names) + ' is not in the password store')
        return None

    def get_tag(self, tag_name):
        for k, v in self.tags.items():
            if tag_name == v['title']:
                return k, v
        logging.info(tag_name + ' is not a tag in the password store')
        return None

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
            handle_exception('Error while unlocking entry', 15)
        entry['success'] = False; entry['export'] = True
        try:   
            plain_nonce = trezor.getDecryptedNonce(client, entry)
        except Exception as ex:
            handle_exception('Error while accessing trezor device', 2, ex)    
        try:
            entry['password']['data'] = crypto.decryptEntryValue(plain_nonce, entry['password']['data'])
            entry['safe_note']['data'] = crypto.decryptEntryValue(plain_nonce, entry['safe_note']['data'])
            entry['password']['type'] = 'String'; entry['safe_note']['type'] = 'String'
            entry['success'] = True
        except Exception as ex:
            handle_exception('Error while decrypting entry', 16, ex)
        return e

    def lock_entry(self, e):
        get_client()
        entry_id = e[0]; entry = e[1]
        if entry['success'] is False or entry['export'] is False:
            handle_exception('Error while locking entry', 17)
        entry['success'] = False; entry['export'] = False
        try:
            entry['nonce'] = trezor.getEncryptedNonce(client, entry)
            plain_nonce = trezor.getDecryptedNonce(client, entry)
            iv_pwd = trezor.getEntropy(client, 12)
            iv_secret = trezor.getEntropy(client, 12)
        except Exception as ex:
            handle_exception('Error while accessing trezor device', 2, ex)
        try:
            entry['password']['data'] = crypto.encryptEntryValue(plain_nonce, json.dumps(entry['password']['data']), iv_pwd)
            entry['safe_note']['data'] = crypto.encryptEntryValue(plain_nonce, json.dumps(entry['safe_note']['data']), iv_secret)
            entry['password']['type'] = 'Buffer'; entry['safe_note']['type'] = 'Buffer'
            entry['success'] = True
        except Exception as ex:
            handle_exception('Error while encrypting entry', 18, ex)
        return e

    def insert_entry(self, e):
        entry_id = e[0]; entry = e[1]
        if entry['success'] is False or entry['export'] is True:
            handle_exception('Error while inserting entry', 19)
        if entry_id == '':
            for k in self.entries.keys():
                entry_id = str(int(k) + 1)
            if entry_id == '':
                entry_id = '0'
        self.entries.update( {entry_id : entry} )

    def insert_tag(t):
        tag_id = t[0]; tag = t[1]
        if tag_id == '':
            for k in self.tags.keys():
                tag_id = str(int(k) + 1)
            if tag_id == '':
                tag_id = '0'
        self.tags.update( {tag_id : tag} )

    def remove_tag(t, recursiv=False):
        tag_id = t[0]; tag = t[1]
        if tag_id == '0':
            handle_exception('Cannot remove <all> tag', 0)
        del self.db_json['tags'][tag_id]
        es = get_entries_by_tag(tag_id)
        for e in es:
            if recursive:
                del self.db_json['entries'][e[0]]
            else:   
                self.entries[e]['tags'].remove(int(tag_id))
    
    def remove_entrie(e):
        del self.db_json['entries'][tag_id]