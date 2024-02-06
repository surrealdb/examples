let config = null;

window.onload = async () => {
	// Read the configuration.
	await configure();

	let cognitoToken = null;
	// Check if the code parameter added by Cognito is already in the URL.
	// If so, use it to authenticate the user with Cognito.
	const urlParams = new URLSearchParams(window.location.search);
	const code = urlParams.get("code");
	if (code) {
		// Exchange authorization code for a token.
		cognitoToken = await authenticate(code);
		// Remove the authorization code from the URL after use.
		window.history.replaceState({}, document.title, "/");
	}

	// Show information using the token.
	showInformation(cognitoToken);
}

const configure = async () => {
	const response = await fetch("/config.json");
	config = await response.json();

	document.getElementById("surrealdb-endpoint").textContent = config.surrealdb_endpoint;
	document.getElementById("cognito-domain").textContent = config.cognito_domain;
	document.getElementById("cognito-user-pool-id").textContent = config.cognito_user_pool_id;
	document.getElementById("cognito-client-id").textContent = config.cognito_client_id;

	// Build the URL to the JWKS object for your Cognito user pool.
	// It should be used as the value for your JWKS token in SurrealDB.
	const jwksEndpoint = "https://cognito-idp." + config.cognito_region + ".amazonaws.com/" +
		config.cognito_user_pool_id + "/.well-known/jwks.json";
	document.getElementById("cognito-jwks-endpoint").textContent = jwksEndpoint;

	// Get the origin of the current page.
	// It should be allowed as a redirect in your Cognito client.
	const loc = window.location;
	config.origin = loc.protocol + "//" + loc.hostname + (loc.port ? ":" + loc.port : "");
	document.getElementById("current-origin").textContent = config.origin;
};

// Exchange authorization code for a set of tokens.
const authenticate = async (code) => {
	// Connect to the Cognito token endpoint.
	const tokenEndpoint = config.cognito_domain + "/oauth2/token";
	const headers = {"Content-Type": "application/x-www-form-urlencoded"};

	// Exchange authorization code for a token.
	const queryParams = {
		// This grant type does not require client credentials and is suitable for client applications.
		"grant_type": "authorization_code",
		"client_id": config.cognito_client_id,
		"code": code,
		"redirect_uri": origin,
	};

	const queryString = Object.keys(queryParams)
		.map(key => encodeURIComponent(key) + "=" + encodeURIComponent(queryParams[key]))
		.join("&");

	const cognitoAuth = await fetch(tokenEndpoint + "?" + queryString, {
		method: "POST",
		headers: headers,
	});

	// Return object containing the Cognito tokens.
	const cognitoToken = await cognitoAuth.json();
	return cognitoToken;
};

// Exchange refresh token for a new set of tokens.
const refresh = async () => {
	// Get value of refresh token from DOM element.
	const refreshToken = document.getElementById("ipt-refresh-token").innerHTML;

	// Connect to the Cognito token endpoint.
	const tokenEndpoint = config.cognito_domain + "/oauth2/token";
	const headers = {"Content-Type": "application/x-www-form-urlencoded"};

	// Exchange refresh token for a new token.
	const queryParams = {
		"grant_type": "refresh_token",
		"refresh_token": refreshToken,
		"client_id": config.cognito_client_id,
		"redirect_uri": origin,
	};

	const queryString = Object.keys(queryParams)
		.map(key => encodeURIComponent(key) + "=" + encodeURIComponent(queryParams[key]))
		.join("&");

	const cognitoAuth = await fetch(tokenEndpoint + "?" + queryString, {
		method: "POST",
		headers: headers,
	});

	// Parse JSON object containing the new Cognito tokens.
	// These tokens will not contain a new refresh token.
	const newCognitoToken = await cognitoAuth.json();

	// Update information in the UI with the new token.
	showInformation(newCognitoToken);

	// Set the original value of the refresh token in the DOM element.
	document.getElementById("ipt-refresh-token").innerHTML = refreshToken;
};

const showInformation = async (cognitoToken) => {
	// If we have a token, we are authenticated.
	const isAuthenticated = cognitoToken != null;

	document.getElementById("btn-login").disabled = isAuthenticated;
	document.getElementById("btn-refresh").disabled = !isAuthenticated;
	document.getElementById("btn-logout").disabled = !isAuthenticated;

	// If we are authenticated, show user information.
	if (isAuthenticated) {
		document.getElementById("gated-content").classList.remove("hidden");

		document.getElementById("ipt-id-token").innerHTML = cognitoToken.id_token;
		document.getElementById("ipt-id-token-decoded").textContent = decodeToken(cognitoToken.id_token);
		document.getElementById("ipt-refresh-token").innerHTML = cognitoToken.refresh_token;
		// Uncomment the following lines and corresponding HTML elements if you want to work with the access token.
		// document.getElementById("ipt-access-token").innerHTML = cognitoToken.access_token;
		// document.getElementById("ipt-access-token-decoded").innerHTML = decodeToken(cognitoToken.access_token);

		// Create or update user in SurrealDB with token and get their information from SurrealDB.
		const user = await createUpdateUser(cognitoToken);
		document.getElementById("ipt-sdb-createupdateuser").textContent = JSON.stringify(user);
	} else {
		document.getElementById("gated-content").classList.add("hidden");
	}
};

// Returns any users that the token is authorized to select.
// Should return only the single user matching the email in the token.
const getUser = async (cognitoToken) => {
	const response = await fetch(config.surrealdb_endpoint + "/key/user", {
		method: "GET",
		headers: {
			"Accept": "application/json",
			"Authorization": "Bearer " + cognitoToken.id_token
		}
	});

	return response.json();
};

// Creates a user matching the information in the token.
// If the user already exists, updates the existing user with the new data.
const createUpdateUser = async (cognitoToken) => {
	// We retrieve some user information from the token claims.
	const tokenClaims = parseToken(cognitoToken.id_token);

	// We define the general query to create or update a user.
	// We leave the method to be defined later.
	let query = {
		body: JSON.stringify({
			email: tokenClaims.email,
			cognito_username: tokenClaims["cognito:username"],
		}),
		headers: {
			"Accept": "application/json",
			"Authorization": "Bearer " + cognitoToken.id_token
		}
	};

	// We retrieve the user that the token is authorized to access.
	const surrealDbUser = await getUser(cognitoToken);
	if (surrealDbUser[0].result.length == 0) {
		// If a user for the token does not exist, we create the record.
		console.log("Token user does not exist in database. Creating record.");
		query.method = "POST";
	} else {
		// If a user for the token already exists, we update the record.
		console.log("Token user already exists in database. Updating record.");
		query.method = "PUT";
	}

	// We perform the query and return the created/updated record.
	const response = await fetch(config.surrealdb_endpoint + "/key/user", query);
	return response.json();
};

const login = () => {
	// Redirect user to the Cognito Hosted UI.
	document.location = config.cognito_domain +
		"/login?response_type=code&client_id=" + config.cognito_client_id + "&redirect_uri=" + origin;
};

const logout = () => {
	// Redirect user to the Cognito logout endpoint.
	document.location = config.cognito_domain +
		"/logout?response_type=code&client_id=" + config.cognito_client_id + "&redirect_uri=" + origin;
};

// Parse the JWT to access its claims.
// NOTE: It is important to note that NO VERIFICATION is made here.
// The function does not properly parse the JWT following RFC 7519 either.
// This function exists only to get some data for demonstration purposes.
const parseToken = (token) => {
	const tokenParts = token.split(".");
	return JSON.parse(atob(tokenParts[1]));
};

// Print the decoded JWT to assist with debugging.
const decodeToken = (token) => {
	const tokenParts = token.split(".");
	const decodedToken = "Header:\n" + atob(tokenParts[0]) + "\n\nPayload:\n" + atob(tokenParts[1]);
	return decodedToken
};
