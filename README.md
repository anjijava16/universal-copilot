# universal-copilot
universal-copilot

## End to End Flow VS Code agent chat Simple Hi 
```
[User types "hi" in VS Code agent chat]
        ↓
VS Code collects:
  - System prompt (predefined)
  - User message
  - Available tools (76 schemas)
        ↓
Request sent to Copilot backend
        ↓
Backend routes to claude-haiku-4.5 with 39k prompt tokens
        ↓
Model processes:
  - Reads system instructions
  - Sees tools but decides none are needed
  - Generates "Hi! What would you like to work on with ScrapeAgent?"
        ↓
Response (61 tokens) sent back to VS Code
        ↓
VS Code displays message in the chat panel

```
