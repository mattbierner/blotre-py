import re
import requests
import urllib
from urlparse import urlunparse

import logging


DEFAULT_CONF = {
    'protocol': 'https',
    'host': 'blot.re'
}

def _extend(dict1, dict2):
    extended = dict1.copy()
    extended.update(dict2)
    return extended


class EndpointError(Exception):
    def __init__(self, error, error_description):
        self.error = error
        self.error_description = error_description

class Blotre:
    """Main Blot're State object"""
    ROOT = '/v0/'
    API_ROOT = ROOT + 'api/'
    OAUTH2_ROOT = ROOT + 'oauth2/'

    JSON_HEADERS = {
        'accepts': 'application/json',
        'content-type': 'application/json'
    }

    def __init__(self, client, creds={}, config={}):
        self.client = client
        self.config = _extend(DEFAULT_CONF, config)
        self.creds = creds
        
    def set_creds(self, creds):
        """Manually update the current creds."""
        self.creds = creds
        self.on_creds_changed()
        return self
        
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
    
    def get_redeem_url(self):
        """
        Get the Url where a user can redeem a onetime code
        for a disposable client.
        """
        return self._format_url(Blotre.OAUTH2_ROOT + 'redeem')
            
    def _access_token_endpoint(self, grantType, extraParams={}):
        """Base exchange of data for an access_token"""
        response = requests.post(
            self._format_url(Blotre.OAUTH2_ROOT + 'access_token'),
            data = _extend({
                'grant_type': grantType,
                'client_id': self.client.get('client_id', ''),
                'client_secret': self.client.get('client_secret', ''),
                'redirect_uri': self.client.get('redirect_uri', '')
            }, extraParams))
        
        data = response.json()
        if 'error' in data or 'error_description' in data:
            raise EndpointError(
                data.get('error', ''),
                data.get('error_description', ''))
        else:
            return self.set_creds(data)
            
    def redeem_authorization_code(self, code):
        """
        Exchange an authorization code for a new access token.
        If successful, update client to use these credentials.
        """
        return self._access_token_endpoint('authorization_code', {
            'code': code
        })

#
    def _make_request(self, type, path, args, noRetry=False):
        response = getattr(requests, type)(path, **args)
    
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            if not noRetry and self._is_expired_response(response) \
              and 'refresh_token' in self.creds:
                self.redeemRefreshToken()
                
                
    def get(self, path, query={}):
        return self._make_request('get',
            self._format_url(Blotre.API_ROOT + path, query=query), {
                'headers': Blotre.JSON_HEADERS
            })

    
a = Blotre({
    'client_id': '55614f0630042c617481d7c3',
    'client_secret': 'YTY1Njg2MDctZTdjYy00ODlhLWFkNmYtNjkzYjI3N2M0MDRl',
    'redirect_uri': 'http://localhost:50000',
}, config = {
    'protocol': 'http',
    'host': 'localhost:9000'
},
creds = {
    'access_token': 'OTU2NTQ5YzMtYjYzOC00ZGFmLWIzNWItOWVjYjZkMTNjODdl'
})


logging.basicConfig() 
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

print a.get_authorization_url()

#print a.redeem_authorization_code("MzRlMzg3YWMtNTVmYy00NjUwLTg4OTUtYmNmYzIyNWQ4ZWU1")
#print a.creds

print a.get('stream')