# Surreal Stickies SvelteKit: Adding Graph Relations, Live Queries, and Authentication.

This application demonstrates how to use SurrealDB features like Live Queries, Authentication, Indexing and Graph Queries in your applications. Unlike the previous version of notes app in which we built an API layer and connected with SurrealDB on the server side, in this application, we securely connect to the database client side.

## 🛠 Setup and Installation

### Prerequisites

- Make sure you have `bun` installed.

### Steps

#### Clone the Examples Repository

```bash
git clone https://github.com/surrealdb/examples.git
```

#### Navigate to the Notes-Kit Directory

```bash
cd examples/notes-kit
```
#### Install Dependencies (First Time Only)

```bash
bun i
```

#### Instantiate a Local Database instance

```bash
surreal start --bind 127.0.0.1:3001 --user root --pass surrealdb
```

#### Start the Frontend and Database

```bash
bun dev

```
#### Connect to SurrealDB Instance

```bash
surreal sql --conn ws://localhost:3001 --user root --pass root --ns test --db test --pretty
```

#### Execute Schema Queries
Manually go over all the .surql files in the src/schema directory and execute all the queries.

#### 🌟 Features
The notes-v2 app extends the previous notes app with new features like live updates, tags and multi-user login. 

#### 📣 Show and Tell
We'd love to see what you build with this example! Share your projects and tag @SurrealDB on [Twitter](https://twitter.com/SurrealDB)!

#### 📞 Join the Conversation
Join our [Discord](https://discord.gg/surrealdb) community to stay updated, get your questions answered, and showcase your projects.
