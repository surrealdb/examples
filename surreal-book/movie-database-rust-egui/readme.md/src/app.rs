use std::sync::mpsc::{Receiver, Sender};

use egui::{
    Color32, Context, Event,
    FontFamily::Proportional,
    FontId, Rect, RichText, Style,
    TextStyle::{self, Body, Button, Heading, Monospace, Name, Small},
    Vec2, global_theme_preference_buttons,
};
use egui_extras::install_image_loaders;
use serde::{Deserialize, Serialize};

use crate::{Country, Movie, Person, db::DbResponse};

#[derive(Debug)]
// Commands sent from the app to the database
pub enum DbCommand {
    SelectPerson(String),
    SelectMovie {
        title: Option<String>,
        plot: Option<String>,
    },
    SelectCountry(String),
    RawQuery(String),
    Signin(UserInput),
    Signup(UserInput),
    Root,
}

pub struct MovieApp {
    pub current_movie: MovieBrief,
    pub movie: Movie,
    pub person: Person,
    pub country: Country,
    pub output: String,
    pub mode: Mode,
    pub loaded: bool,
    pub command_sender: Sender<DbCommand>,
    pub response_receiver: Receiver<DbResponse>,
    pub raw_query: String,
    pub font_size: f32,
    pub db_status: RichText,
}

#[derive(Debug, PartialEq, PartialOrd)]
pub enum Mode {
    Nothing,
    SelectPerson(String),
    SelectCountry(String),
    SelectMovie { title: String, plot: String },
    RawQuery,
    Signup(UserInput),
    Signin(UserInput),
    SigninRoot,
}

enum Font {
    Heading,
    Heading2,
    Context,
    Body,
    Monospace,
    Button,
    Small,
}

impl Font {
    fn with_size(self, font_size: f32) -> (TextStyle, FontId) {
        match self {
            Font::Heading => (Heading, FontId::new(font_size + 20.0, Proportional)),
            Font::Heading2 => (
                Name("Heading2".into()),
                FontId::new(font_size + 15.0, Proportional),
            ),
            Font::Context => (
                Name("Context".into()),
                FontId::new(font_size + 13.0, Proportional),
            ),
            Font::Monospace => (Monospace, FontId::new(font_size + 4.0, Proportional)),
            Font::Body => (Body, FontId::new(font_size + 8.0, Proportional)),
            Font::Button => (Button, FontId::new(font_size + 4.0, Proportional)),
            Font::Small => (Small, FontId::new(font_size, Proportional)),
        }
    }
}

impl MovieApp {
    fn send_command(&self, command: DbCommand) {
        if let Err(e) = self.command_sender.send(command) {
            eprintln!("Couldn't send commend: {e}");
        }
    }

    fn change_font(&mut self, style: &mut Style) {
        style.text_styles = [
            Font::Heading.with_size(self.font_size),
            Font::Heading2.with_size(self.font_size),
            Font::Context.with_size(self.font_size),
            Font::Body.with_size(self.font_size),
            Font::Monospace.with_size(self.font_size),
            Font::Button.with_size(self.font_size),
            Font::Small.with_size(self.font_size),
        ]
        .into();
    }
}

pub struct MovieBrief {
    poster: String,
    title: String,
    plot: String,
    year: String,
}

impl From<Movie> for MovieBrief {
    fn from(movie: Movie) -> Self {
        Self {
            poster: movie.poster,
            title: movie.title,
            plot: movie.plot,
            year: movie.released,
        }
    }
}

impl Default for MovieBrief {
    fn default() -> Self {
        Self {
            poster: "https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZmRlYWMwMWFmXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg/480".to_string(),
            title: "The Shawshank Redemption".into(),
            plot: "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.".into(),
            year: "1994".into()
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Default, Clone, PartialEq, PartialOrd)]
pub struct UserInput {
    name: String,
    pass: String,
}

fn key_pressed(ctx: &Context) -> bool {
    ctx.input(|i| {
        i.events
            .iter()
            .any(|event| matches!(event, Event::Key { pressed: true, .. }))
    })
}

impl eframe::App for MovieApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if !self.loaded {
            install_image_loaders(ctx);
            self.loaded = true;
        }

        if let Ok(msg) = self.response_receiver.try_recv() {
            match msg {
                DbResponse::RandomMovie(movie) => self.current_movie = MovieBrief::from(movie),
                DbResponse::Busy => {
                    self.db_status = RichText::new("Database status: Busy").color(Color32::RED)
                }
                DbResponse::Free => {
                    self.db_status = RichText::new("Database status: Free").color(Color32::GREEN)
                }
                // DbResponse::Info(m) => self.info = m,
                DbResponse::Movie(movies) => {
                    self.output = movies.into_iter().map(|m| m.to_string()).collect();
                }
                msg => self.output = format!("{msg}"),
            }
        }

        egui::TopBottomPanel::top("top panel").show(ctx, |ui| {
            self.change_font(ui.style_mut());
            global_theme_preference_buttons(ui);
            ui.separator();
            ui.add(egui::Slider::new(&mut self.font_size, 5.0..=35.0).text("Font size"));
            ui.separator();
            ui.label(self.db_status.clone());
            ui.separator();
            // Top buttons
            ui.horizontal(|ui| {
                // Select country
                ui.selectable_value(
                    &mut self.mode,
                    Mode::SelectCountry(String::new()),
                    "Select country",
                );
                ui.separator();
                // Select movie
                ui.selectable_value(
                    &mut self.mode,
                    Mode::SelectMovie {
                        title: String::new(),
                        plot: String::new(),
                    },
                    "Select movie",
                );
                ui.separator();
                // Select person
                ui.selectable_value(
                    &mut self.mode,
                    Mode::SelectPerson(String::new()),
                    "Select person",
                );
                ui.separator();
                // Signup
                ui.selectable_value(
                    &mut self.mode,
                    Mode::Signup(UserInput::default()),
                    "Create new user",
                );
                ui.separator();
                // Signin
                ui.selectable_value(
                    &mut self.mode,
                    Mode::Signin(UserInput::default()),
                    "Sign in as record user",
                );
                ui.separator();
                // Sign out
                ui.selectable_value(&mut self.mode, Mode::SigninRoot, "Sign in as root");
                ui.separator();
                // Raw query
                ui.selectable_value(&mut self.mode, Mode::RawQuery, "Raw query");
            });
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            self.change_font(ui.style_mut());

            ui.horizontal(|ui| {
                ui.vertical(|ui| {
                    if let Mode::SelectCountry(name) = &mut self.mode {
                        ui.label(
                            RichText::new("Movies for country:")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(name);
                    };

                    if let Mode::SelectMovie { title, plot } = &mut self.mode {
                        ui.label(
                            RichText::new("Movie title")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(title);
                        ui.label(
                            RichText::new("Movie plot")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(plot);
                    };

                    if let Mode::SelectPerson(name) = &mut self.mode {
                        ui.label(
                            RichText::new("Person name:")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(name);
                    };

                    if let Mode::Signup(input) = &mut self.mode {
                        ui.label(
                            RichText::new("Sign up with username:")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(&mut input.name);
                        ui.label(
                            RichText::new("Sign up with password:")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(&mut input.pass);
                    };

                    if let Mode::Signin(input) = &mut self.mode {
                        ui.label(
                            RichText::new("Sign in with name:")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(&mut input.name);
                        ui.label(
                            RichText::new("Sign in with password:")
                                .font(Font::Small.with_size(self.font_size).1),
                        );
                        ui.text_edit_singleline(&mut input.pass);
                    };

                    // Commands requiring user to click button to execute
                    match &self.mode {
                        Mode::RawQuery => {
                            ui.code_editor(&mut self.raw_query);
                            if ui.button("Execute raw query!").clicked() {
                                self.send_command(DbCommand::RawQuery(self.raw_query.clone()));
                            }
                        }
                        Mode::Signin(s) => {
                            if ui.button("Execute signin!").clicked() {
                                self.send_command(DbCommand::Signin(s.clone()));
                            }
                        }
                        Mode::Signup(s) => {
                            if ui.button("Execute signup!").clicked() {
                                self.send_command(DbCommand::Signup(s.clone()));
                            }
                        }
                        Mode::SigninRoot => {
                            if ui.button("Move back to Root").clicked() {
                                self.send_command(DbCommand::Root);
                            }
                        }
                        _ => {}
                    }
                });
            });

            ui.separator();

            ui.horizontal(|ui| {
                let Rect { min, max } = ctx.screen_rect();
                egui::ScrollArea::vertical()
                    .min_scrolled_height((max.y - min.y) / 2.2)
                    .show(ui, |ui| {
                        ui.vertical(|ui| {
                            ui.label("Latest output:");
                            ui.text_edit_multiline(&mut self.output);
                        });
                    });
            });

            ui.separator();

            let title = format!("{} ({})", self.current_movie.title, self.current_movie.year);
            ui.label(&title);
            ui.add(
                egui::Image::new(&self.current_movie.poster)
                    .show_loading_spinner(true)
                    .max_width(200.0)
                    .corner_radius(10.0)
                    .fit_to_exact_size(Vec2 { x: 500.0, y: 500.0 }),
            );
            ui.label(
                RichText::new(&self.current_movie.plot)
                    .font(FontId::new(self.font_size, Proportional)),
            );

            // ==============
            // UI all drawn, send commands for actions not requiring user to click button
            match &self.mode {
                Mode::SelectMovie { title, plot } => {
                    if (!title.is_empty() || !plot.is_empty()) && key_pressed(ctx) {
                        self.send_command(DbCommand::SelectMovie {
                            title: if title.is_empty() {
                                None
                            } else {
                                Some(title.clone())
                            },
                            plot: if plot.is_empty() {
                                None
                            } else {
                                Some(plot.clone())
                            },
                        });
                    }
                }
                Mode::SelectCountry(name) => {
                    if !name.is_empty() && key_pressed(ctx) {
                        self.send_command(DbCommand::SelectCountry(name.clone()));
                    }
                }
                Mode::SelectPerson(name) => {
                    if !name.is_empty() && key_pressed(ctx) {
                        self.send_command(DbCommand::SelectPerson(name.clone()));
                    }
                }
                _ => {}
            }
        });
    }
}