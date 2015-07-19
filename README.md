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
client.create_stream({
    'name': 'Temperature'
    'uri': "toastmastergeneral/temperature"
})




[blotre]: https://blot.re
[blotre-register]: https://github.com/mattbierner/blotre/wiki/registering-a-client
[blotre-rest]: https://github.com/mattbierner/blotre/wiki/REST
[blotre-disposable]: https://github.com/mattbierner/blotre/wiki/single-use-clients
