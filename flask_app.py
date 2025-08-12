import sqlite3
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime

connection = sqlite3.connect("ba2.db", check_same_thread=False)
cursor = connection.cursor()

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"

login_manager = LoginManager(app)
login_manager.login_view = "login"

def get_db_connection():
    conn = sqlite3.connect('ba2.db')
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    user = cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    if user is not None:
        return User(user[0], user[1], user[2])
    return None


@app.route("/add/", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        try:
            cursor.execute(
                "INSERT INTO post (title, content, author_id) VALUES (?, ?, ?)",
                (title, content, current_user.id)
            )
            connection.commit()
            return redirect(url_for("index"))
        except Exception as e:
            print(f"Error creating post: {e}")
            return render_template("add_post.html", error="Failed to create post")
    return render_template("add_post.html")



@app.route("/")
def index():
    cursor.execute("""
        SELECT post.id, post.title, post.content, post.author_id, post.date,
               user.username, user.email,
               COUNT(like.id) AS likes
        FROM post
        JOIN user ON post.author_id = user.id
        LEFT JOIN like ON post.id = like.post_id
        GROUP BY post.id, post.title, post.content, post.author_id, post.date, user.username, user.email
    """)
    result = cursor.fetchall()
    posts = []
    for post in reversed(result):
        post_data = {
            "id": post[0],
            "title": post[1],
            "content": post[2],
            "author_id": post[3],
            "date": post[4],
            "username": post[5],
            "email": post[6],
            "likes": post[7]
        }

        if current_user.is_authenticated:
            cursor.execute("SELECT post_id FROM like WHERE user_id = ?", (current_user.id,))
            likes_result = cursor.fetchall()
            post_data["liked_posts"] = [like[0] for like in likes_result]
        else:
            post_data["liked_posts"] = []

        posts.append(post_data)

    return render_template("blog.html", posts=posts)


@app.route("/post/<int:post_id>")
def post(post_id):
    cursor.execute("""
        SELECT p.*, u.username
        FROM post p
        JOIN user u ON p.author_id = u.id
        WHERE p.id = ?
    """, (post_id,))
    result = cursor.fetchone()

    if not result:
        abort(404)

    post_dict = {
        "id": result[0],
        "title": result[1],
        "content": result[2],
        "author_id": result[3],
        "date": result[4],
        "username": result[5]
    }

    # Проверка лайков для этого поста
    if current_user.is_authenticated:
        cursor.execute("SELECT id FROM like WHERE user_id = ? AND post_id = ?",
                       (current_user.id, post_id))
        post_dict["is_liked"] = cursor.fetchone() is not None
    else:
        post_dict["is_liked"] = False

    return render_template("post.html", post=post_dict)


@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            cursor.execute(
                "INSERT INTO user (username, password_hash, email) VALUES (?, ?, ?)",
                (username, generate_password_hash(password, method="pbkdf2:sha256"), email)
            )
            connection.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", message="Username already exists!")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = cursor.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()
        if user and User(user[0], user[1], user[2]).check_password(password):
            login_user(User(user[0], user[1], user[2]))
            return redirect(url_for("index"))
        else:
            return render_template("login.html", message="Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()
    if post and post[3] == current_user.id:
        cursor.execute("DELETE FROM like WHERE post_id = ?", (post_id,))
        cursor.execute("DELETE FROM post WHERE id = ?", (post_id,))
        connection.commit()
    return redirect(url_for("index"))


@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):
    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()
    if post:
        cursor.execute("SELECT id FROM like WHERE user_id = ? AND post_id = ?",
                       (current_user.id, post_id))
        if cursor.fetchone():
            cursor.execute("DELETE FROM like WHERE user_id = ? AND post_id = ?",
                           (current_user.id, post_id))
        else:
            cursor.execute("INSERT INTO like (user_id, post_id) VALUES (?, ?)",
                           (current_user.id, post_id))
        connection.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()

    if not post or post[3] != current_user.id:
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        cursor.execute(
            "UPDATE post SET title = ?, content = ? WHERE id = ?",
            (title, content, post_id)
        )
        connection.commit()
        return redirect(url_for("post", post_id=post_id))

    post_dict = {
        "id": post[0],
        "title": post[1],
        "content": post[2],
        "author_id": post[3],
        "date": post[4]
    }
    return render_template("edit_post.html", post=post_dict)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db_connection()
    try:
        post = conn.execute('''
            SELECT post.*, user.username
            FROM post JOIN user ON post.author_id = user.id
            WHERE post.id = ?
        ''', (post_id,)).fetchone()

        if not post:
            flash('Post not found', 'error')
            return redirect(url_for('index'))

        comments = conn.execute('''
            SELECT comment.*, user.username
            FROM comment JOIN user ON comment.user_id = user.id
            WHERE comment.post_id = ?
            ORDER BY comment.date DESC
        ''', (post_id,)).fetchall()

        post = dict(post)
        comments = [dict(comment) for comment in comments]

        return render_template('post.html', post=post, comments=comments)
    finally:
        conn.close()


@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('view_post', post_id=post_id))

    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO comment (post_id, user_id, content, date) VALUES (?, ?, ?, ?)',
            (post_id, current_user.id, content, datetime.now())
        )
        conn.commit()
        flash('Comment added successfully', 'success')
    except sqlite3.Error as e:
        flash(f'Error adding comment: {str(e)}', 'error')
    finally:
        conn.close()

    return redirect(url_for('view_post', post_id=post_id))


@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    conn = get_db_connection()
    try:
        comment = conn.execute(
            'SELECT * FROM comment WHERE id = ?',
            (comment_id,)
        ).fetchone()

        if not comment:
            flash('Comment not found', 'error')
        elif comment['user_id'] != current_user.id:
            flash('You can only delete your own comments', 'error')
        else:
            conn.execute(
                'DELETE FROM comment WHERE id = ?',
                (comment_id,)
            )
            conn.commit()
            flash('Comment deleted successfully', 'success')

        return redirect(url_for('view_post', post_id=comment['post_id']))
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)