let config = null;
let auth0Client = null;

const fetchConfig = () => fetch("/config.json");

const configure = async () => {
	const response = await fetchConfig();
	const config = await response.json();

	document.getElementById("surrealdb-endpoint").textContent = config.surrealdb_endpoint;
	document.getElementById("auth0-domain").textContent = config.auth0_domain;
	document.getElementById("auth0-client-id").textContent = config.auth0_client_id;
	document.getElementById("auth0-audience").textContent = config.auth0_audience;

	auth0Client = await auth0.createAuth0Client({
		domain: config.auth0_domain,
		clientId: config.auth0_client_id,
		authorizationParams: {
			audience: config.auth0_audience
		}
	});
};

window.onload = async () => {
	await configure();
	updateUI();

	const isAuthenticated = await auth0Client.isAuthenticated();

	const query = window.location.search;
	if (query.includes("code=") && query.includes("state=")) {
		await auth0Client.handleRedirectCallback();

		updateUI();

		window.history.replaceState({}, document.title, "/");
	}
}

const updateUI = async () => {
	const isAuthenticated = await auth0Client.isAuthenticated();

	document.getElementById("btn-logout").disabled = !isAuthenticated;
	document.getElementById("btn-login").disabled = isAuthenticated;

	if (isAuthenticated) {
		document.getElementById("gated-content").classList.remove("hidden");

		document.getElementById("ipt-id-token").innerHTML = (await auth0Client.getIdTokenClaims()).__raw;
		document.getElementById("ipt-access-token").innerHTML = await auth0Client.getTokenSilently();
		document.getElementById("ipt-access-token-decoded").textContent = await decodeToken();
		document.getElementById("ipt-user-profile").textContent = JSON.stringify(await auth0Client.getUser());

		document.getElementById("ipt-sdb-getuser").textContent = JSON.stringify(await getUser());
		document.getElementById("ipt-sdb-createupdateuser").textContent = JSON.stringify(await createUpdateUser());
	} else {
		document.getElementById("gated-content").classList.add("hidden");
	}
};

const login = async () => {
	await auth0Client.loginWithRedirect({
		authorizationParams: {
			redirect_uri: window.location.origin
		}
	});
};

const logout = () => {
	auth0Client.logout({
		logoutParams: {
			returnTo: window.location.origin
		}
	});
};

// Print the decoded JWT to assist with debugging.
const decodeToken = async () => {
	const token = await auth0Client.getTokenSilently();
	const tokenParts = token.split(".");
	const decodedToken = "Header:\n" + atob(tokenParts[0]) + "\n\nPayload:\n" + atob(tokenParts[1]);
	return decodedToken
};

// Returns any users that the token is authorized to select.
// Should return only the single user matching the email in the token.
const getUser = async () => {
	// We fetch an access token from Auth0 with the ID token.
	const auth0Token = await auth0Client.getTokenSilently();

	const response = await fetch(config.surrealdb_endpoint + "/key/user", {
		method: "GET",
		headers: {
			"Accept": "application/json",
			"Authorization": "Bearer " + auth0Token
		}
	});

	return response.json();
};

// Creates a user matching the information in the token.
// If the user already exists, updates the existing user with the new data.
const createUpdateUser = async () => {
	// We collect the user data from the Auth0 ID token.
	const auth0User = await auth0Client.getUser();
	// We fetch an access token from Auth0 with the ID token.
	const auth0Token = await auth0Client.getTokenSilently();

	// We define the general query to create or update a user.
	// We leave the method to be defined later.
	let query = {
		body: JSON.stringify({
			email: auth0User.email,
			name: auth0User.name,
			nickname: auth0User.nickname,
			picture: auth0User.picture
		}),
		headers: {
			"Accept": "application/json",
			"Authorization": "Bearer " + auth0Token
		}
	};

	// We retrieve the user that the token is authorized to access.
	const surrealDbUser = await getUser();
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
	let response = await fetch(config.surrealdb_endpoint + "/key/user", query);
	return response.json();
};
