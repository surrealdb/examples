package com.surrealdb.starter.factory;

import com.surrealdb.Surreal;
import com.surrealdb.starter.model.Publisher;

public class PublisherFactory {

    private final Surreal driver;

    public PublisherFactory(Surreal driver) {
        this.driver = driver;
    }

    public Publisher createPublisher(String name) {
        Publisher publisher = new Publisher(name);

        // Create a new publisher
        return driver.create(Publisher.class, "publisher", publisher).getFirst();
    }

}
