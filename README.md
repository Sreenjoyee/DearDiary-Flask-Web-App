# DearDiary 🧠📔

DearDiary is a personal digital diary web app built with Flask.  
It allows users to write, update, and manage private or public diary entries — their own safe space on the web 💙

---

## 🚀 Features

- 🔐 User Registration & Login
- 🔁 "Remember Me" login support
- 📓 Create, edit, and delete diary posts
- 🔒 Private or Public entries
- 💌 Password reset via email (Brevo Email API)
- 📅 Pagination support for browsing entries
- 🎨 CSS & HTML with a slight usage of boostrap for the UI (only for creating a modal box as confirmation for deleting a post)

---

## 🛠️ Built With

- [Flask] – web framework
- [SQLAlchemy]– ORM for database operations
- [SQLite]– lightweight DB used during development
- [Postgres db] - On Render while deploying
- [Flask-Login] – user session management
- [Flask-WTF] – form validation
- [Flask-Migrate] – database migrations
- [Brevo Transactional Email API] (https://www.brevo.com/) – for sending password reset emails


---
I plan to deploy this on render after some changes
for now it only runs on (only after I activate the run.py):
http://192.168.1.5:5000



