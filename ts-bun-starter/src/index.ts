import { serve, spawnSync } from "bun";
// biome-ignore lint/style/useNodejsImportProtocol: <explanation>
import { join } from "path";
import { cwd } from "process";
import { existsSync } from "fs";

// Helper function to run the script
function executeScript(scriptName: string) {
  // Get the current working directory and resolve the script path
  const scriptPath = join(cwd(), "src", `${scriptName}.ts`);

  // Check if the script file exists
  if (!existsSync(scriptPath)) {
    return `Error: Script file "${scriptName}.ts" not found in the src directory.`;
  }

  const result = spawnSync(["bun", scriptPath], {
    stdout: "pipe",
    stderr: "pipe",
  });

  if (result.success) {
    return result.stdout.toString();
  }
  return `Error executing script: ${result.stderr.toString()}`;
}

// Start the server
serve({
  port: 3000,
  fetch(req) {
    const url = new URL(req.url);
    const script = url.searchParams.get("script");

    if (script) {
      const output = executeScript(script);
      return new Response(output, {
        headers: { "Content-Type": "text/plain" },
      });
    }

    // Serve HTML UI with buttons
    return new Response(
      `
   <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Script Runner</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
          }
          .container {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
          }
          h1 {
            color: #333;
          }
          .button {
            background-color: #ff00a0;
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            margin: 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
          }
          .button:hover {
            background-color: #007bff;
          }
          #output {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            text-align: left;
            white-space: pre-wrap;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Interact with Scripts</h1>
          <button class="button" onclick="runScript('surreal')">Start Database</button>
          <button class="button" onclick="runScript('create')">Run Create Script</button>
          <button class="button" onclick="runScript('delete')">Run Delete Script</button>
          <button class="button" onclick="runScript('select')">Run Select Script</button>
          <button class="button" onclick="runScript('update')">Run Update Script</button>
          <pre id="output"></pre>
        </div>
        <script>
          function runScript(script) {
            fetch(\`/?script=\${script}\`)
              .then(response => response.text())
              .then(text => {
                document.getElementById('output').textContent = text;
              })
              .catch(error => {
                document.getElementById('output').textContent = 'Error: ' + error;
              });
          }
        </script>
      </body>
      </html>
      `,
      { headers: { "Content-Type": "text/html" } }
    );
  },
});