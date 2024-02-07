# SurrealDB AWS Cognito Authentication Example

## Introduction

**Important**: This example is intended to be used alongside the [AWS Cognito Integration Guide](https://docs.surrealdb.com/docs/nightly/how-to/integrate-aws-cognito-as-authentication-provider/).

This example shows how AWS Cognito can be used as an authentication provider by web applications that rely on SurrealDB as the only backend.

The application will authenticate the user with AWS Cognito and use the identity token issued to create or update their user in the SurrealDB backend.

It will also demonstrate how the authenticated user is only allowed to query their own user record from SurrealDB.

## Usage

### Configuration

You must first configure the values that you generated while following the [AWS Cognito Integration Guide](https://docs.surrealdb.com/docs/nightly/how-to/integrate-aws-cognito-as-authentication-provider/) in the `config.json` file.

You may also update the address of the SurrealDB endpoint to match your testing environment.

```json
{
	"surrealdb_endpoint": "http://localhost:8000",
	"cognito_region": "YOUR_AWS_COGNITO_REGION",
	"cognito_domain": "YOUR_COGNITO_USER_POOL_DOMAIN",
	"cognito_user_pool_id": "YOUR_COGNITO_USER_POOL_ID",
	"cognito_client_id": "YOUR_COGNITO_CLIENT_ID"
}
```

### Preparation

You must have a SurrealDB instance listening at the `surrealdb_endpoint` address and configured as described in the [AWS Cognito Integration Guide](https://docs.surrealdb.com/docs/nightly/how-to/integrate-aws-cognito-as-authentication-provider/).

### Execution

To run this example, you can serve the files at the root of this directory with any file server and visit its address on any modern web browser.

For example, you can use the provided `start.sh` script to serve the files with a simple Python file server and visit `http://localhost:8080`. 
