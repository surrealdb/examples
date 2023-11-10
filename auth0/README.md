# SurrealDB Auth0 Authentication Example

## Introduction

**Important**: This example is intended to be used alongside the [Auth0 Integration Guide](#TBD).

This example has been created to show how Auth0 can be used as an authentication provider by web applications that rely on SurrealDB as their only backend.

This example application will authenticate the user with Auth0 and use the access token issued to create or update their user in the SurrealDB backend.

It will also demonstrate how the authenticated user is only authorized to query their own user record from SurrealDB.

## Usage

### Configuration

You must first configure the values that you generated while following the [Auth0 Integration Guide](#TBD) in the `config.json` file.

You may also update the address of the SurrealDB endpoint to match your testing environment.

```json
{
	"surrealdb_endpoint": "http://localhost:8000",
	"auth0_domain": "YOUR_AUTH0_DOMAIN",
	"auth0_client_id": "YOUR_AUTH0_CLIENT_ID",
	"auth0_audience": "YOUR_AUTH0_AUDIENCE"
}
```

### Preparation

You must have a SurrealDB instance listening at the `surrealdb_endpoint` address and configured as described in the [Auth0 Integration Guide](#TBD).

### Execution

To run this example, you can serve the files at the root of this directory with any file server and visit its address on any modern web browser.

For example, you can use the provided `start.sh` script to serve the files with a simple Python file server and visit `http://localhost:8080`. 
