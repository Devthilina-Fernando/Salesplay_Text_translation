# Salesplay Text Translation

This project provides a backend server for translating strings using OpenAI and managing translations with MySQL.

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
   - **Windows**  
     ```bash
     python -m venv venv
     ```
   - **Linux/macOS**  
     ```bash
     python3 -m venv venv
     ```
4. **Activate the environment**  
   - **Windows**  
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/macOS**  
     ```bash
     source venv/bin/activate
     ```
5. **Install Python dependencies**  
   ```bash
   pip install -r requirements.txt
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


If you don't have gettext, download it from the bellow link and install it

for windows
https://gnuwin32.sourceforge.net/packages/gettext.htm

for linux

