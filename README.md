<div align="center">
    <a href="https://blot.re">
        <img src="https://github.com/mattbierner/blotre/raw/master/documentation/readme-logo.png" width="280px" alt="Blot're" />
    </a>
</div>

Thin Python [Blot're][blotre] client.

**Supports**
* Unauthenticated queries.
* Authorization flows.
 * Exchange authorization code for creds.
 * Disposable client creation and redemption.
* Authorized requests.
 * Automatic exchanges refresh token if available.
* Easy disposable client creation for command line apps.

## Client Creation

### Basic Client Creation
To create a new client application after [registering on Blot're][blotre-register]. 

```python
import blotre

blotre.Blotre({
    'client_id': "Client id from Blot're",
    'client_secret': "Client secret from Blot're",
    'redirect_uri': "Redirect uri registed with Blot're",
})
```

You can also manually provide credentials to be used in requests

```python
blotre.Blotre({ ... }, creds = {
    'access_token' = "token value",
    'refresh_token' = "optional, refresh token value"
})
```

### Authorization Code Flow
The OAuth2 authorization code flow is the preferred method to obtain user authorization.

First create a new client using the information you [registered with Blot're][blotre-register].

```python
import blotre

client = blotre.Blotre({
    'client_id': "55614f0630042c617481d7c3",
    'client_secret': "YTY1Njg2MDctZTdjYy00ODlhLWFkNmYtNjkzYjI3N2M0MDRl",
    'redirect_uri': "http://localhost:50000",
})
```

Then, display the authorization page to the user

```python
print client.get_authorization_url()

https://blot.re/v0/oauth2/authorize?redirect_uri=http%3A%2F%2Flocalhost%3A50000&response_type=code&client_id=55614f0630042c617481d7c3
```

After the user has authorized and your app has the authorization code, you can exchange the code for credentials.

```python
try:
    # Exchange the code for creds and update the current client
    client.redeem_authorization_code(returned_code)
    # Client is now authorized
handle blotre.TokenEndpointError as e:
    # Something went wrong.
    print e
```

### Basic Disposable Client Creation
Alternately, for simple applications you can use the [Blot're disposable client authorization flow][blotre-disposable]. This allows you to register a client application that can be authorized by at most one user.


```python
import blotre

client = blotre.create_disposable({
    'name': "Toa*",
    'blurb': "The Pintrest of toast"
})
```

Now the user must redeem the code to authorized your app

```python
print client.get_redeem_url()
print client.client.code

# Wait for user to redeem, and then
try:
    # Exchange the code for creds and update the current client
    client.redeem_onetime_code()
    # Client is now authorized
handle blotre.TokenEndpointError as e:
    # Something went wrong.
    print e
```

## Making Requests
Query operations do not require any user authorization:

```python
import blotre

client = blotre.Blotre({})
print client.get_streams()
```

Successful operations return parsed JSON data. All operations also take a list of query parameters

```python
client.get_streams({
    'query': 'toast'
})
```

Create, update, and delete operations all require client authorization.

```python
try:
    client.create_stream({
        'name': 'Temperature'
        'uri': "toastmastergeneral/temperature"
    })
handle blotre.RestError as e:
    print e # not authorized in this case
```

All the APIs are extremely simple and just forward to Blot're. This means that  you are responsible for correctly formating the request.

``` python
try:
    client.create_stream({
        'name': 'A B C'
        'uri': "toastmastergeneral/a b c"
    })
handle blotre.RestError as e:
    print e # Invalid uri, uri may not contains spaces
```

```python
# Instead you must escape the uri client side first
name = 'A B C'
client.create_stream({
    'name': 
    'uri': client.join_uri('toastmastergeneral', name)
})
```

If the access_token expires while your client app is running and a refresh token is available, the client will silently attempt to exchange the refresh token and replay the request.


## Disposable Command Line Apps
[Disposable client apps][blotre-disposable] are good for prototyping and hacking together simple applications. You can create a disposable app manually using Blot're.py, but a helper for command line applications is also provided. This helper persists client data and prompts the user with instructions.

Using it is simple:

```python
import blotre

client = blotre.create_disposable_app({
    'name': "FaceToast",
    'blurb': "Your face on toast!"
})
```

Unlike `create_disposable`, this will look for existing client data in a file and make sure this client has valid creds. If the creds are valid, not further steps are required and `client` can make authorized requests.

If there is not data or the client data has expired, a new disposable app is registred with Blot're. The user is then prompted to redeem the code and press enter. Once they do this, the app exchanges its data for an access token and becomes authorized.

All this happens synchronously so `client` will always be authorized when it is returned, unless of course the user does not redeem the code. The credentials and client info are automatically persisted to a file and can be picked up later.



[blotre]: https://blot.re
[blotre-register]: https://github.com/mattbierner/blotre/wiki/registering-a-client
[blotre-rest]: https://github.com/mattbierner/blotre/wiki/REST
[blotre-disposable]: https://github.com/mattbierner/blotre/wiki/single-use-clients
