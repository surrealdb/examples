# SurrealDB Stickies

This repository is a monorepo that contains both the server and client code for the SurrealDB Stickies.

The repository is organized into two main directories:

- `server/`: This directory contains the backend server code, written in Node.js and Express.
- `client/`: This directory contains the frontend client code, built using React.

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
cd server && npm install
cd ../client && npm install
cd ..
```
### 4. Start the server
Use the following command to start the server:

```bash
yarn run server
```

### Start the client
In a new terminal window, start the client:

```bash
yarn run client
```
You should now be able to access the Notes App in your web browser at http://localhost:3000.


