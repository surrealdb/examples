#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")] // hide console window on Windows in release
#![allow(unreachable_code)]

use std::{
    sync::mpsc,
    thread,
    time::{self, Instant},
};

use anyhow::Error;
use eframe::egui;

use egui::{Color32, RichText};
use surrealbook::{
    Country, Movie, Person,
    app::{Mode, MovieApp, MovieBrief},
    db::{Database, DbResponse},
};
use surrealdb::engine::any::connect;
use tokio::runtime::Runtime;

fn main() -> Result<(), Error> {
    let (command_sender, command_receiver) = mpsc::channel();
    let (response_sender, response_receiver) = mpsc::channel();

    thread::spawn(|| {
        let rt = Runtime::new().expect("Oops runtime");
        if let Err(e) = rt.block_on(async {
            let db = connect("memory").await?;

            db.use_ns("movies").use_db("movies").await?;
            db.query(surrealbook::INIT).await?;

            let mut database = Database {
                db,
                command_receiver,
                response_sender,
                clock: Instant::now(),
            };

            loop {
                if let Err(e) = database.receive().await {
                    println!("Error receiving: {e}");
                }
                if Instant::now() - database.clock > time::Duration::from_secs(4) {
                    match database.get_random_movie().await {
                        Ok(random_movie) => {
                            database.clock = Instant::now();
                            database
                                .response_sender
                                .send(DbResponse::RandomMovie(random_movie))?
                        }
                        Err(e) => panic!("Couldn't get random movie: {e}"),
                    };
                }
            }
            Ok::<(), Error>(())
        }) {
            panic!("Database error, shutting down: {e}");
        }
    });

    let app = MovieApp {
        current_movie: MovieBrief::default(),
        movie: Movie::default(),
        person: Person::default(),
        country: Country::default(),
        output: String::new(),
        mode: Mode::Nothing,
        loaded: false,
        command_sender,
        response_receiver,
        raw_query: String::new(),
        font_size: 15.0,
        db_status: RichText::new("Database status: Free").color(Color32::DARK_GREEN),
    };

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder {
            maximized: Some(true),
            ..Default::default()
        },
        ..Default::default()
    };

    eframe::run_native("Movie database", options, Box::new(|_cc| Ok(Box::new(app)))).unwrap();
    Ok(())
}