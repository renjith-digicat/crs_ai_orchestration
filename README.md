# AI Assisted Cyber Resilience and Security (CRS) orchestration
An experimental AI assistant for CRS orchestration..

## Current Capabilities:

- #TODO: CRS Orchestration
    Explain details..

## Flow diagram of the application

- #TODO: Define the architecture and add the mermaid diagram here


## Developer Guidelines

### 1. Prerequisites

- **pyenv**: Manage Python versions
  Follow the [pyenv installation guide](https://github.com/pyenv/pyenv#installation).

- **uv**: Rust‑based package & venv manager
  Install via:
  ```bash
  curl -Ls https://astral.sh/uv/install.sh | sh
(See full docs at https://astral.sh/uv)

### 2. Setup python 3.12 or higher

```shell
pyenv install —list   # List all installed python versions

pyenv install 3.12.6  # Install the specific     python version

pyenv local 3.12.6  # set local python version

uv venv  # create a virtual environment
```

### 3. Install dependencies
```shell
uv pip install .  # install the project dependencies from the pyproject.toml file
```

### 4. Add the following environment variables to the `.env` file
- `OLLAMA_API_KEY=ollama`
- `OLLAMA_BASE_URL=http://localhost:11434/v1`
- `OPENAI_API_KEY=<your openai api key>`
- `GROQ_BASE_URL=https://api.groq.com/openai/v1`
- `GROQ_API_KEY=<your groq api key>`

**Note-1**: It will use your APIs to call the model. So beware of the number of API calls you make, rate limit, number of tokens etc.

**Note-2**: You need to create an account with the relevant services like openai or groq, and login to the relevant services and login and get the API keys.

### 5. Get a Brave Web Search API Key and add it to the `.env` file
- Sign up for a [Brave Search API account](https://brave.com/search/api/)
- Choose a plan (Free tier available with 2,000 queries/month)
- Generate your API key from [the developer dashboard](https://api.search.brave.com/app/keys)
- `BRAVE_SEARCH_API_KEY=<your brave search api key>`

### 5. Run the application
```shell
uv run streamlit run app.py
```

Then go to the `http://localhost:8501/` on your browser to use the UI to chat to the AI assistant.


### Note: *Tips for fromatting the code before committing*

- `uvx ruff check .` to lint the whole repo
-  `uvx ruff check . --fix` to fix the linting errors
- `uvx ruff format .` to format the whole repo
- `uvx ruff check . --diff` to see the changes

