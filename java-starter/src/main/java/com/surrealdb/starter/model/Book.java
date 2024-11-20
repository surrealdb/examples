package com.surrealdb.starter.model;

import com.surrealdb.RecordId;

import java.time.ZonedDateTime;

public class Book {
    public RecordId id;
    public String title;
    public String author;
    public ZonedDateTime publishedAt;
    public boolean available;

    //  A default constructor is required
    public Book() {
    }

    public Book(String title, String author, ZonedDateTime publishedAt, boolean available) {
        this.title = title;
        this.author = author;
        this.publishedAt = publishedAt;
        this.available = available;
    }

    @Override
    public String toString() {
        return "Book{" +
                "id=" + id +
                ", title='" + title + '\'' +
                ", author='" + author + '\'' +
                ", publishedAt=" + publishedAt +
                ", available=" + available +
                '}';
    }
}
