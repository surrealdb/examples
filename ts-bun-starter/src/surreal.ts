import { spawn } from "child_process";

console.log("Starting SurrealDB...");

const surrealProcess = spawn("surreal", ["start", "--unauthenticated"], {
  stdio: "inherit",
});

surrealProcess.on("error", (error) => {
  console.error("Failed to start SurrealDB:", error.message);
});

surrealProcess.on("exit", (code) => {
  if (code === 0) {
    console.log("SurrealDB process exited successfully");
  } else {
    console.error(`SurrealDB process exited with code ${code}`);
  }
});

// Keep the script running
process.stdin.resume();