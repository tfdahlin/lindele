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
<details><!-- GET /users/{username} -->
	<summary>GET /users/{username}</summary>
	<p>Currently only returns json with the user's username.</p>
	<p>
	Requirements:
		- A user must be logged in.
	</p>
	<p>
	Example response:
		`{ 'username': 'AcidBurn' }`
	</p>
</details>

<details><!-- POST /register -->
	<summary>POST /register</summary>
	Attempts to register a user account.

	Request parameters:
		- email
		- username
		- password
		- password_confirm
</details>

<details><!-- POST /login -->
	<summary>POST /login</summary>
	Authenticates credentials provided by a user.

	Request parameters:
		- email
		- password
</details>

<details><!-- POST /logout -->
	<summary>POST /logout</summary>
	Tells the browser to clear its cookies for the API.

	Requirements:
		A user to be logged in.
</details>

<details><!-- GET /current_user -->
	<summary>GET /current_user</summary>
	Gets information about the user that is currently logged in.

	Example response:

		```
		{
			'logged_in:' true,
			'user': {
				'username': 'AcidBurn',
				'volume': 95
			}
		}
		```
</details>

<details><!-- POST /set_volume -->
	<summary>POST /set_volume</summary>
	Stores a volume level for the user that is currently logged in.

	Request parameters:
		volume
</details>


## Music endpoints
### Track endpoints
<details><!-- GET /songs -->
	<summary>GET /songs</summary>
	Provides a list of all songs currently in the database.

	This list is sorted by artist name, then album name, then track title.

	Example response:

	```
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
	```
</details>

<details><!-- GET /songs/{song_id} -->
	<summary>GET /songs/{songid}</summary>
	Provides track details about a specific track.

	Example response:

	```
	{
		'title': 'Linger Longer',
		'artist': 'Cosmo Sheldrake',
		'album': 'The Much Much How How and I (Deluxe)',
		'id': 1337,
		'length': '05:36'
	}
	```
</details>

<details><!-- GET /songs/{song_id}/audio -->
	<summary>GET /songs/{song_id}/audio</summary>
	Serves the audio for a specific track.

	This route allows handles range requests, and in those cases returns a 206
	status code.
	This route does not serve files with the application/json content-type 
	header, and instead serves with the audio/mpeg content-type header.
</details>

<details><!-- GET /songs/{song_id}/artwork -->
	<summary>GET /songs/{song_id}/artwork</summary>
	Serves the album artwork for a specific track.

	This route does not serve files with the application/json content-type 
	header, and instead serves with the image/jpeg or image/png content-type 
	header.
</details>


### Playlist endpoints
<details><!-- GET /playlists -->
	<summary>GET /playlists</summary>
	Provides a list of all playlists that the current user can access.

	This includes both public playlists, and playlists owned by the current user.

	Example response:

	```
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
	```
</details>

<details><!-- GET /playlists/{playlist_id} -->
	<summary>GET /playlists/{playlist_id}</summary>
	Provides details about a specific playlist.

	Example response:

	```
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
	```
</details>

<details><!-- POST /playlists/create -->
	<summary>POST /playlists/create</summary>
	Creates a new playlist for the current user.

	Parameters:
		- playlist_name

	Requirements:
		- A user must be logged in.
</details>

<details><!-- GET /playlists/owned -->
	<summary>GET /playlists/owned</summary>
	Provides a list of playlists owned by the user making the request.

	This is different from the /playlists endpoint because it does not include
	public playlists not owned by the current user.

	Requirements:
		- A user must be logged in.

	Example response:

	```
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
	```
</details>

<details><!-- POST /playlists/{playlist_id}/add -->
	<summary>POST /playlists/{playlist_id}/add</summary>
	Adds a song to the specified playlist.

	Parameters:
		- songid

	Requirements:
		- A user must be logged in.
		- The user must own the playlist being modified.
</details>

<details><!-- POST /playlists/{playlist_id}/remove -->
	<summary>POST /playlists/{playlist_id}/remove</summary>
	Removes a song from the specified playlist.

	Parameters:
		- songid

	Requirements:
		- A user must be logged in.
		- The user must own the playlist being modified.
</details>

<details><!-- POST /playlists/{playlist_id}/set_publicity -->
	<summary>POST /playlists/{playlist_id}/set_publicity</summary>
	Sets the publicity of the specified playlist.

	Parameters:
		- is_public: Must be a boolean or a string that, when converted to lowercase, reads "true" or "false"

	Requirements:
		- A user must be logged in.
		- The user must own the playlist being modified.
</details>


## System control endpoints
<details><!-- GET /refresh -->
	<summary>GET /refresh</summary>
	Prompts the song database to be refreshed by processing the music folder.
</details>

<details><!-- GET /remount -->
	<summary>GET /remount</summary>
	Prompts the server to attempt to remount the music folder, if applicable.

	Requirements:
		- User must be logged in.
		- Current user must be an admin.
</details>

<details><!-- GET /restart -->
	<summary>GET /restart</summary>
	Prompts the server to restart after a short delay.

	Requirements:
		- User must be logged in.
		- Current user must be an admin.
</details>

<details><!-- GET /ping -->
	<summary>GET /ping</summary>
	Returns a simple response to test that the server is online.

	Example response:

	```
	{
		'msg': 'Pong!'
	}
	```
</details>
