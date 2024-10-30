DEFINE ACCESS user ON DATABASE TYPE RECORD 
    SIGNUP (
        CREATE user CONTENT { 
            name: $name, 
            password: crypto::argon2::generate($password), 
            username: $username
        }
    )
    SIGNIN (
        SELECT * FROM user WHERE username = $username AND crypto::argon2::compare(password, $password)
    )
DURATION FOR TOKEN 1h, FOR SESSION 1w
