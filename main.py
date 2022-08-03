from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from functools import wraps
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from forms import CreatePostForm, RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_only(f):
    @wraps(f)
    def decoreted_function(*args, **kwargs):
        if current_user.password != admin_password:
            return abort(403)
        return f(*args, **kwargs)
    return decoreted_function

##CONFIGURE TABLES


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)




class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


db.create_all()

admin_password = "pbkdf2:sha256:150000$5UuuoQXt$70a0dae3b015d5e20da1aa047295519df408223199e4cd9844fe5c79cfaa9b32"


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user, admin_password=admin_password)


@app.route('/register', methods=["POST", "GET"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():

        if db.session.query(User).filter_by(Email=register_form.email.data).first():

            flash("Email Entered Already Exist. Please Log In")
            return redirect(url_for('login'))
        else:
            new_user = User(Email=register_form.email.data,
                            name=register_form.name.data,
                            password=generate_password_hash(register_form.password.data, method='pbkdf2:sha256', salt_length=8))
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.query(User).filter_by(Email=login_form.email.data).first()
        if user:
            password_i = login_form.password.data
            if check_password_hash(user.password, password_i):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Password Invalid. Please Try Again")
                return redirect(url_for('login'))
        else:
            flash("Email does not exist. Please try again.")
            return redirect(url_for('login'))
    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))



@app.route("/post/<int:post_id>")
@login_required
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    return render_template("post.html", post=requested_post, current_user=current_user, admin_password=admin_password)



@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html")


@app.route("/new-post")
@admin_only
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@admin_only
@login_required
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
@login_required
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
