package com.surrealdb.starter.factory;

import com.surrealdb.Surreal;
import com.surrealdb.starter.model.Book;
import com.surrealdb.starter.model.Publisher;

import java.time.ZonedDateTime;

public class BookFactory {

    private final Surreal driver;

    public BookFactory(Surreal driver) {
        this.driver = driver;
    }

    public Book createBook(String title, String author, ZonedDateTime date, Publisher publisher) {
        Book book = new Book(title, author, date, true);

        // Create a new book
        Book created = driver.create(Book.class, "book", book).getFirst();

        // Relate the book to the publisher
        driver.relate(created.id, "published_by", publisher.id);

        return created;
    }

}
