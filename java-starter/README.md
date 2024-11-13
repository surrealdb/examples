# SurrealDB Java Starter

This example introduces you to the basics of the SurrealDB Java SDK. The application mimics a book library system which tracks books and publishers. While rudimentary, it demonstrates the core concepts of the SDK.

## 🚀 Quick start guide

This tutorial is inspired by the [Java Quick Start](https://surrealdb.com/docs/sdk/java/start) guide, which provides an in-depth explanation for code used in this example.

## ✅ Prerequisites

- You have a basic understanding of Java and the Java Runtime Environment.
- You have Java 8 or higher installed on your machine.
- You have a suitable IDE installed, such as IntelliJ IDEA or Eclipse.

## 🛠 Setup and installation

1. Clone the repository
2. Open the project in your favorite IDE (IntelliJ IDEA, Eclipse, etc.)
3. Run the `Main.java` file

## 📝 Code overview

The example consists of three parts to demonstrate a simple CRUD setup.

### Model Classes

The model classes define the structure of the data that will be stored in the database. In this example, we have two model classes: `Book` and `Publisher`. Both expose a required public zero-argument constructor, and their fields represent columns in the database.

### Factory Classes

The factory classes are responsible for creating the necessary records in the database and converting these to their model class representations. In this example, we have two factory classes: `BookFactory` and `PublisherFactory`.

### Main Class

The `Main` class contains code to interact with the factories and models, and demonstrates how to use the most important methods to perform CRUD operations on the database.

## 📚 Resources

- [Quick Start](https://surrealdb.com/docs/sdk/java/start)
- [Data types](https://surrealdb.com/docs/sdk/java/data-types)
- [JavaDoc](https://surrealdb.github.io/surrealdb.java/javadoc/)