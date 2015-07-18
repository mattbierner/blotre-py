import re
import requests
import urllib
from urlparse import urlunparse

DEFAULT_CONF = {
    'protocol': 'https',
    'host': 'blot.re'
}

class Blotre:
    """Main Blot're State object"""
    ROOT = '/v0/'
    API_ROOT = ROOT + 'api/'
    OAUTH2_ROOT = ROOT + 'oauth2/'

    def __init__(self, client, creds={}, userConf={}):
        self.client = client
        self.config = DEFAULT_CONF.copy()
        self.config.update(userConf)
        self.creds = creds
        
    def set_creds(self, creds):
        """Manually update the current creds."""
        self.creds = creds
        self.on_creds_changed()
        
    def on_creds_changed(self):
        pass
        
    def normalize_uri(self, uri):
        """Convert a stream path into it's normalized form."""
        urllib.quote(
            re.sub(r"\s", '+', uri.trim().toLowerCase()),
            safe='~@#$&()*!+=:;,.?/\'')
            
    def get_websocket_url(self):
        """
        Get the url for using the websocked APIs,
        both subscription and send/receive.
        """
        return ('ws' if self.config.protocol == 'http' else 'wss') + \
            '://' + config.host + '/v0/ws'
        
    def _format_url(self, relPath, query={}):
        return urlunparse((
            self.config.get('protocol'),
            self.config.get('host'),
            relPath,
            '',
            urllib.urlencode(query),
            ''))
            
# Authorization
    def get_authorization_url(self):
        """Get the authorization Url for the current client."""
        return self._format_url(
            Blotre.OAUTH2_ROOT + 'authorize',
            query = {
                'response_type': 'code',
                'client_id': self.client.get('client_id', ''),
                'redirect_uri': self.client.get('redirect_uri', '')
            })
    
    
a = Blotre({})

print a.get_authorization_url()