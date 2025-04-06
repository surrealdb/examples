DEFINE ACCESS user ON DATABASE TYPE RECORD
	SIGNUP ( CREATE user SET name = $name, email = $email, password = crypto::argon2::generate($pass) )
	SIGNIN ( SELECT * FROM user WHERE email = $email AND crypto::argon2::compare(password, $pass) )
	DURATION FOR TOKEN 15m, FOR SESSION 12h
;

DEFINE TABLE user SCHEMAFULL
	PERMISSIONS FOR select, update, delete
		WHERE $access = "user"
		AND id = $auth.id
;

-- Give the user table an email field. Store it in a string
DEFINE FIELD email ON TABLE user 
    TYPE string
    ASSERT string::is::email($value);

DEFINE FIELD name ON TABLE user TYPE string;
DEFINE FIELD password ON TABLE user TYPE string;