# SurrealPolls 🗳️– Your Gateway to Instant Opinions!

Welcome to **SurrealPolls**, where gathering votes and making decisions has never been easier (or more fun)! Whether you’re planning a group outing, running a class survey, or settling the eternal "pineapple on pizza" debate, we’ve got you covered. 

Built with cutting-edge technologies like **SolidJS**, **Vite**, **SurrealDB**, **Surreal Cloud**, and **Tailwind CSS**, this app is as modern as your need for instant polls.

---

## What’s Inside the Polling Magic?

### **Tech Stack Highlights**:
- **SolidJS**: Super snappy frontend framework for blazing-fast performance and reactivity. Your votes will feel instant, and your app will feel buttery smooth.
- **Tailwind CSS**: Your app is not just functional; it’s also pretty, thanks to this utility-first CSS framework.
- **Surreal Cloud**: Surreal Cloud (Beta) transforms the database experience, providing the power and versatility of SurrealDB without the complexity of managing infrastructure. 



---

## Features That’ll Make You Smile 😄

### 📝 **Create Polls**
Spin up a poll in seconds. Just give it a title, list out some options, and BOOM! A shareable link is ready for your friends, colleagues, or anyone with an opinion.

### ✅ **Vote Away**
Let your participants cast their votes effortlessly. The app ensures a seamless and real-time voting experience, so nobody’s left waiting.

### 🔒 **End Polls**
Want to close the poll and announce the results? No problem! You’re in control. End the poll whenever you’re ready to seal the deal.

### 📊 **Real-Time Results**
Results update in real-time, giving you instant insights into where everyone stands. No refresh button required!

---

## How to Run This Beauty

### Prerequisites
Make sure you have the following installed:
- [Node.js](https://nodejs.org) (v16+)
- [SurrealDB](https://surrealdb.com) (running locally or remotely)

### Installation
Ready to dive in? Let’s go!

1. Clone the repo:
   ```bash
   git clone https://github.com/your-repo/polling-app.git
   cd polling-app
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Connect to a SurrealDB Cloud Instance via CLI:

    When you have a SurrealDB Cloud instance running, you can [connect to it using the SurrealDB CLI](https://surrealdb.com/docs/cloud/connect/cli) and this will give you an endpoint to use in the make file.  

    Copy the endpoint without the `surreal sql` prefix as you will be making an import into the database.

    ```bash
   --endpoint <endpoint> --token <token>
    ```
 > We recommend using [Surrealist](https://surrealist.dev) the GUI for SurrealDB Cloud to manage and create your database users. 

4.  Create a database user in the Authentication section of Surrealist as you will need to use the username and password to connect to the database from the frontend.

4. Mirroring  the `.env.example` file, create an `.env` file in the root of the project and set the `VITE_DB_HOST` and `DB_TOKEN` to the endpoint and token you copied from the CLI. Then, set the `VITE_DB_USER` to `root` and `VITE_DB_PASS` to `root`. 


5. Apply the schema: Use the included Makefile to set up your database schema:
    ```bash
    make apply
    ```
    This will automatically apply all .surql files in the schema directory to your SurrealDB instance.

5. Configure SurrealDB in `src/lib/providers/surrealdb.tsx` if needed (default is localhost).

6. Run the development server:
   ```bash
   npm run dev
   ```

7. Open your browser at [http://localhost:3000](http://localhost:3000) and start polling!

---

## File Structure
Here’s how this masterpiece is organized:

```
/surrealpolls
|-- /src
|   |-- /assets         # Static assets like icons
|   |-- /components     # Reusable UI components
|   |   |-- Footer      # Footer component
|   |   |-- Navbar      # Navbar component
|   |-- /lib            # Logic and utility files
|   |   |-- /providers  # Context providers (e.g., surrealdb.tsx)
|   |   |-- utils.ts    # Helper functions
|   |-- /pages          # Pages for routing (Home, Create Poll, Vote, Results)
|   |-- /styles         # Global styles (index.css)
|   |-- App.tsx         # The main app component
|   |-- index.tsx       # Entry point of the app
|   |-- routes.tsx      # App routes
|-- /public             # Public files (e.g., favicon)
|-- /.env.example       # Example env file
|-- Makefile            # For schema management
|-- tailwind.config.js  # Tailwind configuration
|-- vite.config.ts      # Vite configuration
```

---

## Things You Can Try
- **Create Your First Poll**: Go to the “Create Poll” page, add some options, and share the generated link.
- **Test Real-Time Voting**: Open the voting link in two different tabs/devices and watch the magic happen.
- **End a Poll**: Close a poll to stop further voting and see the results instantly.

---

## Why Use This App?
- **Speedy Setup**: It’s quick to build and deploy—thanks to SolidJS and Vite.
- **Beautiful UI**: Tailwind CSS makes everything look polished without extra effort.
- **Powerful Backend**: SurrealDB ensures your data is safe, scalable, and lightning-fast.
- **Open Source**: Customize it to your heart’s content.

---

## Contributing
Feel free to fork the repo, make improvements, and send us a pull request. We’re always open to ideas that make polling better (and cooler)!

---

## License
This project is licensed under the MIT License—because sharing is caring. 😊

---

Happy polling! 🎉

