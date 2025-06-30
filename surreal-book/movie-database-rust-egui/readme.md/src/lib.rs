pub mod app;
pub mod db;

use std::fmt::Display;

use serde::{Deserialize, Serialize};
use surrealdb::sql::Duration;

#[derive(Clone, Default, Serialize, Deserialize, Debug)]
pub struct Movie {
    average_rating: f64,
    #[serde(default)]
    awards: String,
    #[serde(default)]
    boxoffice: i32,
    #[serde(default)]
    dvd_released: String,
    genres: String,
    languages: String,
    poster: String,
    plot: String,
    released: String,
    runtime: Duration,
    title: String,
}

impl Display for Movie {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let Movie {
            average_rating,
            awards,
            boxoffice,
            genres,
            languages,
            plot,
            released,
            runtime,
            title,
            ..
        } = self;

        write!(
            f,
            "
		{title} ({released})
		Genres: {genres}
		Rating: {average_rating}
		Languages: {languages}
		Box office: {boxoffice}
		Runtime: {runtime}
		Plot: {plot}
		Awards: {awards}
		"
        )
    }
}

#[derive(Clone, Serialize, Deserialize, Debug, Default)]
pub struct Country {
    name: String,
    movies: Vec<MovieBrief>,
}

#[derive(Clone, Serialize, Deserialize, Debug, Default)]
struct MovieBrief {
    title: String,
    released: String,
}

#[derive(Serialize, Deserialize, Debug, Default, Clone)]
pub struct Person {
    name: String,
    roles: String,
}

pub const INIT: &str = r#"DEFINE NAMESPACE IF NOT EXISTS movies;
USE NAMESPACE movies;
DEFINE DATABASE IF NOT EXISTS movies CHANGEFEED 3d;
USE DATABASE movies;

IF !$INITIATED {
DEFINE USER owner  ON DATABASE PASSWORD "owner"  ROLES OWNER;
DEFINE USER editor ON DATABASE PASSWORD "editor" ROLES EDITOR;
DEFINE USER viewer ON DATABASE PASSWORD "viewer" ROLES VIEWER;

DEFINE PARAM $GENRES  VALUE ['Action','Adventure', 'Animation',	'Biography', 'Comedy',	'Crime', 'Drama', 'Family',	'Fantasy', 'Film-Noir',	'History', 'Horror', 'Music', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War',	'Western'];
DEFINE PARAM $RATINGS VALUE ['Approved', 'G', 'Not Rated', 'PG', 'PG-13', 'Passed', 'R', 'TV-PG', 'Unrated', 'X'];

// movie table
DEFINE TABLE movie SCHEMAFULL TYPE NORMAL PERMISSIONS FOR select WHERE $auth.id IS NOT NONE FOR create, update, delete WHERE created_by = $auth.id;
DEFINE FIELD awards            ON TABLE movie TYPE option<string>;
DEFINE FIELD box_office        ON TABLE movie TYPE option<int>;
DEFINE FIELD dvd_released      ON TABLE movie TYPE option<datetime>;
DEFINE FIELD genres            ON TABLE movie TYPE array<string>     ASSERT $value ALLINSIDE $GENRES;
DEFINE FIELD imdb_rating       ON TABLE movie TYPE option<int>;
DEFINE FIELD languages         ON TABLE movie TYPE array<string>;
DEFINE FIELD metacritic_rating ON TABLE movie TYPE option<int>;
DEFINE FIELD oscars_won        ON TABLE movie TYPE option<int>;
DEFINE FIELD plot              ON TABLE movie TYPE string;
DEFINE FIELD poster            ON TABLE movie TYPE option<string>    ASSERT $value IS NONE OR $value.is_url();
DEFINE FIELD rated             ON TABLE movie TYPE option<string>    ASSERT $value IN $RATINGS;
DEFINE FIELD released          ON TABLE movie TYPE datetime;
DEFINE FIELD rt_rating         ON TABLE movie TYPE option<int>;
DEFINE FIELD runtime           ON TABLE movie TYPE duration;
DEFINE FIELD title             ON TABLE movie TYPE string;
DEFINE FIELD created_by        ON TABLE movie TYPE option<record<user>> READONLY VALUE $auth.id;
DEFINE FIELD average_rating    ON TABLE movie 
	VALUE math::mean([$this.imdb_rating, $this.metacritic_rating, $this.rt_rating][WHERE $this IS NOT NONE]);

// person table
DEFINE TABLE person SCHEMAFULL TYPE NORMAL  PERMISSIONS FOR select WHERE $auth.id IS NOT NONE FOR create, update, delete WHERE created_by = $auth.id;
DEFINE FIELD name ON TABLE person TYPE string;
DEFINE FIELD roles ON person TYPE array<string>;
DEFINE FIELD created_by        ON TABLE person TYPE option<record<user>> READONLY VALUE $auth.id;

// country table
DEFINE TABLE country SCHEMAFULL TYPE NORMAL  PERMISSIONS FOR select WHERE $auth.id IS NOT NONE FOR create, update, delete WHERE created_by = $auth.id;
DEFINE FIELD name ON TABLE country TYPE string;
DEFINE FIELD created_by        ON TABLE country TYPE option<record<user>> READONLY VALUE $auth.id;

// Relations
DEFINE TABLE starred_in TYPE RELATION FROM person  TO movie PERMISSIONS FOR select WHERE $auth.id IS NOT NONE FOR create, update, delete WHERE created_by = $auth.id;
DEFINE TABLE wrote      TYPE RELATION FROM person  TO movie PERMISSIONS FOR select WHERE $auth.id IS NOT NONE FOR create, update, delete WHERE created_by = $auth.id;
DEFINE TABLE directed   TYPE RELATION FROM person  TO movie PERMISSIONS FOR select WHERE $auth.id IS NOT NONE FOR create, update, delete WHERE created_by = $auth.id;
DEFINE TABLE has_movie  TYPE RELATION FROM country TO movie PERMISSIONS FOR select WHERE $auth.id IS NOT NONE FOR create, update, delete WHERE created_by = $auth.id;

DEFINE FIELD created_by ON TABLE starred_in TYPE option<record<user>> READONLY VALUE $auth.id;
DEFINE FIELD created_by ON TABLE wrote      TYPE option<record<user>> READONLY VALUE $auth.id;
DEFINE FIELD created_by ON TABLE directed   TYPE option<record<user>> READONLY VALUE $auth.id;
DEFINE FIELD created_by ON TABLE has_movie  TYPE option<record<user>> READONLY VALUE $auth.id;

// Record users and access
DEFINE TABLE user SCHEMAFULL
    PERMISSIONS FOR select WHERE $auth.id = id;

DEFINE FIELD name    ON TABLE user          TYPE string;
DEFINE FIELD pass    ON TABLE user          TYPE string;
DEFINE FIELD actions ON TABLE user FLEXIBLE TYPE option<array<object>>;

DEFINE INDEX unique_name ON TABLE user FIELDS name UNIQUE;

DEFINE ACCESS account ON DATABASE TYPE RECORD
	SIGNUP ( CREATE user SET name = $name, pass = crypto::argon2::generate($pass) )
	SIGNIN ( SELECT * FROM user WHERE name = $name AND crypto::argon2::compare(pass, $pass) )
	DURATION FOR TOKEN 15m, FOR SESSION 12h;

// Full text search
DEFINE ANALYZER movie_fts TOKENIZERS class FILTERS ascii, lowercase, edgengram(2,10);
DEFINE INDEX plot_index  ON TABLE movie FIELDS plot  SEARCH ANALYZER movie_fts BM25 HIGHLIGHTS;
DEFINE INDEX title_index ON TABLE movie FIELDS title SEARCH ANALYZER movie_fts BM25;
DEFINE INDEX person_index ON TABLE person FIELDS name SEARCH ANALYZER movie_fts BM25;

// Events
DEFINE EVENT soft_deletion ON TABLE movie WHEN $event = "DELETE" THEN {
    CREATE deleted_movie CONTENT $before;
};

DEFINE EVENT movie_activity ON TABLE movie WHEN $auth.id IS NOT NONE THEN {
	UPDATE $auth.id SET	
        actions += {
            event: $event,
            input: $value,
            at: time::now()
        }
};

DEFINE EVENT country_activity ON TABLE country WHEN $auth.id IS NOT NONE THEN {
	UPDATE $auth.id SET	
        actions += {
            event: $event,
            input: $value,
            at: time::now()
        }
};

DEFINE EVENT person_activity ON TABLE person WHEN $auth.id IS NOT NONE THEN {
	UPDATE $auth.id SET	
        actions += {
            event: $event,
            input: $value,
            at: time::now()
        }
};

DEFINE FUNCTION fn::date_to_datetime($input: string) -> datetime {
    LET $split = $input.split(' ');
    RETURN <datetime>($split[2] + '-' + fn::month_to_num($split[1]) + '-' + $split[0]);
} PERMISSIONS NONE;

DEFINE FUNCTION fn::month_to_num($input: string) -> string {
    RETURN 
        IF      $input = 'Jan' { '01' }
        ELSE IF $input = 'Feb' { '02' }
        ELSE IF $input = 'Mar' { '03' }
        ELSE IF $input = 'Apr' { '04' }
        ELSE IF $input = 'May' { '05' }
        ELSE IF $input = 'Jun' { '06' }
        ELSE IF $input = 'Jul' { '07' }
        ELSE IF $input = 'Aug' { '08' }
        ELSE IF $input = 'Sep' { '09' }
        ELSE IF $input = 'Oct' { '10' }
        ELSE IF $input = 'Nov' { '11' }
        ELSE IF $input = 'Dec' { '12' }
        ELSE {
            THROW "Invalid input: `" + $input + "`. Please enter an abbreviated three-letter such as 'Oct'."
        }
} PERMISSIONS NONE;

DEFINE FUNCTION fn::get_imdb($obj: array<object>) -> option<number> {
    LET $data = (SELECT VALUE Score FROM ONLY $obj WHERE Source = 'Internet Movie Database' LIMIT 1);
    RETURN IF $data IS NONE { NONE } ELSE { <number>$data.replace('/10', '') * 10 }
} PERMISSIONS NONE;

DEFINE FUNCTION fn::get_rt($obj: array<object>) -> option<number> {
    LET $data = (SELECT VALUE Score FROM ONLY $obj WHERE Source = 'Rotten Tomatoes' LIMIT 1);
    RETURN IF $data IS NONE { NONE } ELSE { <number>$data.replace('%', '') }
} PERMISSIONS NONE;

DEFINE FUNCTION fn::get_metacritic($obj: array<object>) -> option<number> {
    LET $data = (SELECT VALUE Score FROM ONLY $obj WHERE Source = 'Metacritic' LIMIT 1);
    RETURN IF $data IS NONE { NONE } ELSE { <number>$data.replace('/100', '') }
} PERMISSIONS NONE;

DEFINE FUNCTION fn::get_oscars($input: string) -> option<int> {
	RETURN IF $input.starts_with('Won ') AND 'Oscar' in $input {
    	let $input = $input.replace('Won ', '');
    	<int>$input.split(' Oscar')[0]
	} ELSE {
    	NONE
	}
} PERMISSIONS NONE;

DEFINE FUNCTION fn::random_movie() {
    LET $random_genre = rand::enum($GENRES);
    LET $random_rating = rand::enum($RATINGS);
    LET $title = RETURN "Movies for " + $random_genre + " and " + $random_rating;
    RETURN [$title, (SELECT * FROM movie WHERE $random_genre IN genres and $random_rating IN rated)];    
} PERMISSIONS FULL;

INSERT INTO naive_movie [
	{
		Actors: 'Tim Robbins, Morgan Freeman, Bob Gunton',
		Awards: 'Nominated for 7 Oscars. 21 wins & 43 nominations total',
		BoxOffice: '$28,767,189',
		Country: 'United States',
		DVD: '21 Dec 1999',
		Director: 'Frank Darabont',
		Genre: 'Drama',
		Language: 'English',
		Plot: 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZmRlYWMwMWFmXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '9.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '91%'
			},
			{
				Source: 'Metacritic',
				Score: '81/100'
			}
		],
		Released: '14 Oct 1994',
		Runtime: '142 min',
		Title: 'The Shawshank Redemption',
		Writer: 'Stephen King, Frank Darabont',
	},
	{
		Actors: 'Marlon Brando, Al Pacino, James Caan',
		Awards: 'Won 3 Oscars. 31 wins & 30 nominations total',
		BoxOffice: '$136,381,073',
		Country: 'United States',
		DVD: '11 May 2004',
		Director: 'Francis Ford Coppola',
		Genre: 'Crime, Drama',
		Language: 'English, Italian, Latin',
		Plot: 'The aging patriarch of an organized crime dynasty in postwar New York City transfers control of his clandestine empire to his reluctant youngest son.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '9.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '100/100'
			}
		],
		Released: '24 Mar 1972',
		Runtime: '175 min',
		Title: 'The Godfather',
		Writer: 'Mario Puzo, Francis Ford Coppola',
	},
	{
		Actors: 'Christian Bale, Heath Ledger, Aaron Eckhart',
		Awards: 'Won 2 Oscars. 159 wins & 163 nominations total',
		BoxOffice: '$534,987,076',
		Country: 'United States, United Kingdom',
		DVD: '09 Dec 2008',
		Director: 'Christopher Nolan',
		Genre: 'Action, Crime, Drama',
		Language: 'English, Mandarin',
		Plot: 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '9.1/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '84/100'
			}
		],
		Released: '18 Jul 2008',
		Runtime: '152 min',
		Title: 'The Dark Knight',
		Writer: 'Jonathan Nolan, Christopher Nolan, David S. Goyer',
	},
	{
		Actors: 'Al Pacino, Robert De Niro, Robert Duvall',
		Awards: 'Won 6 Oscars. 17 wins & 20 nominations total',
		BoxOffice: '$47,834,595',
		Country: 'United States',
		DVD: '24 May 2005',
		Director: 'Francis Ford Coppola',
		Genre: 'Crime, Drama',
		Language: 'English, Italian, Spanish, Latin, Sicilian',
		Plot: 'The early life and career of Vito Corleone in 1920s New York City is portrayed, while his son, Michael, expands and tightens his grip on the family crime syndicate.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMWMwMGQzZTItY2JlNC00OWZiLWIyMDctNDk2ZDQ2YjRjMWQ0XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '9.0/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '18 Dec 1974',
		Runtime: '202 min',
		Title: 'The Godfather: Part II',
		Writer: 'Francis Ford Coppola, Mario Puzo',
	},
	{
		Actors: 'Henry Fonda, Lee J. Cobb, Martin Balsam',
		Awards: 'Nominated for 3 Oscars. 17 wins & 13 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '04 Mar 2008',
		Director: 'Sidney Lumet',
		Genre: 'Crime, Drama',
		Language: 'English',
		Plot: 'The jury in a New York City murder trial is frustrated by a single member whose skeptical caution forces them to more carefully consider the evidence before jumping to a hasty verdict.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMWU4N2FjNzYtNTVkNC00NzQ0LTg0MjAtYTJlMjFhNGUxZDFmXkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '9.0/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '100%'
			},
			{
				Source: 'Metacritic',
				Score: '96/100'
			}
		],
		Released: '10 Apr 1957',
		Runtime: '96 min',
		Title: '12 Angry Men',
		Writer: 'Reginald Rose',
	},
	{
		Actors: 'Liam Neeson, Ralph Fiennes, Ben Kingsley',
		Awards: 'Won 7 Oscars. 91 wins & 49 nominations total',
		BoxOffice: '$96,898,818',
		Country: 'United States',
		DVD: '12 Feb 2008',
		Director: 'Steven Spielberg',
		Genre: 'Biography, Drama, History',
		Language: 'English, Hebrew, German, Polish, Latin',
		Plot: 'In German-occupied Poland during World War II, industrialist Oskar Schindler gradually becomes concerned for his Jewish workforce after witnessing their persecution by the Nazis.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNDE4OTMxMTctNmRhYy00NWE2LTg3YzItYTk3M2UwOTU5Njg4XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.9/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '94/100'
			}
		],
		Released: '04 Feb 1994',
		Runtime: '195 min',
		Title: "Schindler's List",
		Writer: 'Thomas Keneally, Steven Zaillian',
	},
	{
		Actors: 'Elijah Wood, Viggo Mortensen, Ian McKellen',
		Awards: 'Won 11 Oscars. 209 wins & 124 nominations total',
		BoxOffice: '$378,251,207',
		Country: 'New Zealand, United States',
		DVD: '25 May 2004',
		Director: 'Peter Jackson',
		Genre: 'Action, Adventure, Drama',
		Language: 'English, Quenya, Old English, Sindarin',
		Plot: "Gandalf and Aragorn lead the World of Men against Sauron's army to draw his gaze from Frodo and Sam as they approach Mount Doom with the One Ring.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNzA5ZDNlZWMtM2NhNS00NDJjLTk4NDItYTRmY2EwMWZlMTY3XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '9.0/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '94/100'
			}
		],
		Released: '17 Dec 2003',
		Runtime: '201 min',
		Title: 'The Lord of the Rings: The Return of the King',
		Writer: 'J.R.R. Tolkien, Fran Walsh, Philippa Boyens',
	},
	{
		Actors: 'John Travolta, Uma Thurman, Samuel L. Jackson',
		Awards: 'Won 1 Oscar. 70 wins & 75 nominations total',
		BoxOffice: '$107,928,762',
		Country: 'United States',
		DVD: '20 Aug 2002',
		Director: 'Quentin Tarantino',
		Genre: 'Crime, Drama',
		Language: 'English, Spanish, French',
		Plot: 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.9/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			},
			{
				Source: 'Metacritic',
				Score: '94/100'
			}
		],
		Released: '14 Oct 1994',
		Runtime: '154 min',
		Title: 'Pulp Fiction',
		Writer: 'Quentin Tarantino, Roger Avary',
	},
	{
		Actors: 'Elijah Wood, Ian McKellen, Orlando Bloom',
		Awards: 'Won 4 Oscars. 121 wins & 126 nominations total',
		BoxOffice: '$316,115,420',
		Country: 'New Zealand, United States',
		DVD: '06 Aug 2002',
		Director: 'Peter Jackson',
		Genre: 'Action, Adventure, Drama',
		Language: 'English, Sindarin',
		Plot: 'A meek Hobbit from the Shire and eight companions set out on a journey to destroy the powerful One Ring and save Middle-earth from the Dark Lord Sauron.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BN2EyZjM3NzUtNWUzMi00MTgxLWI0NTctMzY4M2VlOTdjZWRiXkEyXkFqcGdeQXVyNDUzOTQ5MjY@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.8/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '91%'
			},
			{
				Source: 'Metacritic',
				Score: '92/100'
			}
		],
		Released: '19 Dec 2001',
		Runtime: '178 min',
		Title: 'The Lord of the Rings: The Fellowship of the Ring',
		Writer: 'J.R.R. Tolkien, Fran Walsh, Philippa Boyens',
	},
	{
		Actors: 'Clint Eastwood, Eli Wallach, Lee Van Cleef',
		Awards: '3 wins & 6 nominations',
		BoxOffice: '$25,100,000',
		Country: 'Italy, Spain, West Germany',
		DVD: '07 Nov 2006',
		Director: 'Sergio Leone',
		Genre: 'Adventure, Western',
		Language: 'Italian',
		Plot: 'A bounty hunting scam joins two men in an uneasy alliance against a third in a race to find a fortune in gold buried in a remote cemetery.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNjJlYmNkZGItM2NhYy00MjlmLTk5NmQtNjg1NmM2ODU4OTMwXkEyXkFqcGdeQXVyMjUzOTY1NTc@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.8/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '29 Dec 1967',
		Runtime: '178 min',
		Title: 'The Good, the Bad and the Ugly',
		Writer: 'Luciano Vincenzoni, Sergio Leone, Agenore Incrocci',
	},
	{
		Actors: 'Tom Hanks, Robin Wright, Gary Sinise',
		Awards: 'Won 6 Oscars. 50 wins & 75 nominations total',
		BoxOffice: '$330,455,270',
		Country: 'United States',
		DVD: '28 Aug 2001',
		Director: 'Robert Zemeckis',
		Genre: 'Drama, Romance',
		Language: 'English',
		Plot: 'The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75, whose only desire is to be reunited with his childhood sweeth',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNWIwODRlZTUtY2U3ZS00Yzg1LWJhNzYtMmZiYmEyNmU1NjMzXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.8/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '70%'
			},
			{
				Source: 'Metacritic',
				Score: '82/100'
			}
		],
		Released: '06 Jul 1994',
		Runtime: '142 min',
		Title: 'Forrest Gump',
		Writer: 'Winston Groom, Eric Roth',
	},
	{
		Actors: 'Brad Pitt, Edward Norton, Meat Loaf',
		Awards: 'Nominated for 1 Oscar. 11 wins & 38 nominations total',
		BoxOffice: '$37,030,102',
		Country: 'United States, Germany',
		DVD: '14 Oct 2003',
		Director: 'David Fincher',
		Genre: 'Drama',
		Language: 'English',
		Plot: 'An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into much more.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNDIzNDU0YzEtYzE5Ni00ZjlkLTk5ZjgtNjM3NWE4YzA3Nzk3XkEyXkFqcGdeQXVyMjUzOTY1NTc@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.8/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '79%'
			},
			{
				Source: 'Metacritic',
				Score: '66/100'
			}
		],
		Released: '15 Oct 1999',
		Runtime: '139 min',
		Title: 'Fight Club',
		Writer: 'Chuck Palahniuk, Jim Uhls',
	},
	{
		Actors: 'Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page',
		Awards: 'Won 4 Oscars. 157 wins & 220 nominations total',
		BoxOffice: '$292,587,330',
		Country: 'United States, United Kingdom',
		DVD: '07 Dec 2010',
		Director: 'Christopher Nolan',
		Genre: 'Action, Adventure, Sci-Fi',
		Language: 'English, Japanese, French',
		Plot: 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O., but his tragic past may doom the project and his team to disaster.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.8/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '87%'
			},
			{
				Source: 'Metacritic',
				Score: '74/100'
			}
		],
		Released: '16 Jul 2010',
		Runtime: '148 min',
		Title: 'Inception',
		Writer: 'Christopher Nolan',
	},
	{
		Actors: 'Elijah Wood, Ian McKellen, Viggo Mortensen',
		Awards: 'Won 2 Oscars. 126 wins & 138 nominations total',
		BoxOffice: '$342,952,511',
		Country: 'New Zealand, United States',
		DVD: '26 Aug 2003',
		Director: 'Peter Jackson',
		Genre: 'Action, Adventure, Drama',
		Language: 'English, Sindarin, Old English',
		Plot: "While Frodo and Sam edge closer to Mordor with the help of the shifty Gollum, the divided fellowship makes a stand against Sauron's new ally, Saruman, and his hordes of Isengard.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BZGMxZTdjZmYtMmE2Ni00ZTdkLWI5NTgtNjlmMjBiNzU2MmI5XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.7/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '87/100'
			}
		],
		Released: '18 Dec 2002',
		Runtime: '179 min',
		Title: 'The Lord of the Rings: The Two Towers',
		Writer: 'J.R.R. Tolkien, Fran Walsh, Philippa Boyens',
	},
	{
		Actors: 'Mark Hamill, Harrison Ford, Carrie Fisher',
		Awards: 'Won 2 Oscars. 25 wins & 20 nominations total',
		BoxOffice: '$292,753,960',
		Country: 'United States',
		DVD: '21 Sep 2004',
		Director: 'Irvin Kershner',
		Genre: 'Action, Adventure, Fantasy',
		Language: 'English',
		Plot: 'After the Rebels are brutally overpowered by the Empire on the ice planet Hoth, Luke Skywalker begins Jedi training with Yoda, while his friends are pursued across the galaxy by Darth Vader and bounty hunter Boba Fett.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYmU1NDRjNDgtMzhiMi00NjZmLTg5NGItZDNiZjU5NTU4OTE0XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.7/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '82/100'
			}
		],
		Released: '20 Jun 1980',
		Runtime: '124 min',
		Title: 'Star Wars: Episode V - The Empire Strikes Back',
		Writer: 'Leigh Brackett, Lawrence Kasdan, George Lucas',
	},
	{
		Actors: 'Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss',
		Awards: 'Won 4 Oscars. 42 wins & 51 nominations total',
		BoxOffice: '$172,076,928',
		Country: 'United States, Australia',
		DVD: '15 May 2007',
		Director: 'Lana Wachowski, Lilly Wachowski',
		Genre: 'Action, Sci-Fi',
		Language: 'English',
		Plot: 'When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth--the life he knows is the elaborate deception of an evil cyber-intelligence.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.7/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '88%'
			},
			{
				Source: 'Metacritic',
				Score: '73/100'
			}
		],
		Released: '31 Mar 1999',
		Runtime: '136 min',
		Title: 'The Matrix',
		Writer: 'Lilly Wachowski, Lana Wachowski',
	},
	{
		Actors: 'Robert De Niro, Ray Liotta, Joe Pesci',
		Awards: 'Won 1 Oscar. 44 wins & 38 nominations total',
		BoxOffice: '$46,909,721',
		Country: 'United States',
		DVD: '22 Aug 1997',
		Director: 'Martin Scorsese',
		Genre: 'Biography, Crime, Drama',
		Language: 'English, Italian',
		Plot: 'The story of Henry Hill and his life in the mob, covering his relationship with his wife Karen Hill and his mob partners Jimmy Conway and Tommy DeVito in the Italian-American crime syndicate.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BY2NkZjEzMDgtN2RjYy00YzM1LWI4ZmQtMjIwYjFjNmI3ZGEwXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.7/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '21 Sep 1990',
		Runtime: '145 min',
		Title: 'Goodfellas',
		Writer: 'Nicholas Pileggi, Martin Scorsese',
	},
	{
		Actors: 'Jack Nicholson, Louise Fletcher, Michael Berryman',
		Awards: 'Won 5 Oscars. 38 wins & 16 nominations total',
		BoxOffice: '$108,981,275',
		Country: 'United States',
		DVD: '16 Dec 1997',
		Director: 'Milos Forman',
		Genre: 'Drama',
		Language: 'English',
		Plot: 'A criminal pleads insanity and is admitted to a mental institution, where he rebels against the oppressive nurse and rallies up the scared patients.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZjA0OWVhOTAtYWQxNi00YzNhLWI4ZjYtNjFjZTEyYjJlNDVlL2ltYWdlL2ltYWdlXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.7/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '84/100'
			}
		],
		Released: '19 Nov 1975',
		Runtime: '133 min',
		Title: "One Flew Over the Cuckoo's Nest",
		Writer: 'Lawrence Hauben, Bo Goldman, Ken Kesey',
	},
	{
		Actors: 'Morgan Freeman, Brad Pitt, Kevin Spacey',
		Awards: 'Nominated for 1 Oscar. 29 wins & 43 nominations total',
		BoxOffice: '$100,125,643',
		Country: 'United States',
		DVD: '19 Dec 2000',
		Director: 'David Fincher',
		Genre: 'Crime, Drama, Mystery',
		Language: 'English',
		Plot: 'Two detectives, a rookie and a veteran, hunt a serial killer who uses the seven deadly sins as his motives.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTUwODM5MTctZjczMi00OTk4LTg3NWUtNmVhMTAzNTNjYjcyXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '82%'
			},
			{
				Source: 'Metacritic',
				Score: '65/100'
			}
		],
		Released: '22 Sep 1995',
		Runtime: '127 min',
		Title: 'Se7en',
		Writer: 'Andrew Kevin Walker',
	},
	{
		Actors: 'Toshirô Mifune, Takashi Shimura, Keiko Tsushima',
		Awards: 'Nominated for 2 Oscars. 5 wins & 8 nominations total',
		BoxOffice: '$318,649',
		Country: 'Japan',
		DVD: '05 Sep 2006',
		Director: 'Akira Kurosawa',
		Genre: 'Action, Drama',
		Language: 'Japanese',
		Plot: 'A poor village under attack by bandits recruits seven unemployed samurai to help them defend themselves.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOWE4ZDdhNmMtNzE5ZC00NzExLTlhNGMtY2ZhYjYzODEzODA1XkEyXkFqcGdeQXVyNTAyODkwOQ@@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Metacritic',
				Score: '98/100'
			}
		],
		Released: '19 Nov 1956',
		Runtime: '207 min',
		Title: 'Seven Samurai',
		Writer: 'Akira Kurosawa, Shinobu Hashimoto, Hideo Oguni',
	},
	{
		Actors: 'James Stewart, Donna Reed, Lionel Barrymore',
		Awards: 'Nominated for 5 Oscars. 6 wins & 6 nominations total',
		BoxOffice: '$44,000',
		Country: 'United States',
		DVD: '13 Jul 2004',
		Director: 'Frank Capra',
		Genre: 'Drama, Family, Fantasy',
		Language: 'English, French',
		Plot: 'An angel is sent from Heaven to help a desperately frustrated businessman by showing him what life would have been like if he had never existed.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZjc4NDZhZWMtNGEzYS00ZWU2LThlM2ItNTA0YzQ0OTExMTE2XkEyXkFqcGdeQXVyNjUwMzI2NzU@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.7/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '89/100'
			}
		],
		Released: '07 Jan 1947',
		Runtime: '130 min',
		Title: "It's a Wonderful Life",
		Writer: 'Frances Goodrich, Albert Hackett, Frank Capra',
	},
	{
		Actors: 'Jodie Foster, Anthony Hopkins, Lawrence A. Bonney',
		Awards: 'Won 5 Oscars. 69 wins & 51 nominations total',
		BoxOffice: '$130,742,922',
		Country: 'United States',
		DVD: '21 Aug 2001',
		Director: 'Jonathan Demme',
		Genre: 'Crime, Drama, Thriller',
		Language: 'English, Latin',
		Plot: 'A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer, a madman who skins his victims.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNjNhZTk0ZmEtNjJhMi00YzFlLWE1MmEtYzM1M2ZmMGMwMTU4XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '85/100'
			}
		],
		Released: '14 Feb 1991',
		Runtime: '118 min',
		Title: 'The Silence of the Lambs',
		Writer: 'Thomas Harris, Ted Tally',
	},
	{
		Actors: 'Tom Hanks, Matt Damon, Tom Sizemore',
		Awards: 'Won 5 Oscars. 79 wins & 75 nominations total',
		BoxOffice: '$217,049,603',
		Country: 'United States',
		DVD: '25 May 2004',
		Director: 'Steven Spielberg',
		Genre: 'Drama, War',
		Language: 'English, French, German, Czech',
		Plot: 'Following the Normandy Landings, a group of U.S. soldiers go behind enemy lines to retrieve a paratrooper whose brothers have been killed in action.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZjhkMDM4MWItZTVjOC00ZDRhLThmYTAtM2I5NzBmNmNlMzI1XkEyXkFqcGdeQXVyNDYyMDk5MTU@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '91/100'
			}
		],
		Released: '24 Jul 1998',
		Runtime: '169 min',
		Title: 'Saving Private Ryan',
		Writer: 'Robert Rodat',
	},
	{
		Actors: 'Alexandre Rodrigues, Leandro Firmino, Matheus Nachtergaele',
		Awards: 'Nominated for 4 Oscars. 74 wins & 50 nominations total',
		BoxOffice: '$7,564,459',
		Country: 'Brazil, France, Germany',
		DVD: '08 Jun 2004',
		Director: 'Fernando Meirelles, Kátia Lund',
		Genre: 'Crime, Drama',
		Language: 'Portuguese',
		Plot: "In the slums of Rio, two kids' paths diverge as one struggles to become a photographer and the other a kingpin.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTMwYjc5ZmItYTFjZC00ZGQ3LTlkNTMtMjZiNTZlMWQzNzI5XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '91%'
			},
			{
				Source: 'Metacritic',
				Score: '79/100'
			}
		],
		Released: '13 Feb 2004',
		Runtime: '130 min',
		Title: 'City of God',
		Writer: 'Paulo Lins, Bráulio Mantovani',
	},
	{
		Actors: 'Roberto Benigni, Nicoletta Braschi, Giorgio Cantarini',
		Awards: 'Won 3 Oscars. 72 wins & 52 nominations total',
		BoxOffice: '$57,563,264',
		Country: 'Italy',
		DVD: '09 Nov 1999',
		Director: 'Roberto Benigni',
		Genre: 'Comedy, Drama, Romance',
		Language: 'Italian, German, English',
		Plot: 'When an open-minded Jewish waiter and his son become victims of the Holocaust, he uses a perfect mixture of will, humor, and imagination to protect his son from the dangers around their camp.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYmJmM2Q4NmMtYThmNC00ZjRlLWEyZmItZTIwOTBlZDQ3NTQ1XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '80%'
			},
			{
				Source: 'Metacritic',
				Score: '59/100'
			}
		],
		Released: '20 Dec 1997',
		Runtime: '116 min',
		Title: 'Life Is Beautiful',
		Writer: 'Vincenzo Cerami, Roberto Benigni',
	},
	{
		Actors: 'Tom Hanks, Michael Clarke Duncan, David Morse',
		Awards: 'Nominated for 4 Oscars. 15 wins & 37 nominations total',
		BoxOffice: '$136,801,374',
		Country: 'United States',
		DVD: '13 Jun 2000',
		Director: 'Frank Darabont',
		Genre: 'Crime, Drama, Fantasy',
		Language: 'English, French',
		Plot: 'The lives of guards on Death Row are affected by one of their charges: a black man accused of child murder and rape, yet who has a mysterious gift.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTUxMzQyNjA5MF5BMl5BanBnXkFtZTYwOTU2NTY3._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '79%'
			},
			{
				Source: 'Metacritic',
				Score: '61/100'
			}
		],
		Released: '10 Dec 1999',
		Runtime: '189 min',
		Title: 'The Green Mile',
		Writer: 'Stephen King, Frank Darabont',
	},
	{
		Actors: 'Mark Hamill, Harrison Ford, Carrie Fisher',
		Awards: 'Won 7 Oscars. 63 wins & 29 nominations total',
		BoxOffice: '$460,998,507',
		Country: 'United States',
		DVD: '06 Dec 2005',
		Director: 'George Lucas',
		Genre: 'Action, Adventure, Fantasy',
		Language: 'English',
		Plot: "Luke Skywalker joins forces with a Jedi Knight, a cocky pilot, a Wookiee and two droids to save the galaxy from the Empire's world-destroying battle station, while also attempting to rescue Princess Leia from the mysterious Darth Vad",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNzVlY2MwMjktM2E4OS00Y2Y3LWE3ZjctYzhkZGM3YzA1ZWM2XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '25 May 1977',
		Runtime: '121 min',
		Title: 'Star Wars',
		Writer: 'George Lucas',
	},
	{
		Actors: 'Matthew McConaughey, Anne Hathaway, Jessica Chastain',
		Awards: 'Won 1 Oscar. 44 wins & 148 nominations total',
		BoxOffice: '$188,020,017',
		Country: 'United States, United Kingdom, Canada',
		DVD: '31 Mar 2015',
		Director: 'Christopher Nolan',
		Genre: 'Adventure, Drama, Sci-Fi',
		Language: 'English',
		Plot: "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDktN2IxOS00OGEyLWFmMjktY2FiMmZkNWIyODZiXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.7/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '72%'
			},
			{
				Source: 'Metacritic',
				Score: '74/100'
			}
		],
		Released: '07 Nov 2014',
		Runtime: '169 min',
		Title: 'Interstellar',
		Writer: 'Jonathan Nolan, Christopher Nolan',
	},
	{
		Actors: 'Arnold Schwarzenegger, Linda Hamilton, Edward Furlong',
		Awards: 'Won 4 Oscars. 36 wins & 33 nominations total',
		BoxOffice: '$205,881,154',
		Country: 'United States',
		DVD: '13 Feb 2007',
		Director: 'James Cameron',
		Genre: 'Action, Sci-Fi',
		Language: 'English, Spanish',
		Plot: 'A cyborg, identical to the one who failed to kill Sarah Connor, must now protect her ten-year-old son John from a more advanced and powerful cyborg.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMGU2NzRmZjUtOGUxYS00ZjdjLWEwZWItY2NlM2JhNjkxNTFmXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '75/100'
			}
		],
		Released: '03 Jul 1991',
		Runtime: '137 min',
		Title: 'Terminator 2: Judgment Day',
		Writer: 'James Cameron, William Wisher',
	},
	{
		Actors: 'Michael J. Fox, Christopher Lloyd, Lea Thompson',
		Awards: 'Won 1 Oscar. 22 wins & 25 nominations total',
		BoxOffice: '$212,836,762',
		Country: 'United States',
		DVD: '17 Aug 2010',
		Director: 'Robert Zemeckis',
		Genre: 'Adventure, Comedy, Sci-Fi',
		Language: 'English',
		Plot: 'Marty McFly, a 17-year-old high school student, is accidentally sent thirty years into the past in a time-traveling DeLorean invented by his close friend, the eccentric scientist Doc Brown.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZmU0M2Y1OGUtZjIxNi00ZjBkLTg1MjgtOWIyNThiZWIwYjRiXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '87/100'
			}
		],
		Released: '03 Jul 1985',
		Runtime: '116 min',
		Title: 'Back to the Future',
		Writer: 'Robert Zemeckis, Bob Gale',
	},
	{
		Actors: 'Daveigh Chase, Suzanne Pleshette, Miyu Irino',
		Awards: 'Won 1 Oscar. 58 wins & 31 nominations total',
		BoxOffice: '$13,750,644',
		Country: 'Japan',
		DVD: '15 Apr 2003',
		Director: 'Hayao Miyazaki',
		Genre: 'Animation, Adventure, Family',
		Language: 'Japanese, English',
		Plot: "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjlmZmI5MDctNDE2YS00YWE0LWE5ZWItZDBhYWQ0NTcxNWRhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '96/100'
			}
		],
		Released: '28 Mar 2003',
		Runtime: '125 min',
		Title: 'Spirited Away',
		Writer: 'Hayao Miyazaki',
	},
	{
		Actors: 'Anthony Perkins, Janet Leigh, Vera Miles',
		Awards: 'Nominated for 4 Oscars. 7 wins & 14 nominations total',
		BoxOffice: '$32,000,000',
		Country: 'United States',
		DVD: '04 Oct 2005',
		Director: 'Alfred Hitchcock',
		Genre: 'Horror, Mystery, Thriller',
		Language: 'English',
		Plot: "A Phoenix secretary embezzles $40,000 from her employer's client, goes on the run, and checks into a remote motel run by a young man under the domination of his mother.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNTQwNDM1YzItNDAxZC00NWY2LTk0M2UtNDIwNWI5OGUyNWUxXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '97/100'
			}
		],
		Released: '08 Sep 1960',
		Runtime: '109 min',
		Title: 'Psycho',
		Writer: 'Joseph Stefano, Robert Bloch',
	},
	{
		Actors: 'Adrien Brody, Thomas Kretschmann, Frank Finlay',
		Awards: 'Won 3 Oscars. 57 wins & 74 nominations total',
		BoxOffice: '$32,572,577',
		Country: 'France, Germany, Poland, United Kingdom',
		DVD: '27 May 2003',
		Director: 'Roman Polanski',
		Genre: 'Biography, Drama, Music',
		Language: 'English, German, Russian',
		Plot: 'A Polish Jewish musician struggles to survive the destruction of the Warsaw ghetto of World War II.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOWRiZDIxZjktMTA1NC00MDQ2LWEzMjUtMTliZmY3NjQ3ODJiXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '85/100'
			}
		],
		Released: '28 Mar 2003',
		Runtime: '150 min',
		Title: 'The Pianist',
		Writer: 'Ronald Harwood, Wladyslaw Szpilman',
	},
	{
		Actors: 'Jean Reno, Gary Oldman, Natalie Portman',
		Awards: '6 wins & 15 nominations',
		BoxOffice: '$19,501,238',
		Country: 'France, United States',
		DVD: '24 Feb 1998',
		Director: 'Luc Besson',
		Genre: 'Action, Crime, Drama',
		Language: 'English, Italian, French',
		Plot: "12-year-old Mathilda is reluctantly taken in by Léon, a professional assassin, after her family is murdered. An unusual relationship forms as she becomes his protégée and learns the assassin's trade.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BODllNWE0MmEtYjUwZi00ZjY3LThmNmQtZjZlMjI2YTZjYmQ0XkEyXkFqcGdeQXVyNTc1NTQxODI@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '73%'
			},
			{
				Source: 'Metacritic',
				Score: '64/100'
			}
		],
		Released: '18 Nov 1994',
		Runtime: '110 min',
		Title: 'Léon: The Professional',
		Writer: 'Luc Besson',
	},
	{
		Actors: 'Kang-ho Song, Sun-kyun Lee, Yeo-jeong Cho',
		Awards: 'Won 4 Oscars. 308 wins & 271 nominations total',
		BoxOffice: '$53,369,749',
		Country: 'South Korea',
		DVD: '11 Oct 2019',
		Director: 'Bong Joon Ho',
		Genre: 'Comedy, Drama, Thriller',
		Language: 'Korean, English',
		Plot: 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYWZjMjk3ZTItODQ2ZC00NTY5LWE0ZDYtZTI3MjcwN2Q5NTVkXkEyXkFqcGdeQXVyODk4OTc3MTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '96/100'
			}
		],
		Released: '08 Nov 2019',
		Runtime: '132 min',
		Title: 'Parasite',
		Writer: 'Bong Joon Ho, Han Jin-won',
	},
	{
		Actors: 'Matthew Broderick, Jeremy Irons, James Earl Jones',
		Awards: 'Won 2 Oscars. 39 wins & 35 nominations total',
		BoxOffice: '$422,783,777',
		Country: 'United States',
		DVD: '04 Oct 2011',
		Director: 'Roger Allers, Rob Minkoff',
		Genre: 'Animation, Adventure, Drama',
		Language: 'English, Swahili, Xhosa, Zulu',
		Plot: 'Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYTYxNGMyZTYtMjE3MS00MzNjLWFjNmYtMDk3N2FmM2JiM2M1XkEyXkFqcGdeQXVyNjY5NDU4NzI@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '88/100'
			}
		],
		Released: '24 Jun 1994',
		Runtime: '88 min',
		Title: 'The Lion King',
		Writer: 'Irene Mecchi, Jonathan Roberts, Linda Woolverton',
	},
	{
		Actors: 'Russell Crowe, Joaquin Phoenix, Connie Nielsen',
		Awards: 'Won 5 Oscars. 59 wins & 106 nominations total',
		BoxOffice: '$187,705,427',
		Country: 'United States, United Kingdom, Malta, Morocco',
		DVD: '26 Sep 2000',
		Director: 'Ridley Scott',
		Genre: 'Action, Adventure, Drama',
		Language: 'English',
		Plot: 'A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDliMmNhNDEtODUyOS00MjNlLTgxODEtN2U3NzIxMGVkZTA1L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '77%'
			},
			{
				Source: 'Metacritic',
				Score: '67/100'
			}
		],
		Released: '05 May 2000',
		Runtime: '155 min',
		Title: 'Gladiator',
		Writer: 'David Franzoni, John Logan, William Nicholson',
	},
	{
		Actors: "Edward Norton, Edward Furlong, Beverly D'Angelo",
		Awards: 'Nominated for 1 Oscar. 4 wins & 15 nominations total',
		BoxOffice: '$6,719,864',
		Country: 'United States',
		DVD: '05 Apr 2005',
		Director: 'Tony Kaye',
		Genre: 'Drama',
		Language: 'English',
		Plot: 'A former neo-nazi skinhead tries to prevent his younger brother from going down the same wrong path that he did.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZTJhN2FkYWEtMGI0My00YWM4LWI2MjAtM2UwNjY4MTI2ZTQyXkEyXkFqcGdeQXVyNjc3MjQzNTI@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '83%'
			},
			{
				Source: 'Metacritic',
				Score: '62/100'
			}
		],
		Released: '20 Nov 1998',
		Runtime: '119 min',
		Title: 'American History X',
		Writer: 'David McKenna',
	},
	{
		Actors: 'Kevin Spacey, Gabriel Byrne, Chazz Palminteri',
		Awards: 'Won 2 Oscars. 37 wins & 17 nominations total',
		BoxOffice: '$23,341,568',
		Country: 'United States, Germany',
		DVD: '02 Sep 2003',
		Director: 'Bryan Singer',
		Genre: 'Crime, Drama, Mystery',
		Language: 'English, Hungarian, Spanish, French',
		Plot: 'A sole survivor tells of the twisty events leading up to a horrific gun battle on a boat, which began when five criminals met at a seemingly random police lineup.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYTViNjMyNmUtNDFkNC00ZDRlLThmMDUtZDU2YWE4NGI2ZjVmXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '88%'
			},
			{
				Source: 'Metacritic',
				Score: '77/100'
			}
		],
		Released: '16 Aug 1995',
		Runtime: '106 min',
		Title: 'The Usual Suspects',
		Writer: 'Christopher McQuarrie',
	},
	{
		Actors: 'Leonardo DiCaprio, Matt Damon, Jack Nicholson',
		Awards: 'Won 4 Oscars. 97 wins & 141 nominations total',
		BoxOffice: '$132,399,394',
		Country: 'United States, Hong Kong',
		DVD: '13 Feb 2007',
		Director: 'Martin Scorsese',
		Genre: 'Crime, Drama, Thriller',
		Language: 'English, Cantonese',
		Plot: 'An undercover cop and a mole in the police attempt to identify each other while infiltrating an Irish gang in South Boston.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTI1MTY2OTIxNV5BMl5BanBnXkFtZTYwNjQ4NjY3._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '90%'
			},
			{
				Source: 'Metacritic',
				Score: '85/100'
			}
		],
		Released: '06 Oct 2006',
		Runtime: '151 min',
		Title: 'The Departed',
		Writer: 'William Monahan, Alan Mak, Felix Chong',
	},
	{
		Actors: 'Christian Bale, Hugh Jackman, Scarlett Johansson',
		Awards: 'Nominated for 2 Oscars. 6 wins & 45 nominations total',
		BoxOffice: '$53,089,891',
		Country: 'United States, United Kingdom',
		DVD: '13 Feb 2007',
		Director: 'Christopher Nolan',
		Genre: 'Drama, Mystery, Thriller',
		Language: 'English',
		Plot: 'After a tragic accident, two stage magicians in 1890s London engage in a battle to create the ultimate illusion while sacrificing everything they have to outwit each other.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjA4NDI0MTIxNF5BMl5BanBnXkFtZTYwNTM0MzY2._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '76%'
			},
			{
				Source: 'Metacritic',
				Score: '66/100'
			}
		],
		Released: '20 Oct 2006',
		Runtime: '130 min',
		Title: 'The Prestige',
		Writer: 'Jonathan Nolan, Christopher Nolan, Christopher Priest',
	},
	{
		Actors: 'Humphrey Bogart, Ingrid Bergman, Paul Henreid',
		Awards: 'Won 3 Oscars. 10 wins & 9 nominations total',
		BoxOffice: '$4,219,709',
		Country: 'United States',
		DVD: '17 Nov 1998',
		Director: 'Michael Curtiz',
		Genre: 'Drama, Romance, War',
		Language: 'English, French, German, Italian',
		Plot: 'A cynical expatriate American cafe owner struggles to decide whether or not to help his former lover and her fugitive husband escape the Nazis in French Morocco.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BY2IzZGY2YmEtYzljNS00NTM5LTgwMzUtMzM1NjQ4NGI0OTk0XkEyXkFqcGdeQXVyNDYyMDk5MTU@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '99%'
			},
			{
				Source: 'Metacritic',
				Score: '100/100'
			}
		],
		Released: '23 Jan 1943',
		Runtime: '102 min',
		Title: 'Casablanca',
		Writer: 'Julius J. Epstein, Philip G. Epstein, Howard Koch',
	},
	{
		Actors: 'Miles Teller, J.K. Simmons, Melissa Benoist',
		Awards: 'Won 3 Oscars. 98 wins & 145 nominations total',
		BoxOffice: '$13,092,000',
		Country: 'United States',
		DVD: '02 Dec 2014',
		Director: 'Damien Chazelle',
		Genre: 'Drama, Music',
		Language: 'English',
		Plot: "A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor who will stop at nothing to realize a student's potential.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTA5NDZlZGUtMjAxOS00YTRkLTkwYmMtYWQ0NWEwZDZiNjEzXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '88/100'
			}
		],
		Released: '15 Oct 2014',
		Runtime: '106 min',
		Title: 'Whiplash',
		Writer: 'Damien Chazelle',
	},
	{
		Actors: 'François Cluzet, Omar Sy, Anne Le Ny',
		Awards: 'Nominated for 1 BAFTA Film Award38 wins & 40 nominations total',
		BoxOffice: '$10,198,820',
		Country: 'France',
		DVD: '15 Jan 2013',
		Director: 'Olivier Nakache, Éric Toledano',
		Genre: 'Biography, Comedy, Drama',
		Language: 'French, English',
		Plot: 'After he becomes a quadriplegic from a paragliding accident, an aristocrat hires a young man from the projects to be his caregiver.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTYxNDA3MDQwNl5BMl5BanBnXkFtZTcwNTU4Mzc1Nw@@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '75%'
			},
			{
				Source: 'Metacritic',
				Score: '57/100'
			}
		],
		Released: '02 Nov 2011',
		Runtime: '112 min',
		Title: 'The Intouchables',
		Writer: 'Olivier Nakache, Philippe Pozzo di Borgo, Éric Toledano',
	},
	{
		Actors: 'Charles Chaplin, Paulette Goddard, Henry Bergman',
		Awards: '4 wins & 1 nomination',
		BoxOffice: '$163,577',
		Country: 'United States',
		DVD: '16 Nov 2010',
		Director: 'Charles Chaplin',
		Genre: 'Comedy, Drama, Romance',
		Language: 'English',
		Plot: 'The Tramp struggles to live in modern industrial society with the help of a young homeless woman.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYjJiZjMzYzktNjU0NS00OTkxLWEwYzItYzdhYWJjN2QzMTRlL2ltYWdlL2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '96/100'
			}
		],
		Released: '25 Feb 1936',
		Runtime: '87 min',
		Title: 'Modern Times',
		Writer: 'Charles Chaplin',
	},
	{
		Actors: 'Henry Fonda, Charles Bronson, Claudia Cardinale',
		Awards: '4 wins & 5 nominations',
		BoxOffice: '$5,321,508',
		Country: 'Italy, United States',
		DVD: '18 Nov 2003',
		Director: 'Sergio Leone',
		Genre: 'Western',
		Language: 'Italian, English, Spanish',
		Plot: 'A mysterious stranger with a harmonica joins forces with a notorious desperado to protect a beautiful widow from a ruthless assassin working for the railroad.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZGI5MjBmYzYtMzJhZi00NGI1LTk3MzItYjBjMzcxM2U3MDdiXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '80/100'
			}
		],
		Released: '04 Jul 1969',
		Runtime: '165 min',
		Title: 'Once Upon a Time in the West',
		Writer: 'Sergio Donati, Sergio Leone, Dario Argento',
	},
	{
		Actors: 'Tatsuya Nakadai, Akira Ishihama, Shima Iwashita',
		Awards: '9 wins & 3 nominations',
		BoxOffice: 'N/A',
		Country: 'Japan',
		DVD: 'N/A',
		Director: 'Masaki Kobayashi',
		Genre: 'Action, Drama, Mystery',
		Language: 'Japanese',
		Plot: "When a ronin requesting seppuku at a feudal lord's palace is told of the brutal suicide of another ronin who previously visited, he reveals how their pasts are intertwined - and in doing so challenges the clan's integrity.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BYjBmYTQ1NjItZWU5MS00YjI0LTg2OTYtYmFkN2JkMmNiNWVkXkEyXkFqcGdeQXVyMTMxMTY0OTQ@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.6/10'
			},
			{
				Source: 'Metacritic',
				Score: '85/100'
			}
		],
		Released: '04 Aug 1964',
		Runtime: '133 min',
		Title: 'Hara-Kiri',
		Writer: 'Yasuhiko Takiguchi, Shinobu Hashimoto',
	},
	{
		Actors: 'Tsutomu Tatsumi, Ayano Shiraishi, Akemi Yamaguchi',
		Awards: '3 wins',
		BoxOffice: '$516,962',
		Country: 'Japan',
		DVD: '11 Mar 2017',
		Director: 'Isao Takahata',
		Genre: 'Animation, Drama, War',
		Language: 'Japanese',
		Plot: 'A young boy and his little sister struggle to survive in Japan during World War II.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZmY2NjUzNDQtNTgxNC00M2Q4LTljOWQtMjNjNDBjNWUxNmJlXkEyXkFqcGdeQXVyNTA4NzY1MzY@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '100%'
			},
			{
				Source: 'Metacritic',
				Score: '94/100'
			}
		],
		Released: '26 Jul 1989',
		Runtime: '89 min',
		Title: 'Grave of the Fireflies',
		Writer: 'Akiyuki Nosaka, Isao Takahata',
	},
	{
		Actors: 'Sigourney Weaver, Tom Skerritt, John Hurt',
		Awards: 'Won 1 Oscar. 18 wins & 22 nominations total',
		BoxOffice: '$81,900,459',
		Country: 'United Kingdom, United States',
		DVD: '01 Jun 1999',
		Director: 'Ridley Scott',
		Genre: 'Horror, Sci-Fi',
		Language: 'English',
		Plot: 'The crew of a commercial spacecraft encounter a deadly lifeform after investigating an unknown transmission.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMmQ2MmU3NzktZjAxOC00ZDZhLTk4YzEtMDMyMzcxY2IwMDAyXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '89/100'
			}
		],
		Released: '22 Jun 1979',
		Runtime: '117 min',
		Title: 'Alien',
		Writer: "Dan O'Bannon, Ronald Shusett",
	},
	{
		Actors: 'James Stewart, Grace Kelly, Wendell Corey',
		Awards: 'Nominated for 4 Oscars. 6 wins & 13 nominations total',
		BoxOffice: '$36,764,313',
		Country: 'United States',
		DVD: '07 Sep 2004',
		Director: 'Alfred Hitchcock',
		Genre: 'Mystery, Thriller',
		Language: 'English',
		Plot: 'A wheelchair-bound photographer spies on his neighbors from his Greenwich Village courtyard apartment window, and becomes convinced one of them has committed murder, despite the skepticism of his fashion-model girlfriend.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNGUxYWM3M2MtMGM3Mi00ZmRiLWE0NGQtZjE5ODI2OTJhNTU0XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '100/100'
			}
		],
		Released: '01 Sep 1954',
		Runtime: '112 min',
		Title: 'Rear Window',
		Writer: 'John Michael Hayes, Cornell Woolrich',
	},
	{
		Actors: 'Charles Chaplin, Virginia Cherrill, Florence Lee',
		Awards: '3 wins & 1 nomination',
		BoxOffice: '$19,181',
		Country: 'United States',
		DVD: '23 Feb 2010',
		Director: 'Charles Chaplin',
		Genre: 'Comedy, Drama, Romance',
		Language: 'None, English',
		Plot: 'With the aid of a wealthy erratic tippler, a dewy-eyed tramp who has fallen in love with a sightless flower girl accumulates money to be able to help her medically.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BY2I4MmM1N2EtM2YzOS00OWUzLTkzYzctNDc5NDg2N2IyODJmXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '99/100'
			}
		],
		Released: '07 Mar 1931',
		Runtime: '87 min',
		Title: 'City Lights',
		Writer: 'Charles Chaplin, Harry Carr, Harry Crocker',
	},
	{
		Actors: 'Guy Pearce, Carrie-Anne Moss, Joe Pantoliano',
		Awards: 'Nominated for 2 Oscars. 57 wins & 59 nominations total',
		BoxOffice: '$25,544,867',
		Country: 'United States',
		DVD: '04 Sep 2001',
		Director: 'Christopher Nolan',
		Genre: 'Mystery, Thriller',
		Language: 'English',
		Plot: "A man with short-term memory loss attempts to track down his wife's murderer.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BZTcyNjk1MjgtOWI3Mi00YzQwLWI5MTktMzY4ZmI2NDAyNzYzXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '80/100'
			}
		],
		Released: '25 May 2001',
		Runtime: '113 min',
		Title: 'Memento',
		Writer: 'Christopher Nolan, Jonathan Nolan',
	},
	{
		Actors: 'Philippe Noiret, Enzo Cannavale, Antonella Attili',
		Awards: 'Won 1 Oscar. 25 wins & 32 nominations total',
		BoxOffice: '$12,397,210',
		Country: 'Italy, France',
		DVD: '10 Jan 2006',
		Director: 'Giuseppe Tornatore',
		Genre: 'Drama, Romance',
		Language: 'Italian',
		Plot: "A filmmaker recalls his childhood when falling in love with the pictures at the cinema of his home village and forms a deep friendship with the cinema's projectionist.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BM2FhYjEyYmYtMDI1Yy00YTdlLWI2NWQtYmEzNzAxOGY1NjY2XkEyXkFqcGdeQXVyNTA3NTIyNDg@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '90%'
			},
			{
				Source: 'Metacritic',
				Score: '80/100'
			}
		],
		Released: '23 Feb 1990',
		Runtime: '155 min',
		Title: 'Cinema Paradiso',
		Writer: 'Giuseppe Tornatore, Vanna Paoli',
	},
	{
		Actors: 'Martin Sheen, Marlon Brando, Robert Duvall',
		Awards: 'Won 2 Oscars. 21 wins & 33 nominations total',
		BoxOffice: '$83,471,511',
		Country: 'United States',
		DVD: '18 May 2010',
		Director: 'Francis Ford Coppola',
		Genre: 'Drama, Mystery, War',
		Language: 'English, French, Vietnamese',
		Plot: 'A U.S. Army officer serving in Vietnam is tasked with assassinating a renegade Special Forces Colonel who sees himself as a god.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDdhODg0MjYtYzBiOS00ZmI5LWEwZGYtZDEyNDU4MmQyNzFkXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '94/100'
			}
		],
		Released: '15 Aug 1979',
		Runtime: '147 min',
		Title: 'Apocalypse Now',
		Writer: 'John Milius, Francis Ford Coppola, Michael Herr',
	},
	{
		Actors: 'Harrison Ford, Karen Allen, Paul Freeman',
		Awards: 'Won 5 Oscars. 37 wins & 24 nominations total',
		BoxOffice: '$248,159,971',
		Country: 'United States',
		DVD: '13 May 2008',
		Director: 'Steven Spielberg',
		Genre: 'Action, Adventure',
		Language: 'English, German, Hebrew, Spanish, Arabic, Nepali',
		Plot: "In 1936, archaeologist and adventurer Indiana Jones is hired by the U.S. government to find the Ark of the Covenant before Adolf Hitler's Nazis can obtain its awesome powers.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjA0ODEzMTc1Nl5BMl5BanBnXkFtZTcwODM2MjAxNA@@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '85/100'
			}
		],
		Released: '12 Jun 1981',
		Runtime: '115 min',
		Title: 'Indiana Jones and the Raiders of the Lost Ark',
		Writer: 'Lawrence Kasdan, George Lucas, Philip Kaufman',
	},
	{
		Actors: 'Jamie Foxx, Christoph Waltz, Leonardo DiCaprio',
		Awards: 'Won 2 Oscars. 58 wins & 158 nominations total',
		BoxOffice: '$162,805,434',
		Country: 'United States',
		DVD: '16 Apr 2013',
		Director: 'Quentin Tarantino',
		Genre: 'Drama, Western',
		Language: 'English, German, French, Italian',
		Plot: 'With the help of a German bounty-hunter, a freed slave sets out to rescue his wife from a brutal plantation-owner in Mississippi.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjIyNTQ5NjQ1OV5BMl5BanBnXkFtZTcwODg1MDU4OA@@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '86%'
			},
			{
				Source: 'Metacritic',
				Score: '81/100'
			}
		],
		Released: '25 Dec 2012',
		Runtime: '165 min',
		Title: 'Django Unchained',
		Writer: 'Quentin Tarantino',
	},
	{
		Actors: 'Ben Burtt, Elissa Knight, Jeff Garlin',
		Awards: 'Won 1 Oscar. 94 wins & 95 nominations total',
		BoxOffice: '$223,808,164',
		Country: 'United States',
		DVD: '18 Nov 2008',
		Director: 'Andrew Stanton',
		Genre: 'Animation, Adventure, Family',
		Language: 'English, Hindi',
		Plot: 'In the distant future, a small waste-collecting robot inadvertently embarks on a space journey that will ultimately decide the fate of mankind.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjExMTg5OTU0NF5BMl5BanBnXkFtZTcwMjMxMzMzMw@@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '95/100'
			}
		],
		Released: '27 Jun 2008',
		Runtime: '98 min',
		Title: 'WALL·E',
		Writer: 'Andrew Stanton, Pete Docter, Jim Reardon',
	},
	{
		Actors: 'Ulrich Mühe, Martina Gedeck, Sebastian Koch',
		Awards: 'Won 1 Oscar. 80 wins & 38 nominations total',
		BoxOffice: '$11,286,112',
		Country: 'Germany, France',
		DVD: '21 Aug 2007',
		Director: 'Florian Henckel von Donnersmarck',
		Genre: 'Drama, Mystery, Thriller',
		Language: 'German',
		Plot: 'In 1984 East Berlin, an agent of the secret police, conducting surveillance on a writer and his lover, finds himself becoming increasingly absorbed by their lives.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTQyZGFjNWMtYWFiYy00OWU1LTlhMjAtYTBiNmU5NjJiNTAzXkEyXkFqcGdeQXVyMTI3ODAyMzE2._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			},
			{
				Source: 'Metacritic',
				Score: '89/100'
			}
		],
		Released: '30 Mar 2007',
		Runtime: '137 min',
		Title: 'The Lives of Others',
		Writer: 'Florian Henckel von Donnersmarck',
	},
	{
		Actors: 'William Holden, Gloria Swanson, Erich von Stroheim',
		Awards: 'Won 3 Oscars. 18 wins & 20 nominations total',
		BoxOffice: '$299,645',
		Country: 'United States',
		DVD: '11 Nov 2008',
		Director: 'Billy Wilder',
		Genre: 'Drama, Film-Noir',
		Language: 'English',
		Plot: 'A screenwriter develops a dangerous relationship with a faded film star determined to make a triumphant return.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTU0NTkyNzYwMF5BMl5BanBnXkFtZTgwMDU0NDk5MTI@._V1_SX300.jpg',
		Rated: 'Passed',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			}
		],
		Released: '04 Aug 1950',
		Runtime: '110 min',
		Title: 'Sunset Blvd.',
		Writer: 'Charles Brackett, Billy Wilder, D.M. Marshman Jr.',
	},
	{
		Actors: 'Jack Nicholson, Shelley Duvall, Danny Lloyd',
		Awards: '4 wins & 8 nominations',
		BoxOffice: '$45,634,352',
		Country: 'United Kingdom, United States',
		DVD: '23 Oct 2007',
		Director: 'Stanley Kubrick',
		Genre: 'Drama, Horror',
		Language: 'English',
		Plot: 'A family heads to an isolated hotel for the winter where a sinister presence influences the father into violence, while his psychic son sees horrific forebodings from both past and future.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZWFlYmY2MGEtZjVkYS00YzU4LTg0YjQtYzY1ZGE3NTA5NGQxXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '85%'
			},
			{
				Source: 'Metacritic',
				Score: '66/100'
			}
		],
		Released: '13 Jun 1980',
		Runtime: '146 min',
		Title: 'The Shining',
		Writer: 'Stephen King, Stanley Kubrick, Diane Johnson',
	},
	{
		Actors: 'Kirk Douglas, Ralph Meeker, Adolphe Menjou',
		Awards: 'Nominated for 1 BAFTA Film Award7 wins & 4 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '01 May 2001',
		Director: 'Stanley Kubrick',
		Genre: 'Drama, War',
		Language: 'English, German, Latin',
		Plot: 'After refusing to attack an enemy position, a general accuses the soldiers of cowardice and their commanding officer must defend them.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNjViMmRkOTEtM2ViOS00ODg0LWJhYWEtNTBlOGQxNDczOGY3XkEyXkFqcGdeQXVyMDI2NDg0NQ@@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '25 Dec 1957',
		Runtime: '88 min',
		Title: 'Paths of Glory',
		Writer: 'Stanley Kubrick, Calder Willingham, Jim Thompson',
	},
	{
		Actors: 'Charles Chaplin, Paulette Goddard, Jack Oakie',
		Awards: 'Nominated for 5 Oscars. 6 wins & 6 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '24 May 2011',
		Director: 'Charles Chaplin',
		Genre: 'Comedy, Drama, War',
		Language: 'English, Esperanto, Latin',
		Plot: "Dictator Adenoid Hynkel tries to expand his empire while a poor Jewish barber tries to avoid persecution from Hynkel's regime.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMmExYWJjNTktNGUyZS00ODhmLTkxYzAtNWIzOGEyMGNiMmUwXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			}
		],
		Released: '07 Mar 1941',
		Runtime: '125 min',
		Title: 'The Great Dictator',
		Writer: 'Charles Chaplin',
	},
	{
		Actors: 'Robert Downey Jr., Chris Hemsworth, Mark Ruffalo',
		Awards: 'Nominated for 1 Oscar. 46 wins & 79 nominations total',
		BoxOffice: '$678,815,482',
		Country: 'United States',
		DVD: '14 Aug 2018',
		Director: 'Anthony Russo, Joe Russo',
		Genre: 'Action, Adventure, Sci-Fi',
		Language: 'English',
		Plot: 'The Avengers and their allies must be willing to sacrifice all in an attempt to defeat the powerful Thanos before his blitz of devastation and ruin puts an end to the universe.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjMxNjY2MDU1OV5BMl5BanBnXkFtZTgwNzY1MTUwNTM@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '85%'
			},
			{
				Source: 'Metacritic',
				Score: '68/100'
			}
		],
		Released: '27 Apr 2018',
		Runtime: '149 min',
		Title: 'Avengers: Infinity War',
		Writer: 'Christopher Markus, Stephen McFeely, Stan Lee',
	},
	{
		Actors: 'Tyrone Power, Marlene Dietrich, Charles Laughton',
		Awards: 'Nominated for 6 Oscars. 4 wins & 16 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: 'N/A',
		Director: 'Billy Wilder',
		Genre: 'Crime, Drama, Mystery',
		Language: 'English, German',
		Plot: 'A veteran British barrister must defend his client in a murder trial that has surprise after surprise.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNDQwODU5OWYtNDcyNi00MDQ1LThiOGMtZDkwNWJiM2Y3MDg0XkEyXkFqcGdeQXVyMDI2NDg0NQ@@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			}
		],
		Released: '06 Feb 1958',
		Runtime: '116 min',
		Title: 'Witness for the Prosecution',
		Writer: 'Agatha Christie, Billy Wilder, Harry Kurnitz',
	},
	{
		Actors: 'Sigourney Weaver, Michael Biehn, Carrie Henn',
		Awards: 'Won 2 Oscars. 20 wins & 23 nominations total',
		BoxOffice: '$85,160,248',
		Country: 'United Kingdom, United States',
		DVD: '01 Jun 1999',
		Director: 'James Cameron',
		Genre: 'Action, Adventure, Sci-Fi',
		Language: 'English',
		Plot: 'Fifty-seven years after surviving an apocalyptic attack aboard her space vessel by merciless space creatures, Officer Ripley awakens from hyper-sleep and tries to warn anyone who will listen about the predators.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZGU2OGY5ZTYtMWNhYy00NjZiLWI0NjUtZmNhY2JhNDRmODU3XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '84/100'
			}
		],
		Released: '18 Jul 1986',
		Runtime: '137 min',
		Title: 'Aliens',
		Writer: 'James Cameron, David Giler, Walter Hill',
	},
	{
		Actors: 'Kevin Spacey, Annette Bening, Thora Birch',
		Awards: 'Won 5 Oscars. 111 wins & 102 nominations total',
		BoxOffice: '$130,096,601',
		Country: 'United States',
		DVD: '02 Jan 2002',
		Director: 'Sam Mendes',
		Genre: 'Drama',
		Language: 'English',
		Plot: "A sexually frustrated suburban father has a mid-life crisis after becoming infatuated with his daughter's best friend.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNTBmZWJkNjctNDhiNC00MGE2LWEwOTctZTk5OGVhMWMyNmVhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '87%'
			},
			{
				Source: 'Metacritic',
				Score: '84/100'
			}
		],
		Released: '01 Oct 1999',
		Runtime: '122 min',
		Title: 'American Beauty',
		Writer: 'Alan Ball',
	},
	{
		Actors: 'Christian Bale, Tom Hardy, Anne Hathaway',
		Awards: 'Nominated for 1 BAFTA Film Award39 wins & 103 nominations total',
		BoxOffice: '$448,149,584',
		Country: 'United States, United Kingdom',
		DVD: '04 Dec 2012',
		Director: 'Christopher Nolan',
		Genre: 'Action, Crime, Drama',
		Language: 'English, Arabic',
		Plot: "Eight years after the Joker's reign of anarchy, Batman, with the help of the enigmatic Catwoman, is forced from his exile to save Gotham City from the brutal guerrilla terrorist Bane.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTk4ODQzNDY3Ml5BMl5BanBnXkFtZTcwODA0NTM4Nw@@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '87%'
			},
			{
				Source: 'Metacritic',
				Score: '78/100'
			}
		],
		Released: '20 Jul 2012',
		Runtime: '164 min',
		Title: 'The Dark Knight Rises',
		Writer: 'Jonathan Nolan, Christopher Nolan, David S. Goyer',
	},
	{
		Actors: 'Peter Sellers, George C. Scott, Sterling Hayden',
		Awards: 'Nominated for 4 Oscars. 14 wins & 11 nominations total',
		BoxOffice: '$9,440,272',
		Country: 'United Kingdom, United States',
		DVD: '21 Oct 2003',
		Director: 'Stanley Kubrick',
		Genre: 'Comedy, War',
		Language: 'English, Russian',
		Plot: 'An insane American general orders a bombing attack on the Soviet Union, triggering a path to nuclear holocaust that a war room full of politicians and generals frantically tries to stop.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZWI3ZTMxNjctMjdlNS00NmUwLWFiM2YtZDUyY2I3N2MxYTE0XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '97/100'
			}
		],
		Released: '29 Jan 1964',
		Runtime: '95 min',
		Title: 'Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb',
		Writer: 'Stanley Kubrick, Terry Southern, Peter George',
	},
	{
		Actors: 'Shameik Moore, Jake Johnson, Hailee Steinfeld',
		Awards: 'Won 1 Oscar. 82 wins & 57 nominations total',
		BoxOffice: '$190,241,310',
		Country: 'United States',
		DVD: '19 Mar 2019',
		Director: 'Bob Persichetti, Peter Ramsey, Rodney Rothman',
		Genre: 'Animation, Action, Adventure',
		Language: 'English, Spanish',
		Plot: 'Teen Miles Morales becomes the Spider-Man of his universe, and must join with five spider-powered individuals from other dimensions to stop a threat for all realities.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjMwNDkxMTgzOF5BMl5BanBnXkFtZTgwNTkwNTQ3NjM@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '87/100'
			}
		],
		Released: '14 Dec 2018',
		Runtime: '117 min',
		Title: 'Spider-Man: Into the Spider-Verse',
		Writer: 'Phil Lord, Rodney Rothman',
	},
	{
		Actors: 'Joaquin Phoenix, Robert De Niro, Zazie Beetz',
		Awards: 'Won 2 Oscars. 122 wins & 239 nominations total',
		BoxOffice: '$335,477,657',
		Country: 'United States, Canada',
		DVD: '03 Oct 2019',
		Director: 'Todd Phillips',
		Genre: 'Crime, Drama, Thriller',
		Language: 'English',
		Plot: 'In Gotham City, mentally troubled comedian Arthur Fleck is disregarded and mistreated by society. He then embarks on a downward spiral of revolution and bloody crime. This path brings him face-to-face with his alter-ego: the Joker.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNGVjNWI4ZGUtNzE0MS00YTJmLWE0ZDctN2ZiYTk2YmI3NTYyXkEyXkFqcGdeQXVyMTkxNjUyNQ@@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '68%'
			},
			{
				Source: 'Metacritic',
				Score: '59/100'
			}
		],
		Released: '04 Oct 2019',
		Runtime: '122 min',
		Title: 'Joker',
		Writer: 'Todd Phillips, Scott Silver, Bob Kane',
	},
	{
		Actors: 'Choi Min-sik, Yoo Ji-Tae, Kang Hye-jeong',
		Awards: '40 wins & 21 nominations',
		BoxOffice: '$707,481',
		Country: 'South Korea',
		DVD: '07 Aug 2008',
		Director: 'Park Chan-wook',
		Genre: 'Action, Drama, Mystery',
		Language: 'Korean',
		Plot: 'After being kidnapped and imprisoned for fifteen years, Oh Dae-Su is released, only to find that he must find his captor in five days.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTI3NTQyMzU5M15BMl5BanBnXkFtZTcwMTM2MjgyMQ@@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '81%'
			},
			{
				Source: 'Metacritic',
				Score: '77/100'
			}
		],
		Released: '21 Nov 2003',
		Runtime: '120 min',
		Title: 'Old Boy',
		Writer: 'Garon Tsuchiya, Nobuaki Minegishi, Park Chan-wook',
	},
	{
		Actors: 'Mel Gibson, Sophie Marceau, Patrick McGoohan',
		Awards: 'Won 5 Oscars. 33 wins & 34 nominations total',
		BoxOffice: '$75,609,945',
		Country: 'United States',
		DVD: '19 Sep 2006',
		Director: 'Mel Gibson',
		Genre: 'Biography, Drama, History',
		Language: 'English, French, Latin, Gaelic, Italian',
		Plot: 'Scottish warrior William Wallace leads his countrymen in a rebellion to free his homeland from the tyranny of King Edward I of England.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMzkzMmU0YTYtOWM3My00YzBmLWI0YzctOGYyNTkwMWE5MTJkXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '78%'
			},
			{
				Source: 'Metacritic',
				Score: '68/100'
			}
		],
		Released: '24 May 1995',
		Runtime: '178 min',
		Title: 'Braveheart',
		Writer: 'Randall Wallace',
	},
	{
		Actors: 'Tom Hanks, Tim Allen, Don Rickles',
		Awards: 'Won 1 Oscar. 27 wins & 23 nominations total',
		BoxOffice: '$223,225,679',
		Country: 'United States',
		DVD: '23 Mar 2010',
		Director: 'John Lasseter',
		Genre: 'Animation, Adventure, Comedy',
		Language: 'English',
		Plot: "A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDU2ZWJlMjktMTRhMy00ZTA5LWEzNDgtYmNmZTEwZTViZWJkXkEyXkFqcGdeQXVyNDQ2OTk4MzI@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '100%'
			},
			{
				Source: 'Metacritic',
				Score: '95/100'
			}
		],
		Released: '22 Nov 1995',
		Runtime: '81 min',
		Title: 'Toy Story',
		Writer: 'John Lasseter, Pete Docter, Andrew Stanton',
	},
	{
		Actors: 'F. Murray Abraham, Tom Hulce, Elizabeth Berridge',
		Awards: 'Won 8 Oscars. 43 wins & 15 nominations total',
		BoxOffice: '$51,973,029',
		Country: 'United States, France',
		DVD: '24 Sep 2002',
		Director: 'Milos Forman',
		Genre: 'Biography, Drama, Music',
		Language: 'English, Italian, Latin, German',
		Plot: "The life, success and troubles of Wolfgang Amadeus Mozart, as told by Antonio Salieri, the contemporaneous composer who was insanely jealous of Mozart's talent and claimed to have murdered him.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNWJlNzUzNGMtYTAwMS00ZjI2LWFmNWQtODcxNWUxODA5YmU1XkEyXkFqcGdeQXVyNTIzOTk5ODM@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '88/100'
			}
		],
		Released: '19 Sep 1984',
		Runtime: '160 min',
		Title: 'Amadeus',
		Writer: 'Peter Shaffer, Zdenek Mahler',
	},
	{
		Actors: 'Anthony Gonzalez, Gael García Bernal, Benjamin Bratt',
		Awards: 'Won 2 Oscars. 109 wins & 40 nominations total',
		BoxOffice: '$210,460,015',
		Country: 'United States',
		DVD: '13 Feb 2018',
		Director: 'Lee Unkrich, Adrian Molina',
		Genre: 'Animation, Adventure, Comedy',
		Language: 'English, Spanish',
		Plot: "Aspiring musician Miguel, confronted with his family's ancestral ban on music, enters the Land of the Dead to find his great-great-grandfather, a legendary singer.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BYjQ5NjM0Y2YtNjZkNC00ZDhkLWJjMWItN2QyNzFkMDE3ZjAxXkEyXkFqcGdeQXVyODIxMzk5NjA@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '81/100'
			}
		],
		Released: '22 Nov 2017',
		Runtime: '105 min',
		Title: 'Coco',
		Writer: 'Lee Unkrich, Jason Katz, Matthew Aldrich',
	},
	{
		Actors: 'Tom Holland, Zendaya, Benedict Cumberbatch',
		Awards: 'Nominated for 1 Oscar. 15 wins & 45 nominations total',
		BoxOffice: '$800,588,139',
		Country: 'United States',
		DVD: 'N/A',
		Director: 'Jon Watts',
		Genre: 'Action, Adventure, Fantasy',
		Language: 'English',
		Plot: "With Spider-Man's identity now revealed, Peter asks Doctor Strange for help. When a spell goes wrong, dangerous foes from other worlds start to appear, forcing Peter to discover what it truly means to be Spider-Man.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BZWMyYzFjYTYtNTRjYi00OGExLWE2YzgtOGRmYjAxZTU3NzBiXkEyXkFqcGdeQXVyMzQ0MzA0NTM@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '71/100'
			}
		],
		Released: '17 Dec 2021',
		Runtime: '148 min',
		Title: 'Spider-Man: No Way Home',
		Writer: 'Chris McKenna, Erik Sommers, Stan Lee',
	},
	{
		Actors: 'Brad Pitt, Diane Kruger, Eli Roth',
		Awards: 'Won 1 Oscar. 133 wins & 172 nominations total',
		BoxOffice: '$120,540,719',
		Country: 'Germany, United States',
		DVD: '15 Dec 2009',
		Director: 'Quentin Tarantino',
		Genre: 'Adventure, Drama, War',
		Language: 'English, German, French, Italian',
		Plot: "In Nazi-occupied France during World War II, a plan to assassinate Nazi leaders by a group of Jewish U.S. soldiers coincides with a theatre owner's vengeful plans for the same.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTJiNDEzOWYtMTVjOC00ZjlmLWE0NGMtZmE1OWVmZDQ2OWJhXkEyXkFqcGdeQXVyNTIzOTk5ODM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '89%'
			},
			{
				Source: 'Metacritic',
				Score: '69/100'
			}
		],
		Released: '21 Aug 2009',
		Runtime: '153 min',
		Title: 'Inglourious Basterds',
		Writer: 'Quentin Tarantino',
	},
	{
		Actors: 'Jürgen Prochnow, Herbert Grönemeyer, Klaus Wennemann',
		Awards: 'Nominated for 6 Oscars. 13 wins & 11 nominations total',
		BoxOffice: '$11,487,676',
		Country: 'West Germany',
		DVD: '21 Oct 2003',
		Director: 'Wolfgang Petersen',
		Genre: 'Drama, War',
		Language: 'German',
		Plot: 'The claustrophobic world of a WWII German U-boat; boredom, filth and sheer terror.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOGZhZDIzNWMtNjkxMS00MDQ1LThkMTYtZWQzYWU3MWMxMGU5XkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '86/100'
			}
		],
		Released: '10 Feb 1982',
		Runtime: '149 min',
		Title: 'The Boat',
		Writer: 'Wolfgang Petersen, Lothar G. Buchheim',
	},
	{
		Actors: 'Robert Downey Jr., Chris Evans, Mark Ruffalo',
		Awards: 'Nominated for 1 Oscar. 70 wins & 132 nominations total',
		BoxOffice: '$858,373,000',
		Country: 'United States',
		DVD: '30 Jul 2019',
		Director: 'Anthony Russo, Joe Russo',
		Genre: 'Action, Adventure, Drama',
		Language: 'English, Japanese, Xhosa, German',
		Plot: "After the devastating events of Avengers: Infinity War (2018), the universe is in ruins. With the help of remaining allies, the Avengers assemble once more in order to reverse Thanos' actions and restore balance to the universe.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '78/100'
			}
		],
		Released: '26 Apr 2019',
		Runtime: '181 min',
		Title: 'Avengers: Endgame',
		Writer: 'Christopher Markus, Stephen McFeely, Stan Lee',
	},
	{
		Actors: 'Yôji Matsuda, Yuriko Ishida, Yûko Tanaka',
		Awards: '14 wins & 7 nominations',
		BoxOffice: '$4,845,631',
		Country: 'Japan',
		DVD: '20 Jul 2000',
		Director: 'Hayao Miyazaki',
		Genre: 'Animation, Action, Adventure',
		Language: 'Japanese',
		Plot: "On a journey to find the cure for a Tatarigami's curse, Ashitaka finds himself in the middle of a war between the forest gods and Tatara, a mining colony. In this quest he also meets San, the Mononoke Hime.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNGIzY2IzODQtNThmMi00ZDE4LWI5YzAtNzNlZTM1ZjYyYjUyXkEyXkFqcGdeQXVyODEzNjM5OTQ@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '76/100'
			}
		],
		Released: '19 Dec 1997',
		Runtime: '134 min',
		Title: 'Princess Mononoke',
		Writer: 'Hayao Miyazaki, Neil Gaiman',
	},
	{
		Actors: 'Robert De Niro, James Woods, Elizabeth McGovern',
		Awards: 'Won 2 BAFTA Film 12 wins & 12 nominations total',
		BoxOffice: '$5,321,508',
		Country: 'Italy, United States',
		DVD: '10 Jun 2003',
		Director: 'Sergio Leone',
		Genre: 'Crime, Drama',
		Language: 'English, Italian, French, Yiddish, Hebrew',
		Plot: 'A former Prohibition-era Jewish gangster returns to the Lower East Side of Manhattan 35 years later, where he must once again confront the ghosts and regrets of his old life.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMGFkNWI4MTMtNGQ0OC00MWVmLTk3MTktOGYxN2Y2YWVkZWE2XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '87%'
			},
			{
				Source: 'Metacritic',
				Score: '75/100'
			}
		],
		Released: '01 Jun 1984',
		Runtime: '229 min',
		Title: 'Once Upon a Time in America',
		Writer: 'Harry Grey, Leonardo Benvenuti, Piero De Bernardi',
	},
	{
		Actors: 'Robin Williams, Matt Damon, Ben Affleck',
		Awards: 'Won 2 Oscars. 24 wins & 61 nominations total',
		BoxOffice: '$138,433,435',
		Country: 'United States',
		DVD: '08 Dec 1998',
		Director: 'Gus Van Sant',
		Genre: 'Drama, Romance',
		Language: 'English',
		Plot: 'Will Hunting, a janitor at M.I.T., has a gift for mathematics, but needs help from a psychologist to find direction in his life.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTI0MzcxMTYtZDVkMy00NjY1LTgyMTYtZmUxN2M3NmQ2NWJhXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '70/100'
			}
		],
		Released: '09 Jan 1998',
		Runtime: '126 min',
		Title: 'Good Will Hunting',
		Writer: 'Matt Damon, Ben Affleck',
	},
	{
		Actors: 'Tom Hanks, Tim Allen, Joan Cusack',
		Awards: 'Won 2 Oscars. 61 wins & 96 nominations total',
		BoxOffice: '$415,004,880',
		Country: 'United States',
		DVD: '02 Nov 2010',
		Director: 'Lee Unkrich',
		Genre: 'Animation, Adventure, Comedy',
		Language: 'English, Spanish',
		Plot: "The toys are mistakenly delivered to a day-care center instead of the attic right before Andy leaves for college, and it's up to Woody to convince the other toys that they weren't abandoned and to return home.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTgxOTY4Mjc0MF5BMl5BanBnXkFtZTcwNTA4MDQyMw@@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '92/100'
			}
		],
		Released: '18 Jun 2010',
		Runtime: '103 min',
		Title: 'Toy Story 3',
		Writer: 'John Lasseter, Andrew Stanton, Lee Unkrich',
	},
	{
		Actors: 'Ellen Burstyn, Jared Leto, Jennifer Connelly',
		Awards: 'Nominated for 1 Oscar. 37 wins & 70 nominations total',
		BoxOffice: '$3,635,482',
		Country: 'United States',
		DVD: '22 May 2001',
		Director: 'Darren Aronofsky',
		Genre: 'Drama',
		Language: 'English',
		Plot: 'The drug-induced utopias of four Coney Island people are shattered when their addictions run deep.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTdiNzJlOWUtNWMwNS00NmFlLWI0YTEtZmI3YjIzZWUyY2Y3XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'Unrated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '79%'
			},
			{
				Source: 'Metacritic',
				Score: '68/100'
			}
		],
		Released: '15 Dec 2000',
		Runtime: '102 min',
		Title: 'Requiem for a Dream',
		Writer: 'Hubert Selby Jr., Darren Aronofsky',
	},
	{
		Actors: 'Aamir Khan, Madhavan, Mona Singh',
		Awards: '63 wins & 27 nominations',
		BoxOffice: '$6,532,874',
		Country: 'India',
		DVD: 'N/A',
		Director: 'Rajkumar Hirani',
		Genre: 'Comedy, Drama',
		Language: 'Hindi, English',
		Plot: 'Two friends are searching for their long lost companion. They revisit their college days and recall the memories of their friend who inspired them to think differently, even as the rest of the world called them "idiots".',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNTkyOGVjMGEtNmQzZi00NzFlLTlhOWQtODYyMDc2ZGJmYzFhXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.5/10'
			},
			{
				Source: 'Metacritic',
				Score: '67/100'
			}
		],
		Released: '25 Dec 2009',
		Runtime: '170 min',
		Title: '3 Idiots',
		Writer: 'Rajkumar Hirani, Abhijat Joshi, Vidhu Vinod Chopra',
	},
	{
		Actors: 'Ryûnosuke Kamiki, Mone Kamishiraishi, Ryô Narita',
		Awards: '16 wins & 26 nominations',
		BoxOffice: '$5,017,246',
		Country: 'Japan',
		DVD: '31 Jan 2018',
		Director: 'Makoto Shinkai',
		Genre: 'Animation, Drama, Fantasy',
		Language: 'Japanese',
		Plot: 'Two strangers find themselves linked in a bizarre way. When a connection forms, will distance be the only thing to keep them apart?',
		Poster: 'https://m.media-amazon.com/images/M/MV5BODRmZDVmNzUtZDA4ZC00NjhkLWI2M2UtN2M0ZDIzNDcxYThjL2ltYWdlXkEyXkFqcGdeQXVyNTk0MzMzODA@._V1_SX300.jpg',
		Rated: 'TV-PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '79/100'
			}
		],
		Released: '07 Apr 2017',
		Runtime: '106 min',
		Title: 'Your Name.',
		Writer: 'Makoto Shinkai, Clark Cheng',
	},
	{
		Actors: "Gene Kelly, Donald O'Connor, Debbie Reynolds",
		Awards: 'Nominated for 2 Oscars. 7 wins & 9 nominations total',
		BoxOffice: '$1,884,537',
		Country: 'United States',
		DVD: '24 Sep 2002',
		Director: 'Stanley Donen, Gene Kelly',
		Genre: 'Comedy, Musical, Romance',
		Language: 'English',
		Plot: 'A silent film star falls for a chorus girl just as he and his delusionally jealous screen partner are trying to make the difficult transition to talking pictures in 1920s Hollywood.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZDRjNGViMjQtOThlMi00MTA3LThkYzQtNzJkYjBkMGE0YzE1XkEyXkFqcGdeQXVyNDYyMDk5MTU@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '100%'
			},
			{
				Source: 'Metacritic',
				Score: '99/100'
			}
		],
		Released: '11 Apr 1952',
		Runtime: '103 min',
		Title: "Singin' in the Rain",
		Writer: 'Betty Comden, Adolph Green',
	},
	{
		Actors: 'Mark Hamill, Harrison Ford, Carrie Fisher',
		Awards: 'Won 1 Oscar. 23 wins & 20 nominations total',
		BoxOffice: '$309,306,177',
		Country: 'United States',
		DVD: '21 Sep 2004',
		Director: 'Richard Marquand',
		Genre: 'Action, Adventure, Fantasy',
		Language: 'English',
		Plot: "After a daring mission to rescue Han Solo from Jabba the Hutt, the Rebels dispatch to Endor to destroy the second Death Star. Meanwhile, Luke struggles to help Darth Vader back from the dark side without falling into the Emperor's tr",
		Poster: 'https://m.media-amazon.com/images/M/MV5BOWZlMjFiYzgtMTUzNC00Y2IzLTk1NTMtZmNhMTczNTk0ODk1XkEyXkFqcGdeQXVyNTAyODkwOQ@@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '82%'
			},
			{
				Source: 'Metacritic',
				Score: '58/100'
			}
		],
		Released: '25 May 1983',
		Runtime: '131 min',
		Title: 'Star Wars: Episode VI - Return of the Jedi',
		Writer: 'Lawrence Kasdan, George Lucas',
	},
	{
		Actors: 'Harvey Keitel, Tim Roth, Michael Madsen',
		Awards: '12 wins & 23 nominations',
		BoxOffice: '$2,832,029',
		Country: 'United States',
		DVD: '18 Mar 2003',
		Director: 'Quentin Tarantino',
		Genre: 'Crime, Drama, Thriller',
		Language: 'English',
		Plot: 'When a simple jewelry heist goes horribly wrong, the surviving criminals begin to suspect that one of them is a police informant.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZmExNmEwYWItYmQzOS00YjA5LTk2MjktZjEyZDE1Y2QxNjA1XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '91%'
			},
			{
				Source: 'Metacritic',
				Score: '79/100'
			}
		],
		Released: '02 Sep 1992',
		Runtime: '99 min',
		Title: 'Reservoir Dogs',
		Writer: 'Quentin Tarantino, Roger Avary',
	},
	{
		Actors: 'Jim Carrey, Kate Winslet, Tom Wilkinson',
		Awards: 'Won 1 Oscar. 73 wins & 111 nominations total',
		BoxOffice: '$34,400,301',
		Country: 'United States',
		DVD: '28 Sep 2004',
		Director: 'Michel Gondry',
		Genre: 'Drama, Romance, Sci-Fi',
		Language: 'English',
		Plot: 'When their relationship turns sour, a couple undergoes a medical procedure to have each other erased from their memories.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTY4NzcwODg3Nl5BMl5BanBnXkFtZTcwNTEwOTMyMw@@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			},
			{
				Source: 'Metacritic',
				Score: '89/100'
			}
		],
		Released: '19 Mar 2004',
		Runtime: '108 min',
		Title: 'Eternal Sunshine of the Spotless Mind',
		Writer: 'Charlie Kaufman, Michel Gondry, Pierre Bismuth',
	},
	{
		Actors: 'Keir Dullea, Gary Lockwood, William Sylvester',
		Awards: 'Won 1 Oscar. 16 wins & 12 nominations total',
		BoxOffice: '$60,481,243',
		Country: 'United Kingdom, United States',
		DVD: '23 Oct 2007',
		Director: 'Stanley Kubrick',
		Genre: 'Adventure, Sci-Fi',
		Language: 'English, Russian, French',
		Plot: "The Monoliths push humanity to reach for the stars; after their discovery in Africa generations ago, the mysterious objects lead mankind on an awesome journey to Jupiter, with the help of H.A.L. 9000: the world's greatest supercomput",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMmNlYzRiNDctZWNhMi00MzI4LThkZTctMTUzMmZkMmFmNThmXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'G',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			},
			{
				Source: 'Metacritic',
				Score: '84/100'
			}
		],
		Released: '24 Jun 1970',
		Runtime: '149 min',
		Title: '2001: A Space Odyssey',
		Writer: 'Stanley Kubrick, Arthur C. Clarke',
	},
	{
		Actors: 'Toshirô Mifune, Yutaka Sada, Tatsuya Nakadai',
		Awards: '3 wins & 3 nominations',
		BoxOffice: '$46,808',
		Country: 'Japan',
		DVD: '22 Jul 2008',
		Director: 'Akira Kurosawa',
		Genre: 'Crime, Drama, Mystery',
		Language: 'Japanese',
		Plot: "An executive of a Yokohama shoe company becomes a victim of extortion when his chauffeur's son is kidnapped by mistake and held for ransom.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTI4NTNhZDMtMWNkZi00MTRmLWJmZDQtMmJkMGVmZTEzODlhXkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			}
		],
		Released: '26 Nov 1963',
		Runtime: '143 min',
		Title: 'High and Low',
		Writer: 'Hideo Oguni, Ryûzô Kikushima, Eijirô Hisaita',
	},
	{
		Actors: 'Orson Welles, Joseph Cotten, Dorothy Comingore',
		Awards: 'Won 1 Oscar. 11 wins & 13 nominations total',
		BoxOffice: '$1,627,530',
		Country: 'United States',
		DVD: '23 Feb 2010',
		Director: 'Orson Welles',
		Genre: 'Drama, Mystery',
		Language: 'English, Italian',
		Plot: "Following the death of publishing tycoon Charles Foster Kane, reporters scramble to uncover the meaning of his final utterance; 'Rosebud'.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BYjBiOTYxZWItMzdiZi00NjlkLWIzZTYtYmFhZjhiMTljOTdkXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '99%'
			},
			{
				Source: 'Metacritic',
				Score: '100/100'
			}
		],
		Released: '05 Sep 1941',
		Runtime: '119 min',
		Title: 'Citizen Kane',
		Writer: 'Herman J. Mankiewicz, Orson Welles, John Houseman',
	},
	{
		Actors: "Peter O'Toole, Alec Guinness, Anthony Quinn",
		Awards: 'Won 7 Oscars. 31 wins & 15 nominations total',
		BoxOffice: '$45,306,425',
		Country: 'United Kingdom',
		DVD: '03 Apr 2001',
		Director: 'David Lean',
		Genre: 'Adventure, Biography, Drama',
		Language: 'English, Arabic, Turkish',
		Plot: 'The story of T.E. Lawrence, the English officer who successfully united and led the diverse, often warring, Arab tribes during World War I in order to fight the Turks.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYWY5ZjhjNGYtZmI2Ny00ODM0LWFkNzgtZmI1YzA2N2MxMzA0XkEyXkFqcGdeQXVyNjUwNzk3NDc@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '100/100'
			}
		],
		Released: '11 Dec 1962',
		Runtime: '218 min',
		Title: 'Lawrence of Arabia',
		Writer: 'Robert Bolt, Michael Wilson',
	},
	{
		Actors: 'Zain Al Rafeea, Yordanos Shiferaw, Boluwatife Treasure Bankole',
		Awards: 'Nominated for 1 Oscar. 35 wins & 53 nominations total',
		BoxOffice: '$1,661,096',
		Country: 'Lebanon, France, Cyprus, Qatar, United Kingdom',
		DVD: '26 Mar 2019',
		Director: 'Nadine Labaki',
		Genre: 'Drama',
		Language: 'Arabic, Amharic',
		Plot: 'While serving a five-year sentence for a violent crime, a 12-year-old boy sues his parents for neglect.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMmExNzU2ZWMtYzUwYi00YmM2LTkxZTQtNmVhNjY0NTMyMWI2XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '90%'
			},
			{
				Source: 'Metacritic',
				Score: '75/100'
			}
		],
		Released: '20 Sep 2018',
		Runtime: '126 min',
		Title: 'Capernaum',
		Writer: 'Nadine Labaki, Jihad Hojeily, Michelle Keserwany',
	},
	{
		Actors: 'Peter Lorre, Ellen Widmann, Inge Landgut',
		Awards: '2 wins',
		BoxOffice: '$35,566',
		Country: 'Germany',
		DVD: 'N/A',
		Director: 'Fritz Lang',
		Genre: 'Crime, Mystery, Thriller',
		Language: 'German',
		Plot: 'When the police in a German city are unable to catch a child-murderer, other criminals join in the manhunt.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BODA4ODk3OTEzMF5BMl5BanBnXkFtZTgwMTQ2ODMwMzE@._V1_SX300.jpg',
		Rated: 'Passed',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			}
		],
		Released: '31 Aug 1931',
		Runtime: '99 min',
		Title: 'M',
		Writer: 'Thea von Harbou, Fritz Lang, Egon Jacobsohn',
	},
	{
		Actors: 'Cary Grant, Eva Marie Saint, James Mason',
		Awards: 'Nominated for 3 Oscars. 8 wins & 10 nominations total',
		BoxOffice: '$66,728',
		Country: 'United States',
		DVD: '03 Nov 2009',
		Director: 'Alfred Hitchcock',
		Genre: 'Adventure, Mystery, Thriller',
		Language: 'English, French',
		Plot: 'A New York City advertising executive goes on the run after being mistaken for a government agent by a group of foreign spies, and falls for a woman whose loyalties he begins to doubt.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZDA3NDExMTUtMDlhOC00MmQ5LWExZGUtYmI1NGVlZWI4OWNiXkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '98/100'
			}
		],
		Released: '18 Dec 1959',
		Runtime: '136 min',
		Title: 'North by Northwest',
		Writer: 'Ernest Lehman',
	},
	{
		Actors: 'Mads Mikkelsen, Thomas Bo Larsen, Annika Wedderkopp',
		Awards: 'Nominated for 1 Oscar. 38 wins & 73 nominations total',
		BoxOffice: '$613,308',
		Country: 'Denmark, Sweden',
		DVD: '12 Jul 2014',
		Director: 'Thomas Vinterberg',
		Genre: 'Drama',
		Language: 'Danish, English, Polish',
		Plot: "A teacher lives a lonely life, all the while struggling over his son's custody. His life slowly gets better as he finds love and receives good news from his son, but his new luck is about to be brutally shattered by an innocent littl",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTg2NDg3ODg4NF5BMl5BanBnXkFtZTcwNzk3NTc3Nw@@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '77/100'
			}
		],
		Released: '10 Jan 2013',
		Runtime: '115 min',
		Title: 'The Hunt',
		Writer: 'Tobias Lindholm, Thomas Vinterberg',
	},
	{
		Actors: 'James Stewart, Kim Novak, Barbara Bel Geddes',
		Awards: 'Nominated for 2 Oscars. 8 wins & 7 nominations total',
		BoxOffice: '$7,705,225',
		Country: 'United States',
		DVD: '25 Jan 2001',
		Director: 'Alfred Hitchcock',
		Genre: 'Mystery, Romance, Thriller',
		Language: 'English',
		Plot: 'A former San Francisco police detective juggles wrestling with his personal demons and becoming obsessed with the hauntingly beautiful woman he has been hired to trail, who may be deeply disturbed.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYTE4ODEwZDUtNDFjOC00NjAxLWEzYTQtYTI1NGVmZmFlNjdiL2ltYWdlL2ltYWdlXkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '100/100'
			}
		],
		Released: '22 May 1958',
		Runtime: '128 min',
		Title: 'Vertigo',
		Writer: 'Alec Coppel, Samuel A. Taylor, Pierre Boileau',
	},
	{
		Actors: 'Audrey Tautou, Mathieu Kassovitz, Rufus',
		Awards: 'Nominated for 5 Oscars. 59 wins & 74 nominations total',
		BoxOffice: '$33,225,499',
		Country: 'France, Germany',
		DVD: '16 Jul 2002',
		Director: 'Jean-Pierre Jeunet',
		Genre: 'Comedy, Romance',
		Language: 'French, Russian, English',
		Plot: 'Amélie is an innocent and naive girl in Paris with her own sense of justice. She decides to help those around her and, along the way, discovers love.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNDg4NjM1YjMtYmNhZC00MjM0LWFiZmYtNGY1YjA3MzZmODc5XkEyXkFqcGdeQXVyNDk3NzU2MTQ@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '89%'
			},
			{
				Source: 'Metacritic',
				Score: '69/100'
			}
		],
		Released: '08 Feb 2002',
		Runtime: '122 min',
		Title: 'Amélie',
		Writer: 'Guillaume Laurant, Jean-Pierre Jeunet',
	},
	{
		Actors: 'Malcolm McDowell, Patrick Magee, Michael Bates',
		Awards: 'Nominated for 4 Oscars. 12 wins & 24 nominations total',
		BoxOffice: '$26,617,553',
		Country: 'United Kingdom, United States',
		DVD: '23 Oct 2007',
		Director: 'Stanley Kubrick',
		Genre: 'Crime, Sci-Fi',
		Language: 'English',
		Plot: "In the future, a sadistic gang leader is imprisoned and volunteers for a conduct-aversion experiment, but it doesn't go as planned.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTY3MjM1Mzc4N15BMl5BanBnXkFtZTgwODM0NzAxMDE@._V1_SX300.jpg',
		Rated: 'X',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '87%'
			},
			{
				Source: 'Metacritic',
				Score: '77/100'
			}
		],
		Released: '02 Feb 1972',
		Runtime: '136 min',
		Title: 'A Clockwork Orange',
		Writer: 'Stanley Kubrick, Anthony Burgess',
	},
	{
		Actors: "Matthew Modine, R. Lee Ermey, Vincent D'Onofrio",
		Awards: 'Nominated for 1 Oscar. 8 wins & 15 nominations total',
		BoxOffice: '$46,357,676',
		Country: 'United Kingdom, United States',
		DVD: '12 Jun 2001',
		Director: 'Stanley Kubrick',
		Genre: 'Drama, War',
		Language: 'English, Vietnamese',
		Plot: 'A pragmatic U.S. Marine observes the dehumanizing effects the Vietnam War has on his fellow recruits from their brutal boot camp training to the bloody street fighting in Hue.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNzkxODk0NjEtYjc4Mi00ZDI0LTgyYjEtYzc1NDkxY2YzYTgyXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '91%'
			},
			{
				Source: 'Metacritic',
				Score: '76/100'
			}
		],
		Released: '10 Jul 1987',
		Runtime: '116 min',
		Title: 'Full Metal Jacket',
		Writer: 'Stanley Kubrick, Michael Herr, Gustav Hasford',
	},
	{
		Actors: 'Al Pacino, Michelle Pfeiffer, Steven Bauer',
		Awards: '8 nominations',
		BoxOffice: '$45,408,703',
		Country: 'United States',
		DVD: '30 Sep 2003',
		Director: 'Brian De Palma',
		Genre: 'Crime, Drama',
		Language: 'English, Spanish',
		Plot: 'In 1980 Miami, a determined Cuban immigrant takes over a drug cartel and succumbs to greed.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNjdjNGQ4NDEtNTEwYS00MTgxLTliYzQtYzE2ZDRiZjFhZmNlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '81%'
			},
			{
				Source: 'Metacritic',
				Score: '65/100'
			}
		],
		Released: '09 Dec 1983',
		Runtime: '170 min',
		Title: 'Scarface',
		Writer: 'Oliver Stone, Howard Hawks, Ben Hecht',
	},
	{
		Actors: 'Aleksey Kravchenko, Olga Mironova, Liubomiras Laucevicius',
		Awards: '3 wins',
		BoxOffice: '$71,909',
		Country: 'Soviet Union',
		DVD: '22 Mar 2007',
		Director: 'Elem Klimov',
		Genre: 'Drama, Thriller, War',
		Language: 'Russian, Belarusian, German',
		Plot: 'After finding an old rifle, a young boy joins the Soviet resistance movement against ruthless German forces and experiences the horrors of World War II.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BODM4Njg0NTAtYjI5Ny00ZjAxLTkwNmItZTMxMWU5M2U3M2RjXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			}
		],
		Released: '03 Sep 1985',
		Runtime: '142 min',
		Title: 'Come and See',
		Writer: 'Ales Adamovich, Elem Klimov',
	},
	{
		Actors: 'Fred MacMurray, Barbara Stanwyck, Edward G. Robinson',
		Awards: 'Nominated for 7 Oscars. 2 wins & 9 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '29 Aug 2006',
		Director: 'Billy Wilder',
		Genre: 'Crime, Drama, Film-Noir',
		Language: 'English',
		Plot: 'A Los Angeles insurance representative lets an alluring housewife seduce him into a scheme of insurance fraud and murder that arouses the suspicion of his colleague, an insurance investigator.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTdlNjgyZGUtOTczYi00MDdhLTljZmMtYTEwZmRiOWFkYjRhXkEyXkFqcGdeQXVyNDY2MTk1ODk@._V1_SX300.jpg',
		Rated: 'Passed',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '95/100'
			}
		],
		Released: '06 Jul 1944',
		Runtime: '107 min',
		Title: 'Double Indemnity',
		Writer: 'Billy Wilder, Raymond Chandler, James M. Cain',
	},
	{
		Actors: 'Jack Lemmon, Shirley MacLaine, Fred MacMurray',
		Awards: 'Won 5 Oscars. 24 wins & 8 nominations total',
		BoxOffice: '$18,600,000',
		Country: 'United States',
		DVD: '04 Mar 2008',
		Director: 'Billy Wilder',
		Genre: 'Comedy, Drama, Romance',
		Language: 'English',
		Plot: 'A Manhattan insurance clerk tries to rise in his company by letting its executives use his apartment for trysts, but complications and a romance of his own ensue.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNzkwODFjNzItMmMwNi00MTU5LWE2MzktM2M4ZDczZGM1MmViXkEyXkFqcGdeQXVyNDY2MTk1ODk@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '94/100'
			}
		],
		Released: '29 Jun 1960',
		Runtime: '125 min',
		Title: 'The Apartment',
		Writer: 'Billy Wilder, I.A.L. Diamond',
	},
	{
		Actors: 'Robert De Niro, Jodie Foster, Cybill Shepherd',
		Awards: 'Nominated for 4 Oscars. 22 wins & 20 nominations total',
		BoxOffice: '$28,262,574',
		Country: 'United States',
		DVD: '14 Aug 2007',
		Director: 'Martin Scorsese',
		Genre: 'Crime, Drama',
		Language: 'English, Spanish',
		Plot: 'A mentally unstable veteran works as a nighttime taxi driver in New York City, where the perceived decadence and sleaze fuels his urge for violent action.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BM2M1MmVhNDgtNmI0YS00ZDNmLTkyNjctNTJiYTQ2N2NmYzc2XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '94/100'
			}
		],
		Released: '09 Feb 1976',
		Runtime: '114 min',
		Title: 'Taxi Driver',
		Writer: 'Paul Schrader',
	},
	{
		Actors: 'Gregory Peck, John Megna, Frank Overton',
		Awards: 'Won 3 Oscars. 14 wins & 16 nominations total',
		BoxOffice: '$592,237',
		Country: 'United States',
		DVD: '28 Apr 1998',
		Director: 'Robert Mulligan',
		Genre: 'Crime, Drama',
		Language: 'English',
		Plot: 'Atticus Finch, a widowed lawyer in Depression-era Alabama, defends a black man against an undeserved rape charge, and his children against prejudice.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNmVmYzcwNzMtMWM1NS00MWIyLThlMDEtYzUwZDgzODE1NmE2XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '93%'
			},
			{
				Source: 'Metacritic',
				Score: '88/100'
			}
		],
		Released: '16 Mar 1963',
		Runtime: '129 min',
		Title: 'To Kill a Mockingbird',
		Writer: 'Harper Lee, Horton Foote',
	},
	{
		Actors: 'Paul Newman, Robert Redford, Robert Shaw',
		Awards: 'Won 7 Oscars. 18 wins & 6 nominations total',
		BoxOffice: '$156,000,000',
		Country: 'United States',
		DVD: '31 Mar 1998',
		Director: 'George Roy Hill',
		Genre: 'Comedy, Crime, Drama',
		Language: 'English',
		Plot: 'Two grifters team up to pull off the ultimate con.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNGU3NjQ4YTMtZGJjOS00YTQ3LThmNmItMTI5MDE2ODI3NzY3XkEyXkFqcGdeQXVyMjUzOTY1NTc@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '83/100'
			}
		],
		Released: '25 Dec 1973',
		Runtime: '129 min',
		Title: 'The Sting',
		Writer: 'David S. Ward',
	},
	{
		Actors: 'Edward Asner, Jordan Nagai, John Ratzenberger',
		Awards: 'Won 2 Oscars. 79 wins & 87 nominations total',
		BoxOffice: '$293,004,164',
		Country: 'United States',
		DVD: '10 Nov 2009',
		Director: 'Pete Docter, Bob Peterson',
		Genre: 'Animation, Adventure, Comedy',
		Language: 'English',
		Plot: '78-year-old Carl Fredricksen travels to Paradise Falls in his house equipped with balloons, inadvertently taking a young stowaway.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTk3NDE2NzI4NF5BMl5BanBnXkFtZTgwNzE1MzEyMTE@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '88/100'
			}
		],
		Released: '29 May 2009',
		Runtime: '96 min',
		Title: 'Up',
		Writer: 'Pete Docter, Bob Peterson, Tom McCarthy',
	},
	{
		Actors: 'Kevin Spacey, Russell Crowe, Guy Pearce',
		Awards: 'Won 2 Oscars. 92 wins & 86 nominations total',
		BoxOffice: '$64,616,940',
		Country: 'United States',
		DVD: '23 Sep 2008',
		Director: 'Curtis Hanson',
		Genre: 'Crime, Drama, Mystery',
		Language: 'English',
		Plot: 'As corruption grows in 1950s Los Angeles, three policemen - one strait-laced, one brutal, and one sleazy - investigate a series of murders with their own brand of justice.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDQ2YzEyZGItYWRhOS00MjBmLTkzMDUtMTdjYzkyMmQxZTJlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '99%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '19 Sep 1997',
		Runtime: '138 min',
		Title: 'L.A. Confidential',
		Writer: 'James Ellroy, Brian Helgeland, Curtis Hanson',
	},
	{
		Actors: 'Lin-Manuel Miranda, Phillipa Soo, Leslie Odom Jr.',
		Awards: 'Won 1 Primetime Emmy. 18 wins & 46 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '03 Jul 2020',
		Director: 'Thomas Kail',
		Genre: 'Biography, Drama, History',
		Language: 'English',
		Plot: "The real life of one of America's foremost founding fathers and first Secretary of the Treasury, Alexander Hamilton. Captured live on Broadway from the Richard Rodgers Theater with the original Broadway cast.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNjViNWRjYWEtZTI0NC00N2E3LTk0NGQtMjY4NTM3OGNkZjY0XkEyXkFqcGdeQXVyMjUxMTY3ODM@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '03 Jul 2020',
		Runtime: '160 min',
		Title: 'Hamilton',
		Writer: 'Lin-Manuel Miranda, Ron Chernow',
	},
	{
		Actors: 'Al Pacino, Robert De Niro, Val Kilmer',
		Awards: '14 nominations',
		BoxOffice: '$67,436,818',
		Country: 'United States',
		DVD: '27 Jul 1999',
		Director: 'Michael Mann',
		Genre: 'Action, Crime, Drama',
		Language: 'English, Spanish',
		Plot: 'A group of high-end professional thieves start to feel the heat from the LAPD when they unknowingly leave a clue at their latest heist.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNGMwNzUwNjYtZWM5NS00YzMyLWI4NjAtNjM0ZDBiMzE1YWExXkEyXkFqcGdeQXVyNDk3NzU2MTQ@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '87%'
			},
			{
				Source: 'Metacritic',
				Score: '76/100'
			}
		],
		Released: '15 Dec 1995',
		Runtime: '170 min',
		Title: 'Heat',
		Writer: 'Michael Mann',
	},
	{
		Actors: "Takashi Shimura, Nobuo Kaneko, Shin'ichi Himori",
		Awards: 'Nominated for 1 BAFTA Film Award5 wins & 2 nominations total',
		BoxOffice: '$60,239',
		Country: 'Japan',
		DVD: '06 Jan 2004',
		Director: 'Akira Kurosawa',
		Genre: 'Drama',
		Language: 'Japanese',
		Plot: 'A bureaucrat tries to find meaning in his life after he discovers he has terminal cancer.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZTdkN2E5OTYtN2FiMi00YWUwLWEzMGMtZTMzNjY0NjgzYzFiXkEyXkFqcGdeQXVyMTI3ODAyMzE2._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '91/100'
			}
		],
		Released: '25 Mar 1956',
		Runtime: '143 min',
		Title: 'Ikiru',
		Writer: 'Akira Kurosawa, Shinobu Hashimoto, Hideo Oguni',
	},
	{
		Actors: 'Jason Statham, Brad Pitt, Stephen Graham',
		Awards: '4 wins & 7 nominations',
		BoxOffice: '$30,328,156',
		Country: 'United Kingdom, United States',
		DVD: '06 May 2003',
		Director: 'Guy Ritchie',
		Genre: 'Comedy, Crime',
		Language: 'English, Russian',
		Plot: 'Unscrupulous boxing promoters, violent bookmakers, a Russian gangster, incompetent amateur robbers and supposedly Jewish jewelers fight to track down a priceless stolen diamond.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTA2NDYxOGYtYjU1Mi00Y2QzLTgxMTQtMWI1MGI0ZGQ5MmU4XkEyXkFqcGdeQXVyNDk3NzU2MTQ@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '74%'
			},
			{
				Source: 'Metacritic',
				Score: '55/100'
			}
		],
		Released: '19 Jan 2001',
		Runtime: '102 min',
		Title: 'Snatch',
		Writer: 'Guy Ritchie',
	},
	{
		Actors: 'Bruce Willis, Alan Rickman, Bonnie Bedelia',
		Awards: 'Nominated for 4 Oscars. 8 wins & 6 nominations total',
		BoxOffice: '$83,844,093',
		Country: 'United States',
		DVD: '28 Dec 1999',
		Director: 'John McTiernan',
		Genre: 'Action, Thriller',
		Language: 'English, German, Italian, Japanese',
		Plot: 'An NYPD officer tries to save his wife and several others taken hostage by German terrorists during a Christmas party at the Nakatomi Plaza in Los Angeles.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZjRlNDUxZjAtOGQ4OC00OTNlLTgxNmQtYTBmMDgwZmNmNjkxXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '72/100'
			}
		],
		Released: '20 Jul 1988',
		Runtime: '132 min',
		Title: 'Die Hard',
		Writer: 'Roderick Thorp, Jeb Stuart, Steven E. de Souza',
	},
	{
		Actors: 'Harrison Ford, Sean Connery, Alison Doody',
		Awards: 'Won 1 Oscar. 8 wins & 22 nominations total',
		BoxOffice: '$197,171,806',
		Country: 'United States',
		DVD: '13 May 2008',
		Director: 'Steven Spielberg',
		Genre: 'Action, Adventure',
		Language: 'English, German, Greek, Arabic',
		Plot: "In 1938, after his father Professor Henry Jones, Sr. goes missing while pursuing the Holy Grail, Professor Henry \"Indiana\" Jones, Jr. finds himself up against Adolf Hitler's Nazis again to stop them from obtaining its powers.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjNkMzc2N2QtNjVlNS00ZTk5LTg0MTgtODY2MDAwNTMwZjBjXkEyXkFqcGdeQXVyNDk3NzU2MTQ@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '88%'
			},
			{
				Source: 'Metacritic',
				Score: '65/100'
			}
		],
		Released: '24 May 1989',
		Runtime: '127 min',
		Title: 'Indiana Jones and the Last Crusade',
		Writer: 'Jeffrey Boam, George Lucas, Menno Meyjes',
	},
	{
		Actors: 'Payman Maadi, Leila Hatami, Sareh Bayat',
		Awards: 'Won 1 Oscar. 89 wins & 50 nominations total',
		BoxOffice: '$7,099,055',
		Country: 'Iran, France, Australia',
		DVD: '21 Aug 2012',
		Director: 'Asghar Farhadi',
		Genre: 'Drama',
		Language: 'Persian',
		Plot: "A married couple are faced with a difficult decision - to improve the life of their child by moving to another country or to stay in Iran and look after a deteriorating parent who has Alzheimer's disease.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BN2JmMjViMjMtZTM5Mi00ZGZkLTk5YzctZDg5MjFjZDE4NjNkXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '99%'
			},
			{
				Source: 'Metacritic',
				Score: '95/100'
			}
		],
		Released: '16 Mar 2011',
		Runtime: '123 min',
		Title: 'A Separation',
		Writer: 'Asghar Farhadi',
	},
	{
		Actors: 'Brigitte Helm, Alfred Abel, Gustav Fröhlich',
		Awards: '6 wins & 7 nominations',
		BoxOffice: '$1,236,166',
		Country: 'Germany',
		DVD: '22 Mar 2007',
		Director: 'Fritz Lang',
		Genre: 'Drama, Sci-Fi',
		Language: 'German, English',
		Plot: "In a futuristic city sharply divided between the working class and the city planners, the son of the city's mastermind falls in love with a working-class prophet who predicts the coming of a savior to mediate their differences.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTg5YWIyMWUtZDY5My00Zjc1LTljOTctYmI0MWRmY2M2NmRkXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '98/100'
			}
		],
		Released: '13 Mar 1927',
		Runtime: '153 min',
		Title: 'Metropolis',
		Writer: 'Thea von Harbou, Fritz Lang',
	},
	{
		Actors: 'Lamberto Maggiorani, Enzo Staiola, Lianella Carell',
		Awards: 'Won 1 Oscar. 20 wins & 3 nominations total',
		BoxOffice: '$371,111',
		Country: 'Italy',
		DVD: '12 Aug 2003',
		Director: 'Vittorio De Sica',
		Genre: 'Drama',
		Language: 'Italian, English, German',
		Plot: "In post-war Italy, a working-class man's bicycle is stolen, endangering his efforts to find work. He and his son set out to find it.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BNmI1ODdjODctMDlmMC00ZWViLWI5MzYtYzRhNDdjYmM3MzFjXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '99%'
			}
		],
		Released: '13 Dec 1949',
		Runtime: '89 min',
		Title: 'Bicycle Thieves',
		Writer: 'Cesare Zavattini, Luigi Bartolini, Oreste Biancoli',
	},
	{
		Actors: 'Lubna Azabal, Mélissa Désormeaux-Poulin, Maxim Gaudette',
		Awards: 'Nominated for 1 Oscar. 40 wins & 18 nominations total',
		BoxOffice: '$2,071,334',
		Country: 'Canada, France',
		DVD: '15 Mar 2011',
		Director: 'Denis Villeneuve',
		Genre: 'Drama, Mystery, War',
		Language: 'French, Arabic, English',
		Plot: "Twins journey to the Middle East to discover their family history and fulfill their mother's last wishes.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMWE3MGYzZjktY2Q5Mi00Y2NiLWIyYWUtMmIyNzA3YmZlMGFhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			},
			{
				Source: 'Metacritic',
				Score: '80/100'
			}
		],
		Released: '12 Jan 2011',
		Runtime: '131 min',
		Title: 'Incendies',
		Writer: 'Denis Villeneuve, Wajdi Mouawad, Valérie Beaugrand-Champagne',
	},
	{
		Actors: 'Dean-Charles Chapman, George MacKay, Daniel Mays',
		Awards: 'Won 3 Oscars. 134 wins & 206 nominations total',
		BoxOffice: '$159,227,644',
		Country: 'United Kingdom, United States, India, Spain',
		DVD: '25 Dec 2019',
		Director: 'Sam Mendes',
		Genre: 'Action, Drama, War',
		Language: 'English, French, German',
		Plot: 'April 6th, 1917. As an infantry battalion assembles to wage war deep in enemy territory, two soldiers are assigned to race against time and deliver a message that will stop 1,600 men from walking straight into a deadly trap.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTdmNTFjNDEtNzg0My00ZjkxLTg1ZDAtZTdkMDc2ZmFiNWQ1XkEyXkFqcGdeQXVyNTAzNzgwNTg@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '88%'
			},
			{
				Source: 'Metacritic',
				Score: '78/100'
			}
		],
		Released: '10 Jan 2020',
		Runtime: '119 min',
		Title: '1917',
		Writer: 'Sam Mendes, Krysty Wilson-Cairns',
	},
	{
		Actors: 'Darsheel Safary, Aamir Khan, Tisca Chopra',
		Awards: '23 wins & 14 nominations',
		BoxOffice: '$1,223,869',
		Country: 'India',
		DVD: '12 Jan 2010',
		Director: 'Aamir Khan, Amole Gupte',
		Genre: 'Drama, Family',
		Language: 'Hindi',
		Plot: 'An eight-year-old boy is thought to be a lazy trouble-maker, until the new art teacher has the patience and compassion to discover the real problem behind his struggles in school.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDhjZWViN2MtNzgxOS00NmI4LThiZDQtZDI3MzM4MDE4NTc0XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			}
		],
		Released: '21 Dec 2007',
		Runtime: '165 min',
		Title: 'Like Stars on Earth',
		Writer: 'Amole Gupte',
	},
	{
		Actors: 'Christian Bale, Michael Caine, Ken Watanabe',
		Awards: 'Nominated for 1 Oscar. 13 wins & 79 nominations total',
		BoxOffice: '$206,863,479',
		Country: 'United States, United Kingdom',
		DVD: '18 Oct 2005',
		Director: 'Christopher Nolan',
		Genre: 'Action, Crime, Drama',
		Language: 'English, Mandarin',
		Plot: 'After training with his mentor, Batman begins his fight to free crime-ridden Gotham City from corruption.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BOTY4YjI2N2MtYmFlMC00ZjcyLTg3YjEtMDQyM2ZjYzQ5YWFkXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '84%'
			},
			{
				Source: 'Metacritic',
				Score: '70/100'
			}
		],
		Released: '15 Jun 2005',
		Runtime: '140 min',
		Title: 'Batman Begins',
		Writer: 'Bob Kane, David S. Goyer, Christopher Nolan',
	},
	{
		Actors: 'Clint Eastwood, Lee Van Cleef, Gian Maria Volontè',
		Awards: '2 nominations',
		BoxOffice: '$15,000,000',
		Country: 'Italy, Spain, West Germany',
		DVD: '01 Aug 2006',
		Director: 'Sergio Leone',
		Genre: 'Western',
		Language: 'Italian, English',
		Plot: 'Two bounty hunters with the same intentions team up to track down an escaped Mexican outlaw.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNWM1NmYyM2ItMTFhNy00NDU0LThlYWUtYjQyYTJmOTY0ZmM0XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '91%'
			},
			{
				Source: 'Metacritic',
				Score: '74/100'
			}
		],
		Released: '10 May 1967',
		Runtime: '132 min',
		Title: 'For a Few Dollars More',
		Writer: 'Sergio Leone, Fulvio Morsella, Luciano Vincenzoni',
	},
	{
		Actors: 'Aamir Khan, Sakshi Tanwar, Fatima Sana Shaikh',
		Awards: '29 wins & 16 nominations',
		BoxOffice: '$12,391,761',
		Country: 'India, United States',
		DVD: '22 Jun 2017',
		Director: 'Nitesh Tiwari',
		Genre: 'Action, Biography, Drama',
		Language: 'Hindi, English',
		Plot: 'Former wrestler Mahavir Singh Phogat and his two wrestler daughters struggle towards glory at the Commonwealth Games in the face of societal oppression.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTQ4MzQzMzM2Nl5BMl5BanBnXkFtZTgwMTQ1NzU3MDI@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '88%'
			}
		],
		Released: '21 Dec 2016',
		Runtime: '161 min',
		Title: 'Dangal',
		Writer: 'Piyush Gupta, Shreyas Jain, Nikhil Mehrotra',
	},
	{
		Actors: 'Bruno Ganz, Alexandra Maria Lara, Ulrich Matthes',
		Awards: 'Nominated for 1 Oscar. 22 wins & 34 nominations total',
		BoxOffice: '$5,509,040',
		Country: 'Germany, Austria, Italy',
		DVD: '02 Aug 2005',
		Director: 'Oliver Hirschbiegel',
		Genre: 'Biography, Drama, History',
		Language: 'German, Russian, French, English',
		Plot: "Traudl Junge, the final secretary for Adolf Hitler, tells of the Nazi dictator's final days in his Berlin bunker at the end of WWII.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTU0NTU5NTAyMl5BMl5BanBnXkFtZTYwNzYwMDg2._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '90%'
			},
			{
				Source: 'Metacritic',
				Score: '82/100'
			}
		],
		Released: '08 Apr 2005',
		Runtime: '156 min',
		Title: 'Downfall',
		Writer: 'Bernd Eichinger, Joachim Fest, Traudl Junge',
	},
	{
		Actors: 'Charles Chaplin, Edna Purviance, Jackie Coogan',
		Awards: '2 wins',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '01 May 2005',
		Director: 'Charles Chaplin',
		Genre: 'Comedy, Drama, Family',
		Language: 'English',
		Plot: 'The Tramp cares for an abandoned child, but events put that relationship in jeopardy.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZjhhMThhNDItNTY2MC00MmU1LTliNDEtNDdhZjdlNTY5ZDQ1XkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',
		Rated: 'Passed',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '100%'
			}
		],
		Released: '06 Feb 1921',
		Runtime: '68 min',
		Title: 'The Kid',
		Writer: 'Charles Chaplin',
	},
	{
		Actors: 'Marilyn Monroe, Tony Curtis, Jack Lemmon',
		Awards: 'Won 1 Oscar. 15 wins & 15 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '18 Jul 2006',
		Director: 'Billy Wilder',
		Genre: 'Comedy, Music, Romance',
		Language: 'English',
		Plot: 'After two male musicians witness a mob hit, they flee the state in an all-female band disguised as women, but further complications set in.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNzAyOGIxYjAtMGY2NC00ZTgyLWIwMWEtYzY0OWQ4NDFjOTc5XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'Passed',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '94%'
			},
			{
				Source: 'Metacritic',
				Score: '98/100'
			}
		],
		Released: '19 Mar 1959',
		Runtime: '121 min',
		Title: 'Some Like It Hot',
		Writer: 'Billy Wilder, I.A.L. Diamond, Robert Thoeren',
	},
	{
		Actors: 'Robert Pattinson, Zoë Kravitz, Jeffrey Wright',
		Awards: '3 nominations',
		BoxOffice: '$239,032,047',
		Country: 'United States',
		DVD: '19 Apr 2022',
		Director: 'Matt Reeves',
		Genre: 'Action, Crime, Drama',
		Language: 'English',
		Plot: "When the Riddler, a sadistic serial killer, begins murdering key political figures in Gotham, Batman is forced to investigate the city's hidden corruption and question his family's involvement.",
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDdmMTBiNTYtMDIzNi00NGVlLWIzMDYtZTk3MTQ3NGQxZGEwXkEyXkFqcGdeQXVyMzMwOTU5MDk@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.4/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '85%'
			},
			{
				Source: 'Metacritic',
				Score: '72/100'
			}
		],
		Released: '04 Mar 2022',
		Runtime: '176 min',
		Title: 'The Batman',
		Writer: 'Matt Reeves, Peter Craig, Bill Finger',
	},
	{
		Actors: 'Anthony Hopkins, Olivia Colman, Mark Gatiss',
		Awards: 'Won 2 Oscars. 34 wins & 157 nominations total',
		BoxOffice: '$2,122,771',
		Country: 'United Kingdom, France, United States',
		DVD: '25 Mar 2021',
		Director: 'Florian Zeller',
		Genre: 'Drama, Mystery',
		Language: 'English',
		Plot: 'A man refuses all assistance from his daughter as he ages. As he tries to make sense of his changing circumstances, he begins to doubt his loved ones, his own mind and even the fabric of his reality.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZGJhNWRiOWQtMjI4OS00ZjcxLTgwMTAtMzQ2ODkxY2JkOTVlXkEyXkFqcGdeQXVyMTkxNjUyNQ@@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '98%'
			},
			{
				Source: 'Metacritic',
				Score: '88/100'
			}
		],
		Released: '26 Feb 2021',
		Runtime: '97 min',
		Title: 'The Father',
		Writer: 'Christopher Hampton, Florian Zeller',
	},
	{
		Actors: 'Bette Davis, Anne Baxter, George Sanders',
		Awards: 'Won 6 Oscars. 26 wins & 20 nominations total',
		BoxOffice: '$63,463',
		Country: 'United States',
		DVD: '05 Feb 2004',
		Director: 'Joseph L. Mankiewicz',
		Genre: 'Drama',
		Language: 'English, French',
		Plot: 'A seemingly timid but secretly ruthless ingénue insinuates herself into the lives of an aging Broadway star and her circle of theater friends.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTY2MTAzODI5NV5BMl5BanBnXkFtZTgwMjM4NzQ0MjE@._V1_SX300.jpg',
		Rated: 'Passed',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '99%'
			},
			{
				Source: 'Metacritic',
				Score: '98/100'
			}
		],
		Released: '27 Oct 1950',
		Runtime: '138 min',
		Title: 'All About Eve',
		Writer: 'Joseph L. Mankiewicz, Mary Orr',
	},
	{
		Actors: 'Leonardo DiCaprio, Jonah Hill, Margot Robbie',
		Awards: 'Nominated for 5 Oscars. 37 wins & 179 nominations total',
		BoxOffice: '$116,900,694',
		Country: 'United States',
		DVD: '25 Mar 2014',
		Director: 'Martin Scorsese',
		Genre: 'Biography, Comedy, Crime',
		Language: 'English, French',
		Plot: 'Based on the true story of Jordan Belfort, from his rise to a wealthy stock-broker living the high life to his fall involving crime, corruption and the federal government.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjIxMjgxNTk0MF5BMl5BanBnXkFtZTgwNjIyOTg2MDE@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '79%'
			},
			{
				Source: 'Metacritic',
				Score: '75/100'
			}
		],
		Released: '25 Dec 2013',
		Runtime: '180 min',
		Title: 'The Wolf of Wall Street',
		Writer: 'Terence Winter, Jordan Belfort',
	},
	{
		Actors: 'Viggo Mortensen, Mahershala Ali, Linda Cardellini',
		Awards: 'Won 3 Oscars. 59 wins & 124 nominations total',
		BoxOffice: '$85,080,171',
		Country: 'United States, China',
		DVD: '12 Mar 2019',
		Director: 'Peter Farrelly',
		Genre: 'Biography, Comedy, Drama',
		Language: 'English, Italian, Russian, German',
		Plot: 'A working-class Italian-American bouncer becomes the driver of an African-American classical pianist on a tour of venues through the 1960s American South.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYzIzYmJlYTYtNGNiYy00N2EwLTk4ZjItMGYyZTJiOTVkM2RlXkEyXkFqcGdeQXVyODY1NDk1NjE@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '77%'
			},
			{
				Source: 'Metacritic',
				Score: '69/100'
			}
		],
		Released: '16 Nov 2018',
		Runtime: '130 min',
		Title: 'Green Book',
		Writer: 'Nick Vallelonga, Brian Hayes Currie, Peter Farrelly',
	},
	{
		Actors: 'Clint Eastwood, Gene Hackman, Morgan Freeman',
		Awards: 'Won 4 Oscars. 50 wins & 47 nominations total',
		BoxOffice: '$101,167,799',
		Country: 'United States',
		DVD: '30 Oct 2001',
		Director: 'Clint Eastwood',
		Genre: 'Drama, Western',
		Language: 'English',
		Plot: 'Retired Old West gunslinger William Munny reluctantly takes on one last job, with the help of his old partner Ned Logan and a young man, The "Schofield Kid."',
		Poster: 'https://m.media-amazon.com/images/M/MV5BODM3YWY4NmQtN2Y3Ni00OTg0LWFhZGQtZWE3ZWY4MTJlOWU4XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '85/100'
			}
		],
		Released: '07 Aug 1992',
		Runtime: '130 min',
		Title: 'Unforgiven',
		Writer: 'David Webb Peoples',
	},
	{
		Actors: 'Robert De Niro, Sharon Stone, Joe Pesci',
		Awards: 'Nominated for 1 Oscar. 4 wins & 11 nominations total',
		BoxOffice: '$42,512,375',
		Country: 'United States, France',
		DVD: '26 Feb 2002',
		Director: 'Martin Scorsese',
		Genre: 'Crime, Drama',
		Language: 'English',
		Plot: 'A tale of greed, deception, money, power, and murder occur between two best friends: a mafia enforcer and a casino executive compete against each other over a gambling empire, and over a fast-living and fast-loving socialite.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMTcxOWYzNDYtYmM4YS00N2NkLTk0NTAtNjg1ODgwZjAxYzI3XkEyXkFqcGdeQXVyNTA4NzY1MzY@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '78%'
			},
			{
				Source: 'Metacritic',
				Score: '73/100'
			}
		],
		Released: '22 Nov 1995',
		Runtime: '178 min',
		Title: 'Casino',
		Writer: 'Nicholas Pileggi, Martin Scorsese',
	},
	{
		Actors: 'Spencer Tracy, Burt Lancaster, Richard Widmark',
		Awards: 'Won 2 Oscars. 16 wins & 25 nominations total',
		BoxOffice: 'N/A',
		Country: 'United States',
		DVD: '14 Sep 2004',
		Director: 'Stanley Kramer',
		Genre: 'Drama, War',
		Language: 'English, German',
		Plot: 'In 1948, an American court in occupied Germany tries four Nazis judged for war crimes.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNDc2ODQ5NTE2MV5BMl5BanBnXkFtZTcwODExMjUyNA@@._V1_SX300.jpg',
		Rated: 'Approved',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.3/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '92%'
			},
			{
				Source: 'Metacritic',
				Score: '60/100'
			}
		],
		Released: '18 Dec 1961',
		Runtime: '179 min',
		Title: 'Judgment at Nuremberg',
		Writer: 'Abby Mann, Montgomery Clift',
	},
	{
		Actors: 'Ivana Baquero, Ariadna Gil, Sergi López',
		Awards: 'Won 3 Oscars. 110 wins & 115 nominations total',
		BoxOffice: '$37,646,380',
		Country: 'Mexico, Spain',
		DVD: '15 May 2007',
		Director: 'Guillermo del Toro',
		Genre: 'Drama, Fantasy, War',
		Language: 'Spanish',
		Plot: 'In the Falangist Spain of 1944, the bookish young stepdaughter of a sadistic army officer escapes into an eerie but captivating fantasy world.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BYzFjMThiMGItOWRlMC00MDI4LThmOGUtYTNlZGZiYWI1YjMyXkEyXkFqcGdeQXVyMjUzOTY1NTc@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '98/100'
			}
		],
		Released: '19 Jan 2007',
		Runtime: '118 min',
		Title: "Pan's Labyrinth",
		Writer: 'Guillermo del Toro',
	},
	{
		Actors: 'Tatsuya Nakadai, Akira Terao, Jinpachi Nezu',
		Awards: 'Won 1 Oscar. 30 wins & 23 nominations total',
		BoxOffice: '$4,135,750',
		Country: 'Japan, France',
		DVD: '22 Nov 2005',
		Director: 'Akira Kurosawa',
		Genre: 'Action, Drama, War',
		Language: 'Japanese',
		Plot: 'In Medieval Japan, an elderly warlord retires, handing over his empire to his three sons. However, he vastly underestimates how the new-found power will corrupt them and cause them to turn on each other...and him.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BNTEyNjg0MDM4OF5BMl5BanBnXkFtZTgwODI0NjUxODE@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '96%'
			},
			{
				Source: 'Metacritic',
				Score: '96/100'
			}
		],
		Released: '01 Jun 1985',
		Runtime: '162 min',
		Title: 'Ran',
		Writer: 'Akira Kurosawa, Hideo Oguni, Masato Ide',
	},
	{
		Actors: 'Russell Crowe, Ed Harris, Jennifer Connelly',
		Awards: 'Won 4 Oscars. 37 wins & 69 nominations total',
		BoxOffice: '$170,742,341',
		Country: 'United States',
		DVD: '25 Jun 2002',
		Director: 'Ron Howard',
		Genre: 'Biography, Drama',
		Language: 'English',
		Plot: 'After John Nash, a brilliant but asocial mathematician, accepts secret work in cryptography, his life takes a turn for the nightmarish.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMzcwYWFkYzktZjAzNC00OGY1LWI4YTgtNzc5MzVjMDVmNjY0XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '74%'
			},
			{
				Source: 'Metacritic',
				Score: '72/100'
			}
		],
		Released: '04 Jan 2002',
		Runtime: '135 min',
		Title: 'A Beautiful Mind',
		Writer: 'Akiva Goldsman, Sylvia Nasar',
	},
	{
		Actors: 'Bruce Willis, Haley Joel Osment, Toni Collette',
		Awards: 'Nominated for 6 Oscars. 37 wins & 56 nominations total',
		BoxOffice: '$293,506,292',
		Country: 'United States',
		DVD: '02 Sep 2003',
		Director: 'M. Night Shyamalan',
		Genre: 'Drama, Mystery, Thriller',
		Language: 'English, Latin, Spanish',
		Plot: 'A frightened, withdrawn Philadelphia boy who communicates with spirits seeks the help of a disheartened child psychologist.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMWM4NTFhYjctNzUyNi00NGMwLTk3NTYtMDIyNTZmMzRlYmQyXkEyXkFqcGdeQXVyMTAwMzUyOTc@._V1_SX300.jpg',
		Rated: 'PG-13',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '86%'
			},
			{
				Source: 'Metacritic',
				Score: '64/100'
			}
		],
		Released: '06 Aug 1999',
		Runtime: '107 min',
		Title: 'The Sixth Sense',
		Writer: 'M. Night Shyamalan',
	},
	{
		Actors: 'Graham Chapman, John Cleese, Eric Idle',
		Awards: '3 wins & 3 nominations',
		BoxOffice: '$1,827,696',
		Country: 'United Kingdom',
		DVD: '08 Jun 2004',
		Director: 'Terry Gilliam, Terry Jones',
		Genre: 'Adventure, Comedy, Fantasy',
		Language: 'English, French, Latin',
		Plot: 'King Arthur and his Knights of the Round Table embark on a surreal, low-budget search for the Holy Grail, encountering many, very silly obstacles.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BN2IyNTE4YzUtZWU0Mi00MGIwLTgyMmQtMzQ4YzQxYWNlYWE2XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '97%'
			},
			{
				Source: 'Metacritic',
				Score: '91/100'
			}
		],
		Released: '25 May 1975',
		Runtime: '91 min',
		Title: 'Monty Python and the Holy Grail',
		Writer: 'Graham Chapman, John Cleese, Eric Idle',
	},
	{
		Actors: 'Daniel Day-Lewis, Paul Dano, Ciarán Hinds',
		Awards: 'Won 2 Oscars. 116 wins & 137 nominations total',
		BoxOffice: '$40,222,514',
		Country: 'United States',
		DVD: '08 Apr 2008',
		Director: 'Paul Thomas Anderson',
		Genre: 'Drama',
		Language: 'English, American Sign ',
		Plot: 'A story of family, religion, hatred, oil and madness, focusing on a turn-of-the-century prospector in the early days of the business.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMjAxODQ4MDU5NV5BMl5BanBnXkFtZTcwMDU4MjU1MQ@@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '91%'
			},
			{
				Source: 'Metacritic',
				Score: '93/100'
			}
		],
		Released: '25 Jan 2008',
		Runtime: '158 min',
		Title: 'There Will Be Blood',
		Writer: 'Paul Thomas Anderson, Upton Sinclair',
	},
	{
		Actors: 'Jim Carrey, Ed Harris, Laura Linney',
		Awards: 'Nominated for 3 Oscars. 40 wins & 69 nominations total',
		BoxOffice: '$125,618,201',
		Country: 'United States',
		DVD: '23 Aug 2005',
		Director: 'Peter Weir',
		Genre: 'Comedy, Drama',
		Language: 'English',
		Plot: 'An insurance salesman discovers his whole life is actually a reality TV show.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BMDIzODcyY2EtMmY2MC00ZWVlLTgwMzAtMjQwOWUyNmJjNTYyXkEyXkFqcGdeQXVyNDk3NzU2MTQ@._V1_SX300.jpg',
		Rated: 'PG',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '90/100'
			}
		],
		Released: '05 Jun 1998',
		Runtime: '103 min',
		Title: 'The Truman Show',
		Writer: 'Andrew Niccol',
	},
	{
		Actors: 'Toshirô Mifune, Eijirô Tôno, Tatsuya Nakadai',
		Awards: 'Nominated for 1 Oscar. 4 wins & 2 nominations total',
		BoxOffice: '$46,808',
		Country: 'Japan',
		DVD: '23 Jan 2007',
		Director: 'Akira Kurosawa',
		Genre: 'Action, Drama, Thriller',
		Language: 'Japanese',
		Plot: 'A crafty ronin comes to a town divided by two criminal gangs and decides to play them against each other to free the town.',
		Poster: 'https://m.media-amazon.com/images/M/MV5BZThiZjAzZjgtNDU3MC00YThhLThjYWUtZGRkYjc2ZWZlOTVjXkEyXkFqcGdeQXVyNTA4NzY1MzY@._V1_SX300.jpg',
		Rated: 'Not Rated',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.2/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '95%'
			},
			{
				Source: 'Metacritic',
				Score: '93/100'
			}
		],
		Released: '13 Sep 1961',
		Runtime: '110 min',
		Title: 'Yojimbo',
		Writer: 'Akira Kurosawa, Ryûzô Kikushima',
	},
	{
		Actors: 'Arnold Schwarzenegger, Linda Hamilton, Michael Biehn',
		Awards: '8 wins & 6 nominations',
		BoxOffice: '$38,371,200',
		Country: 'United Kingdom, United States',
		DVD: '02 Oct 2001',
		Director: 'James Cameron',
		Genre: 'Action, Sci-Fi',
		Language: 'English, Spanish',
		Plot: "A human soldier is sent from 2029 to 1984 to stop an almost indestructible cyborg killing machine, sent from the same year, which has been programmed to execute a young woman whose unborn son is the key to humanity's future salvation",
		Poster: 'https://m.media-amazon.com/images/M/MV5BYTViNzMxZjEtZGEwNy00MDNiLWIzNGQtZDY2MjQ1OWViZjFmXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
		Rated: 'R',
		Ratings: [
			{
				Source: 'Internet Movie Database',
				Score: '8.1/10'
			},
			{
				Source: 'Rotten Tomatoes',
				Score: '100%'
			},
			{
				Source: 'Metacritic',
				Score: '84/100'
			}
		],
		Released: '26 Oct 1984',
		Runtime: '107 min',
		Title: 'The Terminator',
		Writer: 'James Cameron, Gale Anne Hurd, William Wisher',
	}
] RETURN NONE;

FOR $data in (SELECT * FROM naive_movie) {
    LET $movie = CREATE ONLY movie SET
        awards = $data.Awards,
		box_office = IF $data.BoxOffice = 'N/A' { NONE } ELSE { <int>$data.BoxOffice.replace('$', '').replace(',', '') },
		dvd_released = IF $data.DVD = 'N/A' { NONE } ELSE { fn::date_to_datetime($data.DVD) },
		genres = $data.Genre.split(', '),
		imdb_rating = fn::get_imdb($data.Ratings),
		languages = $data.Language.split(', '),
		metacritic_rating = fn::get_metacritic($data.Ratings),
		oscars_won = fn::get_oscars(awards),
        plot = $data.Plot,
        poster = $data.Poster,
        rated = $data.Rated,
		released = fn::date_to_datetime($data.Released),
        rt_rating = fn::get_rt($data.Ratings),
        runtime = <duration>$data.Runtime.replace(' min', 'm'),
        title = $data.Title;

    FOR $name IN $data.Actors.split(", ") {
	LET $actor = (SELECT * FROM ONLY person WHERE name = $name LIMIT 1);
	LET $actor = IF $actor IS NONE {
		(CREATE ONLY person SET name = $name, roles += "actor")
	} ELSE {
		IF "actor" NOT IN $actor.roles {
			UPDATE $actor SET roles += "actor"
		};
		$actor
	};
    RELATE $actor->starred_in->$movie;
    };

    FOR $name IN $data.Director.split(", ") {
	LET $director = (SELECT * FROM ONLY person WHERE name = $name LIMIT 1);
	LET $director = IF $director IS NONE {
		(CREATE ONLY person SET name = $name, roles += "director")
	} ELSE {
		IF "director" NOT IN $director.roles {
			UPDATE $director SET roles += "director"
		};
		$director
	};
    RELATE $director->directed->$movie;
    };

    FOR $name IN $data.Writer.split(", ") {
	LET $writer = (SELECT * FROM ONLY person WHERE name = $name LIMIT 1);
	LET $writer = IF $writer IS NONE {
		(CREATE ONLY person SET name = $name, roles += "actor")
	} ELSE {
		IF "writer" NOT IN $writer.roles {
			UPDATE $writer SET roles += "writer"
		};
		$writer
	};
    RELATE $writer->wrote->$movie;
    };

	FOR $name IN $data.Country.split(", ") {
	LET $country = (SELECT * FROM ONLY country WHERE name = $name LIMIT 1);
	LET $country = IF $country IS NONE {
		(CREATE ONLY country SET name = $name)
	} ELSE {
		$country
	};
    RELATE $country->has_movie->$movie;
    };
};

	DEFINE PARAM $INITIATED VALUE true;
}"#;