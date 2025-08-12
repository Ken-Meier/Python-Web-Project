# 📰 Flask Blog App

A lightweight blogging platform built with [Flask](https://flask.palletsprojects.com/), using SQLite for data storage. This app allows users to register, log in, create posts, comment on articles, and interact through likes — all styled with custom CSS and organized using Flask's template engine.

---

## ⚙️ Features

- 🔐 User authentication (register & login)
- 📝 Create, edit, and delete blog posts
- 💬 Comment on posts
- 👍 Like functionality (visual feedback via icons)
- 🎨 Styled with custom CSS
- 🗃️ SQLite database (`ba2.db`) for persistent storage
- 🧩 Modular template structure using Jinja2

---

## 🗂️ Folder Structure
Python-Web-Project/
├── static/
│ ├── like.png
│ ├── like1.png
│ ├── style.css
│ └── style1.css
├── templates/
│ ├── add_post.html
│ ├── blog.html
│ ├── comments.html
│ ├── edit_post.html
│ ├── login.html
│ ├── post.html
│ └── register.html
├── ba2.db
├── flask_app.py
└── README.md

---

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.7+
- `pip` installed

### 📥 Installation

1. **Clone the repository:**

```
git clone https://github.com/Ken-Meier/Python-Web-Project.git
cd Python-Web-Projec
```
2. **Install Flask**
```
pip install flask
```
3. **Run the Flask app**
```
python flask_app.py
```
4. **Visit the app***
```
Go to your browser and open:
http://127.0.0.1:5000
```

## 🧰 Built With

- Flask — Python web framework

- SQLite — Embedded relational database

- Jinja2 — Templating engine

- HTML5, CSS3 — Frontend styling

