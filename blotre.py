import json
import os
import re
import requests
import urllib
from urlparse import urlunparse


_JSON_HEADERS = {
    'accepts': 'application/json',
    'content-type': 'application/json'
}

ROOT = '/v0/'
API_ROOT = ROOT + 'api/'
OAUTH2_ROOT = ROOT + 'oauth2/'


DEFAULT_CONFIG = {
    'protocol': 'https',
    'host': 'blot.re',
}

def _extend(dict1, dict2):
    extended = dict1.copy()
    extended.update(dict2)
    return extended

class TokenEndpointError(Exception):
    """
    Error communicating with the token endpoint.
    """ 
    def __init__(self, error, error_description):
        self.error = error
        self.error_description = error_description
        super(TokenEndpointError, self).__init__(
            "[%s] %s" % (self.error, self.error_description))
        
def _token_error_from_data(data):
    return TokenEndpointError(
        data.get('error', ''),
        data.get('error_description', ''))

class RestError(Exception):
    """
    Error response from one of the REST APIS.
    """ 
    def __init__(self, status_code, error_description, details):
        self.status_code = status_code
        self.error_description = error_description
        self.details = details
        super(RestError, self).__init__(
            "[%s] %s" % (self.status_code, self.error_description))

def _is_error_response(body):
    return body.get('type', '') is 'Error' or 'error' in body

def _rest_error_from_response(response):
    body = response.json()
    print body
    return RestError(
        response.status_code,
        body['error'],
        body.get('details', None))

def _format_url(config, relPath, query={}):
    return urlunparse((
        config.get('protocol'),
        config.get('host'),
        relPath,
        '',
        urllib.urlencode(query),
        ''))

class Blotre:
    """
    Main Blot're flow object.
    """
    def __init__(self, client, creds={}, config={}):
        self.client = client
        self.config = _extend(DEFAULT_CONFIG, config)
        self.creds = creds
        
    def set_creds(self, creds):
        """Manually update the current creds."""
        self.creds = creds
        self.on_creds_changed(creds)
        return self
        
    def on_creds_changed(self, newCreds):
        """
        Overridable function called when the creds change
        """
        pass
        
    def normalize_uri(self, uri):
        """Convert a stream path into it's normalized form."""
        return urllib.quote(
            re.sub(r"\s", '+', uri.strip().lower()),
            safe = '~@#$&()*!+=:),.?/\'')
    
    def join_uri(self, *paths):
        return '/'.join(self.normalize_uri(x) for x in paths)
    
    def _get_websocket_protocol(self):
        return 'ws' if self.config.protocol is 'http' else 'wss'
            
    def get_websocket_url(self):
        """
        Get the url for using the websocked APIs,
        used for both subscription and send/receive.
        """
        return self._get_websocket_protocol() + '://' + config.host + '/v0/ws'
    
    def _format_url(self, relPath, query={}):
        return _format_url(self.config, relPath, query)
            
# Authorization
    def get_authorization_url(self):
        """Get the authorization Url for the current client."""
        return self._format_url(
            OAUTH2_ROOT + 'authorize',
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
        return self._format_url(OAUTH2_ROOT + 'redeem')
            
    def _access_token_endpoint(self, grantType, extraParams={}):
        """
        Base exchange of data for an access_token.
        """
        response = requests.post(
            self._format_url(OAUTH2_ROOT + 'access_token'),
            data = _extend({
                'grant_type': grantType,
                'client_id': self.client.get('client_id', ''),
                'client_secret': self.client.get('client_secret', ''),
                'redirect_uri': self.client.get('redirect_uri', '')
            }, extraParams))
        
        data = response.json()
        if 'error' in data or 'error_description' in data:
            raise _token_error_from_data(data)
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
        
    def exchange_refresh_token(self):
        """
        Attempt to exchange a refresh token for a new access token.
        If successful, update client to use these credentials.
        """
        return self._access_token_endpoint('refresh_token', {
            'refresh_token': self.creds['refresh_token']
        })
            
    def redeem_onetime_code(self, code):
        """
        Attempt to exchange a onetime token for a new access token.
        If successful, update client to use these credentials.
        """
        return self._access_token_endpoint(
            'https://oauth2grant.blot.re/onetime_code', {
                'code': code if code else self.client['code']
            })
    
    def get_token_info(self):
        """
        Get information about the current access token.
        """
        response = requests.get(
            self._format_url(OAUTH2_ROOT + 'token_info', {
                'token': self.creds['access_token']
            }))
        data = response.json()
        if response.status_code is not 200:
            raise _token_error_from_data(data)
        else:
            return data
        
# Requests
    def _add_auth_headers(self, base):
        """Attach the acces_token to a request."""
        if 'access_token' in self.creds:
            return _extend(base, {
                'authorization': 'Bearer ' + self.creds['access_token']
            })
        return base
    
    def _is_expired_response(self, response):
        """
        Check if the response failed because of an expired access token.
        """
        if response.status_code is not 401:
            return False
        challenge = response.headers.get('www-authenticate', '')
        return 'error="invalid_token"' in challenge

    def _make_request(self, type, path, args, noRetry=False):
        """
        Make a request to Blot're.
        
        Attempts to reply the request if it fails due to an expired
        access token.
        """
        response = getattr(requests, type)(path, **args)
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        elif not noRetry and self._is_expired_response(response) \
          and 'refresh_token' in self.creds:
            try:
                self.exchange_refresh_token()
            except TokenEndpointError:
                raise _rest_error_from_response(response)
            return self._make_request(type, path, args, noRetry = True)
        raise _rest_error_from_response(response)
                
    def get(self, path, query={}):
        """GET request."""
        return self._make_request('get',
            self._format_url(API_ROOT + path, query=query), {
                'headers': _JSON_HEADERS
            })
        
    def post(self, path, body):
        """POST request."""
        return self._make_request('post',
            self._format_url(API_ROOT + path), {
                'headers': self._add_auth_headers(_JSON_HEADERS),
                'json': body
            })
            
    def put(self, path, body):
        """PUT request."""
        return self._make_request('put',
            self._format_url(API_ROOT + path), {
                'headers': self._add_auth_headers(_JSON_HEADERS),
                'json': body
            })
            
    def delete(self, path):
        """DELETE request."""
        return self._make_request('get',
            self._format_url(API_ROOT + path), {
                'headers': self._add_auth_headers(_JSON_HEADERS)
            })

# User Operations
    def get_user(self, userId, options={}):
        """Get a user by id."""
        return self.get('user/' + userId, options)
    
# Stream Operations
    def get_streams(self, options={}):
        """Stream lookup."""
        return self.get('stream', options)

    def create_stream(self, body):
        """Create a new stream."""
        return self.put('stream', body)

    def get_stream(self, id, options={}):
        """Get a stream."""
        return self.get('stream/' + id, options)

    def delete_stream(self, id):
        """Delete an existing stream."""
        return self.delete('stream', id)

    def get_stream_status(self, id, options={}):
        """Get the status of a stream."""
        return self.get('stream/' + id, options)

    def set_stream_status(self, id, body):
        """Update the status of a stream."""
        return self.post('stream/' + id + '/status', body)

    def get_stream_children(self, id, options={}):
        """Get the children of a stream."""
        return self.get('stream/' + id + '/children', options)

    def get_child(self, streamId, childId, options={}):
        """Get the child of a stream."""
        return self.get('stream/' + streamId + '/children/' + childId, options)

    def create_child(self, streamId, childId):
        """Add a new child to a stream."""
        return self.put('stream/' + streamId + '/children/' + childId)

    def delete_child(self, streamId, childId):
        """Remove a child from a stream."""
        return self.delete('stream/' + streamId + '/children/' + childId)
        
# Basic Disposable Client
def create_disposable(clientInfo, config = {}):
    """
    Create a new disposable client.
    """
    response = requests.put(
        _format_url(
            _extend(DEFAULT_CONFIG, config), 
            OAUTH2_ROOT + 'disposable'),
        json = clientInfo)
    
    if response.status_code is not 200:
        return None
    else:
        body = response.json() 
        return Blotre({
            'client_id': body['id'],
            'client_secret': body['secret'],
            'code': body['code']
        }, config = config)

# Disposable App
class _BlotreDisposableApp(Blotre):
    def __init__(self, file, client, **kwargs):
        Blotre.__init__(self, client, **kwargs)
        self.file = file
        self._persist()

    def on_creds_changed(self, newCreds):
        self._persist()

    def _persist(self):
        """Persist client data."""
        with open(self.file, 'w') as f:
            json.dump({
                'client': self.client,
                'creds': self.creds,
                'config': self.config
            }, f)

def _get_disposable_app_filename(clientInfo):
    """
    Get name of file used to store creds.
    """
    return clientInfo.get('file', clientInfo['name'] + '.client_data.json')
    
def _get_existing_disposable_app(file, clientInfo, conf):
    """
    Attempt to load an existing 
    """
    if not os.path.isfile(file):
        return None
    else:
        data = None
        with open(file, 'r') as f:
            data = json.load(f)
        if not 'client' in data or not 'creds' in data:
            return None
        return _BlotreDisposableApp(file,
            data['client'],
            creds = data['creds'],
            config = conf)

def _try_redeem_disposable_app(file, client):
    """
    Attempt to redeem a one time code registred on the client.
    """
    redeemedClient = client.redeem_onetime_code(None)
    if redeemedClient is None:
        return None
    else:
        return _BlotreDisposableApp(file,
            redeemedClient.client,
            creds = redeemedClient.creds,
            config = redeemedClient.config)

def _create_new_disposable_app(file, clientInfo, config):
    client = create_disposable(clientInfo, config = config)
    if client is None:
        return None
    code = client.client['code']
    userInput = raw_input("Please redeem disposable code: " + code + '\n')
    return _try_redeem_disposable_app(file, client)

def _check_app_is_valid(client):
    """
    Check to see if the app has valid creds.
    """
    try:
        if 'refresh_token' in client.creds:
            client.exchange_refresh_token()
        else:
            existing.get_token_info()
        return True
    except TokenEndpointError as e:
        return False

def create_disposable_app(clientInfo, config={}):
    """
    Use an existing disposable app if data exists or create a new one
    and persist the data.
    """
    file = _get_disposable_app_filename(clientInfo)
    existing = _get_existing_disposable_app(file, clientInfo, config)
    if existing is not None:
        if _check_app_is_valid(existing):
            return existing
        else:
            print "Existing client has expired, must recreate."
        
    return _create_new_disposable_app(file, clientInfo, config)
