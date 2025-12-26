# How to Use SurrealDB with Tanstack Query

This tutorial will guide you through the steps to integrate SurrealDB with a React application using Tanstack Query (formerly React Query). We'll cover setting up the database, fetching data, and displaying it in a React component.

## Prerequisites

- Node.js and npm installed
- Basic knowledge of React and TypeScript
- SurrealDB installed

## Step 1: Setting Up SurrealDB

First, ensure that SurrealDB is installed and running.

```bash
surreal start --user root --pass root
```

## Step 2: Create the React Application

Create a new React application using Create React App with TypeScript. In this example we use Vite.

```bash
npm create vite@latest surrealdb-query --template react-ts
cd surrealdb-query
```

## Step 3: Install Dependencies

Install Tanstack Query (React Query) and SurrealDB client.

```bash
npm install @tanstack/react-query surrealdb.js
```