# SurrealDB Stickies

This repository is a monorepo that contains both the server and client code for the SurrealDB Stickies.

The repository is organized into two main directories:

- `server/`: This directory contains the backend server code, written in Node.js and Express.
- `client/`: This directory contains the frontend client code, built using React.

## Before commiting

We enforce linting rules in this repository. Please make sure to run `pnpm lint --fix` before you commit and ensure that every issue is fixed.

## Getting Started

Follow these steps to get the project up and running:

### 1. Clone the repository

```bash
git clone https://github.com/timpratim/surrealstickies.git
```
### 2. Navigate into the cloned repository

```bash
cd surrealstickies
```

### 3. Install dependencies
You'll need to install dependencies for both the server and client directories:

```bash
pnpm install
```

### 4. Setup your environment
Copy the `server/.env.example` into `server/.env`. The default options should be good for development but feel free to change where needed.

### 5. Start the client, server and surreal instance!
Use the following command to start the server:

```bash
pnpm dev
```

You should now be able to access the Notes App in your web browser at http://localhost:3000.


