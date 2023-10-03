# Surreal Stickies 2.0: Adding Graph Relations, Live Queries, and Authentication.

This application demonstrates how to use SurrealDB features like Live Queries, Authentication, Indexing and Graph Queries in your applications. Unlike the previous version of notes app in which we built an API layer and connectec with SurrealDB on the server side, in this application we securely connect to the database client side.

## 🛠 Setup and Installation

### Prerequisites

- Make sure you have `pnpm` installed. If not, install it using `npm install -g pnpm`.

### Steps

#### Clone the Examples Repository

```bash
git clone https://github.com/your-repo/examples.git
```
#### Navigate to the Notes-V2 Directory
```bash
cd examples/notes-v2
```
#### Install Dependencies (First Time Only)
```bash
pnpm i
```
#### Start the Frontend and Database
```bash
pnpm dev

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