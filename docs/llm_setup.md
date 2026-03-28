# LLM Services

Advanced analysis features (e.g., project summaries using an LLM) use the **Groq API**. This integration is optional and fully consent-based.

If no Groq API key is provided, the system will fall back to local-only analysis.

---

#### How to Set Up a Groq API Key

1. Log in or create a Groq account:
   - https://console.groq.com/login

2. Create an API key:
   - https://console.groq.com/keys

3. Add the following to you `.env` file in the project root:
    ```env
    GROQ_API_KEY=<your-groq-api-key>
    ```

> **Security Note** 
> API keys should never be committed to version control.
> The `.env` file is ignored via `.gitignore`, and a template (`.env.example`) is provided for reference.