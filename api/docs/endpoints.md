# Lindele API Endpoints
In most cases, except when media is served, responses are json and take the following format:
```
{
	'status_code': 200,
	'status': 'OK',
	'version': '1.0',
	'data': {},
	'error': ''
}
```
The `status_code` and `status` elements will always reflect their RFC 
designations, using [this page](https://www.restapitutorial.com/httpstatuscodes.html)
as a reference.

Where not specified, a successful response is almost always a 200 code, with an
empty `data` element and a null `error` element. The examples given for each
endpoint describe the `data` element for a successful call.

Most unsuccessful requests specify the problem in their `error` element, when
it makes sense to provide that information to the consumer.

## User endpoints
<details>
<summary>`/users/<username>`</summary>
Currently only returns a json with the current user's username.

Requirements:
	A user must be logged in.

Example response:
	`{ 'username': 'AcidBurn' }`
</details>

`/register`
Attempts to register a user account.

Request parameters:
	email
	username
	password
	password_confirm

`/login`
Authenticates credentials provided by a user.

Request parameters:
	email
	password

`/logout`
Tells the browser to clear its cookies for the API.

Requirements:
	A user to be logged in.

`/current_user`
Gets information about the user that is currently logged in.

Example response:



`/set_volume`



## Music endpoints
### Track endpoints
`/songs`


`/songs/(\d+)`


`/songs/(\d+)/audio`


`/songs/(\d+)/artwork`



### Playlist endpoints
`/playlists`


`/playlists/(\d+)`


`/playlists/create`


`/playlists/owned`


`/playlists/(\d+)/add`


`/playlists/(\d+)/remove`


`/playlists/(\d+)/set_publicity`



## System control endpoints
`/refresh`


`/remount`


`/restart`


`/ping`

