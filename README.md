# LearnUp Platform - Beginner's Guide

Welcome to **LearnUp**! This is a complete, full-stack application built using a **Django (Python)** backend and a **Next.js (Node.js)** frontend. 

Since you're a beginner, this guide will walk you through exactly how to set up everything on your Windows computer from scratch, step by step! Don't worry if you haven't used MySQL or WAMP/XAMPP before—we will cover everything.

---

## 🛠️ Step 0: Install Prerequisites

Before starting the code, you need to download and install a few basic tools on your computer:

1. **Python (for the backend):** Download [Python 3.12](https://www.python.org/downloads/) and install it. **Crucial:** During installation, make sure you check the box that says `"Add Python to PATH"`.
2. **Node.js (for the frontend):** Download [Node.js (LTS version)](https://nodejs.org/en/) and install it.
3. **XAMPP (for the database):** Since our project uses MySQL, the easiest way to run it is by downloading [XAMPP for Windows](https://www.apachefriends.org/index.html).
4. **Ollama (for the AI features):** Download [Ollama](https://ollama.com/) to run the local AI models.

---

## 🛢️ Step 1: Start the MySQL Database via XAMPP

Our backend needs a place to store user profiles, roadmaps, and posts. We'll use XAMPP to run a local MySQL database.

1. Open the **XAMPP Control Panel** from your Windows Start Menu.
2. You will see a module named **MySQL**. Click the **"Start"** button next to it. (It should turn green).
3. Once running, click the **"Admin"** button next to MySQL. This will open your web browser to `http://localhost/phpmyadmin/`.
4. In phpMyAdmin, look at the left sidebar and click **"New"** to create a database.
5. In the "Database name" box, type exactly `learnup`.
6. Click **"Create"**. 

You're done! Your local MySQL database is now running and waiting for the Django backend to connect to it.

---

## 🧠 Step 2: Start the AI (Ollama)

Our project uses AI to generate questions and learning roadmaps! 

1. Open **PowerShell** or Command Prompt.
2. Type the following command and press Enter:
   ```cmd
   ollama run gemma3
   ```
3. It will download the AI model (this might take a few minutes if it's your first time). Once it says `>>>`, the AI server is running! **Leave this window open** in the background.

---

## ⚙️ Step 3: Start the Backend (Django)

Now we need to start the main Python backend server.

1. Open a new **PowerShell** or Command Prompt window.
2. Navigate to your backend folder:
   ```cmd
   cd d:\Roshen\LearnUp_Backend
   ```
3. Activate the virtual environment (this isolates your Python packages safely):
   ```cmd
   .\venv\Scripts\activate
   ```
   *(You should see `(venv)` appear on the left side of your terminal line).*
4. Install all the required Python packages (we just upgraded these!):
   ```cmd
   pip install -r requirements.txt
   ```
5. **Migrate the Database**: This builds all the tables magically inside that `learnup` database you created in Step 1.
   ```cmd
   python manage.py migrate
   ```
6. **(Optional) Create an Admin user**: If you want a master account to log into the admin panel:
   ```cmd
   python manage.py createsuperuser
   ```
7. **Start the Django Server**:
   ```cmd
   python manage.py runserver
   ```
   You will see an output saying `Starting development server at http://127.0.0.1:8000/`. **Leave this window open!**

---

## 🖥️ Step 4: Start the Frontend (Next.js)

Finally, let's start the visual website that users actually interact with.

1. Open **another new PowerShell** window.
2. Navigate to your frontend folder:
   ```cmd
   cd d:\Roshen\Learn_app_v2
   ```
3. Install the required Node packages (if you haven't already):
   ```cmd
   npm install
   ```
4. Start the frontend developer server:
   ```cmd
   npm run dev
   ```
5. You should see an output indicating the frontend is running on `http://localhost:3000`. 

---

## 🎉 Step 5: Open the App!

You're all done! Open your web browser and go to:
**`http://localhost:3000`**

### Summary of what's running:
1. **XAMPP Control Panel**: Running MySQL (Database).
2. **Terminal 1**: Running `ollama run gemma3` (AI).
3. **Terminal 2**: Running `python manage.py runserver` (Backend APIs on Port 8000).
4. **Terminal 3**: Running `npm run dev` (Frontend UI on Port 3000).

Whenever you want to stop working, you can just close the terminals and click "Stop" on XAMPP!
