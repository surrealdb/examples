use std::{
    fmt::Display,
    sync::mpsc::{Receiver, Sender},
    time::Instant,
};

use anyhow::Error;

use surrealdb::{
    Surreal,
    engine::any::Any,
    opt::auth::{Record, Root},
};
use surrealdb_types::{SurrealValue, ToSql, Value};

use crate::{Movie, app::DbCommand};

// Responses from the database back to the app
#[derive(Clone, Debug, SurrealValue)]
pub enum DbResponse {
    Busy,
    Free,
    Info(String),
    Movie(Vec<Movie>),
    Person(Value),
    Other(String),
    Error(String),
    RandomMovie(Movie),
}

impl Display for DbResponse {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.clone().into_value().to_sql())
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
                    .query("SELECT name, roles FROM person WHERE $input IN name;")
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
                DbCommand::RawQuery(q) => match self.db.query(q).await {
                    Ok(mut c) => {
                        let mut response = String::new();
                        for i in 0..c.num_statements() {
                            match c.take::<Option<Value>>(i) {
                                Ok(v) => response.push_str(&v.unwrap_or(Value::None).to_sql_pretty()),
                                Err(e) => response.push_str(&e.to_string()),
                            }
                            response.push_str("\n");
                        }
                        self.response_sender.send(DbResponse::Other(response))?;
                    }
                    Err(e) => self.send_error(e)?,
                },
                DbCommand::Signup(q) => match self
                    .db
                    .signup(Record {
                        namespace: "main".to_string(),
                        database: "main".to_string(),
                        access: "account".to_string(),
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
                        namespace: "main".to_string(),
                        database: "main".to_string(),
                        access: "account".to_string(),
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
                        username: "root".to_string(),
                        password: "root".to_string(),
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
