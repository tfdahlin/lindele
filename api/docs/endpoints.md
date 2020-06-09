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
<summary>GET /users/{username}</summary>

#### Description
Currently only returns json with the user's username.

##### Requirements:
- A user must be logged in.

##### Example response:

`{ 'username': 'AcidBurn' }`
</details>

<details>
<summary>POST /register</summary>

#### Description
Attempts to register a user account.

##### Parameters:
- email
- username
- password
- password_confirm
</details>

<details>
<summary>POST /login</summary>

#### Description
Authenticates credentials provided by a user.

##### Parameters:
- email
- password
</details>

<details>
<summary>POST /logout</summary>

#### Description
Tells the browser to clear its cookies for the API.

##### Requirements:
- A user to be logged in.
</details>

<details>
<summary>GET /current_user</summary>

#### Description
Gets information about the user that is currently logged in.

##### Example response:

	{
		'logged_in:' true,
		'user': {
			'username': 'AcidBurn',
			'volume': 95
		}
	}
</details>

<details>
<summary>POST /set_volume</summary>

#### Description
Stores a volume level for the user that is currently logged in.

##### Parameters:
- volume
</details>


## Music endpoints
### Track endpoints
<details>
<summary>GET /songs</summary>

#### Description
Provides a list of all songs currently in the database.

This list is sorted by artist name, then album name, then track title.

##### Example response:

	{
		'tracks': [
			{
				'title': 'Linger Longer',
				'artist': 'Cosmo Sheldrake',
				'album': 'The Much Much How How and I (Deluxe)',
				'id': 1337,
				'length': '05:36'
			},
			...
		]
	}
</details>

<details>
<summary>GET /songs/{songid}</summary>

#### Description
Provides track details about a specific track.

##### Example response:

	{
		'title': 'Linger Longer',
		'artist': 'Cosmo Sheldrake',
		'album': 'The Much Much How How and I (Deluxe)',
		'id': 1337,
		'length': '05:36'
	}
</details>

<details>
<summary>GET /songs/{song_id}/audio</summary>

#### Description
Serves the audio for a specific track.

This route supports requests that specify a single byte range, and will serve
the range specified in the `Range` HTTP header of a request. If the `Range`
header is set, this endpoint will return a 206 status code.

This route does not serve files with the application/json content-type 
header, and instead serves with the audio/mpeg content-type header.

If the request includes `dl=1` as a parameter, it is served with a 
`Content-Disposition` header of `attachment; filename="{track name}.mp3"` so
that browsers know to prompt the user to download the file.

##### Parameters:
- dl
</details>

<details>
<summary>GET /songs/{song_id}/artwork</summary>

#### Description
Serves the album artwork for a specific track.

This route does not serve files with the application/json content-type 
header, and instead serves with the image/jpeg or image/png content-type 
header.
</details>


### Playlist endpoints
<details>
<summary>GET /playlists</summary>

#### Description
Provides a list of all playlists that the current user can access.

This includes both public playlists, and playlists owned by the current user.

The ordering of returned playlists is arbitrary.

##### Example response:

	{
		'playlists': [
			{
				'id': 1,
				'name': 'Best playlist ever!!!',
				'owner_name': 'AcidBurn',
				'public': false
			},
			...
		]
	}
</details>

<details>
<summary>GET /playlists/{playlist_id}</summary>

#### Description
Provides details about a specific playlist.

##### Example response:

	{
		'tracks': [
			{
				'title': 'Linger Longer',
				'artist': 'Cosmo Sheldrake',
				'album': 'The Much Much How How and I (Deluxe)',
				'id': 1337,
				'length': '05:36'
			}, 
			...
		],
		'owner_name': 'AcidBurn',
		'name': 'Best playlist ever!!!',
		'public': false
	}
</details>

<details>
<summary>POST /playlists/create</summary>

#### Description
Creates a new playlist for the current user.

##### Parameters:
- playlist_name

##### Requirements:
- A user must be logged in.
</details>

<details>
<summary>GET /playlists/owned</summary>

#### Description
Provides a list of playlists owned by the user making the request.

This is different from the /playlists endpoint because it does not include
public playlists not owned by the current user.

The ordering of returned playlists is arbitrary.

Requirements:
- A user must be logged in.

##### Example response:

	{
		'playlists': [
			{
				'id': 1,
				'name': 'Best playlist ever!!!',
				'owner_name': 'AcidBurn',
				'public': false
			},
			...
		]
	}

</details>

<details>
<summary>POST /playlists/{playlist_id}/add</summary>

#### Description
Adds a song to the specified playlist.

##### Parameters:
- songid

##### Requirements:
- A user must be logged in.
- The user must own the playlist being modified.
</details>

<details>
<summary>POST /playlists/{playlist_id}/remove</summary>

#### Description
Removes a song from the specified playlist.

##### Parameters:
- songid

##### Requirements:
- A user must be logged in.
- The user must own the playlist being modified.
</details>

<details>
<summary>POST /playlists/{playlist_id}/set_publicity</summary>

#### Description
Sets the publicity of the specified playlist.

By default, playlists that a user creates are not publicly accessible. This 
allows a user to publicly share their playlist.

##### Parameters:
- is_public: Must be a boolean or a string that, when converted to lowercase, reads "true" or "false"

##### Requirements:
- A user must be logged in.
- The user must own the playlist being modified.
</details>


## System control endpoints
<details>
<summary>GET /refresh</summary>

Prompts the song database to be refreshed by processing the music folder.
</details>

<details>
<summary>GET /remount</summary>

#### Description
Prompts the server to attempt to remount the music folder, if applicable.

##### Requirements:
- User must be logged in.
- Current user must be an admin.
</details>

<details>
<summary>GET /restart</summary>

#### Description
Prompts the server to restart after a short delay.

##### Requirements:
- User must be logged in.
- Current user must be an admin.
</details>

<details>
<summary>GET /ping</summary>

#### Description
Returns a simple response to test that the server is online.

##### Example response:

	{ 
		'msg': 'Pong!'
	}
</details>
