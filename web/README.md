# Lindelë Web Client
The Lindelë web client serves as a simple client for interacting with the API.
By opening the client in a browser, a user can seamlessly enjoy their music
collection with ease after the API backend has been configured. The client is
separate from the backend in order to encourage user interoperability. If a
user wants to customize their own client, or write a client for another
platform, it should be able to function just as well as this web client.

## Web Client Setup

### Installation
1. Make sure you have [Node.js][1] and NPM installed on your system.
2. Navigate to the `web` folder. 
3. Run `npm install`.

### Running The Frontend
To run the Node.js server, you will need to make a copy of
`web/sample_settings.js` named `web/settings.js`, and make changes accordingly.
After this, you should only need to navigate to the appropriate folder and run
`node app.js`.

[1]:https://nodejs.org