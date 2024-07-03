# TS-Bun-starter

This is a sample project that uses TS + Bun + SurrealDB. 

To install dependencies:

```bash
bun install
```

To run:

```bash
bun run index.ts
```

To start Database:

```bash 
surreal start
```

To Run functions in `/src/`: 

```bash 
-- Create a new user 
bun run src/create.ts
```

```bash 
-- Get all users 
bun run src/select.ts
```

This project was created using `bun init` in bun v1.1.3. [Bun](https://bun.sh) is a fast all-in-one JavaScript runtime.


