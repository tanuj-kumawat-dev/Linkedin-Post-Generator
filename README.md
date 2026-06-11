# LinkCraft AI — Premium LinkedIn Post Generator

A high-fidelity, premium AI-powered LinkedIn Post Generator built with a FastAPI backend and a custom dark-themed Glassmorphic Vanilla HTML/CSS/JS frontend. Designed specifically for serverless deployment on **Vercel**.

## Project Structure
```
├── api/
│   ├── agent.py          # AI agent flow (Outline -> Draft -> Refine/Scrub)
│   ├── index.py          # FastAPI application serverless entry point
│   └── requirements.txt  # Python requirements
├── public/
│   ├── index.html        # Clean semantic interface layout
│   ├── style.css         # Modern glassmorphism system & keyframe animations
│   └── app.js            # Fetch calls, copying functionality & active loading sequences
├── vercel.json           # Routes mapping configuration for Vercel functions
└── README.md             # This file
```

---

## 🔒 Security Best Practices (Handling API Keys Safely)

To prevent security breaches and unauthorized API usage:

1. **Never Hardcode Secrets**: 
   Avoid placing the raw API key anywhere in the git history or source code files (`agent.py`, `index.py`, etc.).
2. **Environment Variables**:
   The application references `os.environ.get("GEMINI_API_KEY")`. Always store your credentials in environment variables.
3. **Set Up on Vercel Dashboard**:
   When deploying the project to Vercel:
   - Navigate to your Vercel Project Dashboard.
   - Go to **Settings** > **Environment Variables**.
   - Add a new variable named `GEMINI_API_KEY` and paste your Gemini API key as the value.
   - Save and redeploy. Vercel injects this securely on the server-side, keeping it completely hidden from client-side browsers.
4. **Local Development Config**:
   For local testing, run the app using commands that inject the key in memory temporarily rather than checking in a configuration file:
   - **PowerShell (Windows)**:
     ```powershell
     $env:GEMINI_API_KEY="your_api_key_here"
     python -m uvicorn api.index:app --reload
     ```
   - **Command Prompt (Windows)**:
     ```cmd
     set GEMINI_API_KEY=your_api_key_here
     python -m uvicorn api.index:app --reload
     ```
   - **Bash/Terminal (Linux/macOS)**:
     ```bash
     export GEMINI_API_KEY="your_api_key_here"
     python -m uvicorn api.index:app --reload
     ```
5. **GitIgnore Settings**:
   Always make sure standard files containing local environment definitions (like `.env` or local profiles) are included in `.gitignore` so they are never pushed to GitHub.

---

## 🛠️ Local Development Setup

To run and test the project locally, ensure you have **Python 3.12** installed:

1. **Install Dependencies**:
   Open a terminal and navigate to the project directory:
   ```bash
   pip install -r api/requirements.txt
   ```

2. **Configure Your API Key**:
   In your terminal, set the `GEMINI_API_KEY` env variable (refer to instructions above).

3. **Start the Local Development Server**:
   ```bash
   python -m uvicorn api.index:app --reload
   ```

4. **Access the App**:
   Open your browser and navigate to:
   - Frontend: `http://localhost:8000/index.html`
   - Health Check: `http://localhost:8000/api/health`
