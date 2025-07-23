# Salesplay Text Translation

This project provides a backend server for translating strings using OpenAI and managing translations with MySQL.

---

## 🚀 Prerequisites

Install `uv` via `pipx` (if you don’t already have it):

```bash
python -m pip install --user pipx
python -m pipx ensurepath
pipx install uv
```

> **After installation**, restart your terminal.

---

## 🔧 Setup & Installation

1. **Clone the repository**  
   ```bash
   git clone <your_repo_url>
   ```
2. **Enter the backend directory**  
   ```bash
   cd backend
   ```
3. **Create a virtual environment**  
   ```bash
   uv venv
   ```
4. **Activate the environment**  
   - **Windows**  
     ```bash
     .\.venv\Scripts\activate
     ```
   - **Linux/macOS**  
     ```bash
     source .venv/bin/activate
     ```
5. **Install Python dependencies**  
   ```bash
   uv pip install -r requirements.txt
   ```
6. **Configure environment variables**  
   Create a file named `.env` in the `backend` folder and add:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   MYSQL_HOST=your_mysql_host
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_PORT=your_mysql_port
   MYSQL_DB=your_database_name
   MSGFMT_PATH=path_to_msgfmt_executable
   ```

---

## 🖥️ Running the Server

- **Default port (8000)**  
  ```bash
  uvicorn main:app --reload
  ```
- **Custom port (e.g., 5000)**  
  ```bash
  uvicorn main:app --reload --port 5000
  ```

---

## 🛑 Stopping the Server

Press <kbd>Ctrl</kbd> + <kbd>C</kbd> in the terminal.

---
