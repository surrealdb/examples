import Cookies from "js-cookie";

const AUTH_COOKIE_NAME = "auth";

export const getAuthCookie = () => {
	return Cookies.get(AUTH_COOKIE_NAME);
};

export const setAuthCookie = (value: string) => {
	Cookies.set(AUTH_COOKIE_NAME, value, {
		expires: 1,
		secure: true,
		sameSite: "strict",
	});
};

export const removeAuthCookie = () => {
	Cookies.remove(AUTH_COOKIE_NAME);
};
