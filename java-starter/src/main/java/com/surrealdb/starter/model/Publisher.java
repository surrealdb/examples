package com.surrealdb.starter.model;

import com.surrealdb.RecordId;

import java.time.ZonedDateTime;

public class Publisher {
    public RecordId id;
    public String name;

    //  A default constructor is required
    public Publisher() {
    }

    public Publisher(String name) {
        this.name = name;
    }

    @Override
    public String toString() {
        return "Publisher{" +
            "id=" + id +
            ", name='" + name + '\'' +
            '}';
    }
}
