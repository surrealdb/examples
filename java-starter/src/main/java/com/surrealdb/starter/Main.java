package com.surrealdb.starter;

import com.surrealdb.*;
import com.surrealdb.starter.factory.BookFactory;
import com.surrealdb.starter.factory.PublisherFactory;
import com.surrealdb.starter.model.Book;
import com.surrealdb.starter.model.Publisher;

import java.time.ZonedDateTime;
import java.util.Iterator;

public class Main {

    public static void main(String[] args) {

        // Instantiate the driver
        try (final Surreal driver = new Surreal()) {
            // Connect to an in-memory database
            driver.connect("memory");

            // Select a namespace and database
            driver.useNs("example").useDb("example");

            // Instantiate factory classes
            PublisherFactory publisherFactory = new PublisherFactory(driver);
            BookFactory bookFactory = new BookFactory(driver);

            // Create our models
            Publisher surrealdb = publisherFactory.createPublisher("SurrealDB");
            Book aeon = bookFactory.createBook(
                "Aeon's Surreal Renaissance",
                "Dave MacLeod",
                ZonedDateTime.parse("2024-10-15T00:00:00Z"),
                surrealdb
            );

            System.out.println("Created publisher: " + surrealdb.id);
            System.out.println("Created book: " + aeon.id);


            // Make the book unavailable
            aeon.available = false;

            driver.update(Book.class, aeon.id, UpType.CONTENT, aeon);


            // Create a second book
            Book surrealist = bookFactory.createBook(
                "Surrealist for dummies",
                "Julian Mills",
                ZonedDateTime.now(),
                surrealdb
            );

            System.out.println("Created book: " + surrealist.id);


            // Select all known books
            Iterator<Book> allBooks = driver.select(Book.class, "book");

            System.out.println("\nBooks:");

            while (allBooks.hasNext()) {
                Book book = allBooks.next();
                System.out.println("- " + book);
            }


            // Make all books available
            Book update = new Book();

            update.available = true;

            Iterator<Book> updatedBooks = driver.update(Book.class, "book", UpType.MERGE, update);

            System.out.println("\nUpdated books:");

            while (updatedBooks.hasNext()) {
                Book book = updatedBooks.next();
                System.out.println("- " + book);
            }


            // Select books by author
            Response response = driver.query("SELECT * FROM book WHERE author = 'Dave MacLeod'");
            Iterator<Book> booksByAuthor = response.take(0).getArray().iterator(Book.class);

            System.out.println("\nBooks by Dave MacLeod:");

            while (booksByAuthor.hasNext()) {
                Book book = booksByAuthor.next();
                System.out.println("- " + book);
            }


            // Delete all books and the publisher
            driver.delete("book");
            driver.delete(surrealdb.id);

        }
    }

}
