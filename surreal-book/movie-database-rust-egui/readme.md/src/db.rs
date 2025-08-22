use std::{
    fmt::Display,
    sync::mpsc::{Receiver, Sender},
    time::Instant,
};

use anyhow::Error;

use surrealdb::{engine::any::Any, opt::auth::{Record, Root}, Surreal, Value};

use crate::{Movie, app::DbCommand};

// Responses from the database back to the app
#[derive(Debug)]
pub enum DbResponse {
    Busy,
    Free,
    Info(String),
    Movie(Vec<Movie>),
    Person(Value),
    Country(Value),
    Other(String),
    Error(String),
    RandomMovie(Movie),
}

impl Display for DbResponse {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DbResponse::Busy => write!(f, "Busy"),
            DbResponse::Free => write!(f, "Free"),
            DbResponse::Info(i) => write!(f, "{i}"),
            DbResponse::Movie(value) => write!(f, "{value:?}"),
            DbResponse::Person(value) => write!(f, "{value}"),
            DbResponse::Country(value) => write!(f, "{value}"),
            DbResponse::Other(o) => write!(f, "{o}"),
            DbResponse::Error(e) => write!(f, "{e}"),
            DbResponse::RandomMovie(value) => write!(f, "{value}"),
        }
    }
}

pub struct Database {
    pub db: Surreal<Any>,
    pub command_receiver: Receiver<DbCommand>,
    pub response_sender: Sender<DbResponse>,
    pub clock: Instant,
}

impl Database {
    pub fn send_error(&self, err: surrealdb::Error) -> Result<(), Error> {
        Ok(self
            .response_sender
            .send(DbResponse::Error(err.to_string()))?)
    }

    pub async fn receive(&mut self) -> Result<(), Error> {
        if let Ok(msg) = self.command_receiver.try_recv() {
            self.response_sender.send(DbResponse::Busy)?;
            match msg {
                DbCommand::SelectPerson(s) => match self
                    .db
                    .query("SELECT name, roles FROM person WHERE name @@ $input;")
                    .bind(("input", s))
                    .await
                {
                    Ok(mut c) => self.response_sender.send(DbResponse::Person(c.take(0)?))?,
                    Err(e) => self.send_error(e)?,
                },
                DbCommand::SelectMovie { title, plot } => {
                    let query = match (title, plot) {
                        (Some(title), Some(plot)) => format!(
                            r#"SELECT *, 
                                languages.join(', '),
                                genres.join(', '),
                                released.format("%Y-%m-%d"),
                                <int>math::round(average_rating) AS average_rating
                                FROM movie WHERE plot @@ '{plot}' AND title @@ '{title}'"#
                        ),
                        (Some(title), None) => {
                            format!(
                                r#"SELECT *,
                                languages.join(', '),
                                genres.join(', '),
                                released.format("%Y-%m-%d"),
                                <int>math::round(average_rating) AS average_rating
                                FROM movie WHERE title @@ '{title}'"#
                            )
                        }
                        (None, Some(plot)) => format!(
                            r#"SELECT *, 
                            languages.join(', '),
                            genres.join(', '),
                            released.format("%Y-%m-%d"),
                            <int>math::round(average_rating) AS average_rating
                            FROM movie WHERE plot @@ '{plot}'"#
                        ),
                        (None, None) => unreachable!(),
                    };
                    match self.db.query(query).await {
                        Ok(mut c) => {
                            self.response_sender.send(DbResponse::Movie(c.take(0)?))?;
                        }
                        Err(e) => self.send_error(e)?,
                    };
                }
                DbCommand::SelectCountry(input) => {
                    let query = "SELECT name AS country, ->has_movie->movie.{ title, released: released.format('%Y') } AS movies FROM country WHERE $name IN name";
                    match self.db.query(query).bind(("name", input)).await {
                        Ok(mut c) => self.response_sender.send(DbResponse::Country(c.take(0)?))?,
                        Err(e) => self.send_error(e)?,
                    };
                }
                DbCommand::RawQuery(q) => match self.db.query(q).await {
                    Ok(mut c) => {
                        let mut response = String::new();
                        for i in 0..c.num_statements() {
                            if let Ok(r) = c.take::<Value>(i) {
                                response.push_str(&format!("{r}\n"))
                            }
                        }
                        self.response_sender.send(DbResponse::Other(response))?;
                    }
                    Err(e) => self.send_error(e)?,
                },
                DbCommand::Signup(q) => match self
                    .db
                    .signup(Record {
                        namespace: "movies",
                        database: "movies",
                        access: "account",
                        params: q,
                    })
                    .await
                {
                    Ok(c) => self
                        .response_sender
                        .send(DbResponse::Other(format!("{c:?}")))?,
                    Err(e) => self.send_error(e)?,
                },
                DbCommand::Signin(q) => match self
                    .db
                    .signin(Record {
                        namespace: "movies",
                        database: "movies",
                        access: "account",
                        params: q,
                    })
                    .await
                {
                    Ok(c) => self
                        .response_sender
                        .send(DbResponse::Other(format!("{c:?}")))?,
                    Err(e) => self.send_error(e)?,
                },
                DbCommand::Root => match self
                    .db
                    .signin(Root {
                        username: "root",
                        password: "root",
                    })
                    .await
                {
                    Ok(_) => self
                        .response_sender
                        .send(DbResponse::Other("Now root again!".into()))?,
                    Err(e) => self
                        .response_sender
                        .send(DbResponse::Other(format!("Couldn't sign in: {e}")))?,
                },
            }
            self.response_sender.send(DbResponse::Free)?;
        }
        Ok(())
    }

    pub async fn get_random_movie(&self) -> Result<Movie, Error> {
        let mut res = self
            .db
            .query(
                "RETURN rand::enum(SELECT *, time::format(released, '%Y') AS released, languages.join(', '), genres.join(', ') FROM movie)",
            )
            .await?;
        match res.take::<Option<Movie>>(0)? {
            Some(movie) => Ok(movie),
            None => Err(anyhow::anyhow!("Couldn't find a movie")),
        }
    }
}