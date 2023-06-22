# Tutorial: Build a Notes App with Next.js, Tailwind and SurrealDB

SurrealDB is a multi-model cloud database, suitable for serverless applications, jamstack applications, single-page applications, and traditional applications. SurrealDB supports SQL querying from client devices, GraphQL, ACID transactions, WebSocket connections, structured and unstructured data, graph querying, full-text indexing, and geospatial querying. In this guide, you'll learn how to implement a sample full-stack notes taking application called Surreal Stickies using: 

- [SurrealDB](https://surrealdb.com/install): for our database operations
- [Next.js](https://nextjs.org/docs/getting-started/installation): for building our server-rendered React application
- [SWR](https://swr.vercel.app/): for reactive data fetching
- [Tailwind](https://tailwindcss.com/docs/installation): for styling our application

With Surreal Stickies, you can add, update and delete notes at your convenience. You can create two types of stickies — a purple one and a pink one.

![SurrealDB Stickies](https://github.com/timpratim/surrealstickies/assets/32492961/48fcb6f4-b0f9-47c4-8ed7-da059272b458)

## Architecture

![architecture](https://github.com/surrealdb/examples/assets/32492961/7e044fb0-e2b3-44a8-b71e-ceba600efc0d)



## **Prerequisites**

Before you begin this tutorial you'll need the following:

- [SurrealDB](https://surrealdb.com/install) installed on your machine
- [Node.js](https://nodejs.org/en/download) installed locally on your computer
- A basic understanding of Next.js and Tailwind
- One of the following package managers: [npm](https://nodejs.org/en/download), [pnpm](https://pnpm.io/installation) or [yarn](https://classic.yarnpkg.com/lang/en/docs/install/#debian-stable)

## Step 1: Install the SurrealDB library

The [SurrealDB](https://surrealdb.com/docs/integration/libraries/javascript) driver for JavaScript enables simple and advanced querying of a remote database from a browser or from server-side code. All connections to SurrealDB are made over WebSockets, and automatically reconnect when the connection is terminated.

Install the SurrealDB library using `npm`, `yarn` or `pnpm`

```
npm install --save surrealdb.js
yarn add surrealdb.js
pnpm install surrealdb.js
```

## Step 2: Set up your Next.js project.

 1. Create a new Next.js applicatio and install all the dependencies asked by Next.js

```bash
pnpx create-next-app@latest surrealdb-stickies
```

For the complete setup, copy the package.json from the GitHub repository of this application and paste it into your package.json

This sets up the scripts you'll use to develop, build, and run your application. It also includes scripts for TypeScript and ESLint for linting.

- **`dev`**: This is the main development command that runs the SurrealDB server and the Next.js development server concurrently.
- **`dev:surreal`**: This starts the SurrealDB server.
- **`dev:next`**: This starts the Next.js development server.
- **`build`**: This builds the application for production.
- **`start`**: This starts the built application.
- **`ts`**: This runs TypeScript in watch mode.
- **`lint`**: This uses ESLint to analyse your code for errors


## Step 3: Building the CRUD APIs

Surreal stickies have functionalities of creating, viewing, updating and deleting notes. Each of these functionalities essentially leverages the CRUD operations (Create, Read, Update, and Delete) provided by SurrealDB.

- **Creating a New Sticky Note**
    
    When a user clicks on the purple or pink `+` button, Surreal Stickies uses the POST method to create a new record in SurrealDB by calling **`surreal.create`**. 
    
    **Syntax:**
    
    ```jsx
    const result = await surreal.create('sticky', {
        content,
        color,
        created,
        updated,
    });
    ```
    
    A query similar to query below will be executed in your database: 
    
    ```jsx
    CREATE sticky CONTENT {
    	color: 'purple',
    	content: '',
    	created: '2023-06-19T15:37:10.106Z',
    	updated: '2023-06-19T15:37:10.106Z'
    };
    ```
    
    In our example, only the creation of a new note runs the CREATE statement. Adding content to the note runs the UPDATE query
    
- **Updating a Sticky Note**
    
    When the user wishes to edit a sticky note, Surreal Stickies uses the PATCH method. The **`surreal.merge`** function enables the application to merge new data with existing records in SurrealDB.
    
    **Syntax**
    
    ```jsx
    const result = await surreal.merge(`sticky:${id}`, update);
    ```
    
    Modifies all records in a table, or a specific record, in the database.
    
    In our stickies app, once the ID and the sticky are validated by the validateId and validateSticky function is validated we merge only the new additions in our note.
    
    A query similar to query below will be executed in your database:
    
    ```sql
    UPDATE sticky:tq5uwwob82bgm5qq60gz MERGE {
        color: 'purple',
        content: 'SurrealDB is a multi-model database',
        updated: '2023-06-19T15:17:15.442Z'
    };
    ```
    
- **Retrieving a Single Sticky Note**
    
    When a user clicks on a sticky note in the user interface, the application needs to fetch the full details of that specific sticky note from the backend. To do this, the application uses the GET method which retrieves the details of this particular sticky note using the **`surreal.select`** function.
    
    
    **Syntax**:
    
    ```jsx
    const result = await surreal.select(`sticky:${id}`);
    ```
    
    It selects all records in a table, or a specific record, from the database. The argument `thing` stands for the table name or a record ID to select.
    
    The following query will be executed in your database whenever you click on a particular sticky:
    
    ```jsx
    SELECT * FROM sticky ORDER BY updated DESC
    ```
    

- **Retrieving All Sticky Notes**
    
    When the user opens the application or hits a "refresh" button, the application needs to display all the sticky notes. To do this, the application calls the GET method which retrieves all sticky notes from the backend. This method is also called when a new note is added or an existing note is deleted or updated, and the UI needs to reflect these changes by fetching the updated list of all sticky notes.
    
    ```jsx
   
        const result = await surreal.query(
            'SELECT * FROM sticky ORDER BY updated DESC'
        );
    ```
    
    The following query will be executed in your database whenever you click anywhere outside the stickies.
    
    ```sql
    SELECT * FROM sticky ORDER BY updated DESC
    ```
    

- **Deleting a Sticky Note**
    
    When the user clicks on the `x` button, the DELETE method is called.
    **Syntax:**
    
    ```jsx
    const result = await surreal.delete(`sticky:${id}`);
    ```
    
     It validates the **`id`** from the request parameters and subsequently uses **`surreal.delete`** to erase the corresponding record from SurrealDB.
    
    The following query will be executed in your database when you click on the `x` button:
    
    ```jsx
    DELETE * FROM sticky:gp4u59t5wlo0vre5d96j;
    ```
    

Now that we are done with the major parts of the backend we will move towards the front end.

## Step 4: Building the User Interface 

1. **Set up the base layout for our application:** The first thing we'll do is set up our base layout for our application using Next.js and Tailwind CSS. In the file **`src/app/layout.tsx`**, we establish the root layout of our application which includes a navbar, the main content of our page, and a footer.
    

2. **Creating API Calls:** After setting up our layout, we need to create API calling functions that will interact with our backend. These functions are created in the **`src/lib/modifiers.ts`** file and include methods to fetch, create, update, and delete stickies.
    
    Here's the code snippet for **`createSticky`** function:
    
    ```jsx
    export async function createSticky(
        payload: Pick<Sticky, 'color' | 'content'>
    ): Promise<{
        success: boolean;
        sticky?: Sticky;
    }> {
        return await (
            await fetch('/api/sticky', {
                method: 'post',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            })
        ).json();
    }
    ```
    
2. **Creating Hooks:**  After defining our API calling functions, we need to create hooks that will use these functions and manage the state in our components. These hooks are created in the **`src/lib/hooks.ts`** file. Here's an example with the **`useCreateSticky`** hook:
    
    ```jsx
    export const useCreateSticky = () =>
        useSWRMutation(
            `/api/sticky`,
            (_, { arg }: { arg: Parameters<typeof createSticky>[0] }) =>
                createSticky(arg)
        );
    ```
    
    These hooks use the **`useSWR`** and **`useSWRMutation`** hooks from the SWR library for data fetching and mutation. SWR provides a lot of useful features like caching, automatic revalidation, and error retries, which make it easier to manage the server state in a React application.
    
3. **Creating the Home Component:** Now, we're ready to build our **`Home`** component which is the main page of our application. In this component, we use the hooks we’ve just defined previously to fetch, create, and render stickies. We also handle user interactions like creating a new sticky or displaying an error message.

Once you have all the components built, you can run the application on localhost. 
    
The following command will start your SurrealDB server and build your application concurrently. 
    
```jsx
npm run dev
```

    
## Summary
    
In this tutorial, we took a deep dive into the building blocks of a real-world sticky note application built with SurrealDB, Next.js, and Tailwind CSS. The backend was set up with the help of SurrealDB and Next.js. We went through the built-in functions provided by SurrealDB to query the database. All the functions we used here are explained in depth in the [documentation](https://surrealdb.com/docs/integration/libraries/javascript). We built API routes using these functions to handle specific CRUD operations on the sticky notes in the SurrealDB database. 
    
## Conclusion
    
The Notes App showed us a very simple and straightforward implementation of SurrealDB. SurrealDB is a powerful database capable of replacing the complete backend with inbuilt features like multi-tenancy, indexing, live queries, custom functions and many more. 
    
In this tutorial, we only touched on a fraction of what makes SurrealD the ultimate multi-model database. To find out more see you can check out the [SurrealDB features](https://surrealdb.com/features) or our [GitHub repo](https://github.com/surrealdb/surrealdb).
