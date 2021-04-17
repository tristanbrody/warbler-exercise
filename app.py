import os

from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    session,
    g,
    url_for,
    template_rendered,
)
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from decorators import login_required
from contextlib import contextmanager

from forms import (
    UserAddForm,
    LoginForm,
    MessageForm,
    ProfileEditForm,
    ChangePasswordForm,
)
from models import (
    DirectMessage,
    DirectMessageThread,
    db,
    connect_db,
    User,
    Message,
    Likes,
)
import pdb

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgres:///warbler"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = True
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "it's a secret")
# toolbar = DebugToolbarExtension(app)

connect_db(app)

admin = Admin(app, name="warbler", template_mode="bootstrap3")
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Message, db.session))

##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global"""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


# @app.after_request
# def add_current_url_to_session(response):
#     """Add previous url to session"""
#     session["previous_url"] = request.endpoint
#     return response


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        flash("You have been logged out", "success")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", "danger")
            return render_template("users/signup.html", form=form)

        do_login(user)
        flash("Congrats on signing up!")
        return redirect("/")

    else:
        return render_template("users/signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    # redirect if user is already logged in
    if g.user:
        return redirect(url_for("homepage"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", "danger")

    return render_template("users/login.html", form=form)


@app.route("/logout", endpoint="logout")
@login_required(context="logout")
def logout():
    """Handle logout of user."""

    do_logout()
    return redirect(url_for("homepage"))


##############################################################################
# General user routes:


@app.route("/users")
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get("q")

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template("users/index.html", users=users)


@app.route("/users/<int:user_id>")
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (
        Message.query.filter(Message.user_id == user_id)
        .order_by(Message.timestamp.desc())
        .limit(100)
        .all()
    )

    num_likes = len([like for like in user.likes])

    return render_template(
        "users/show.html", user=user, messages=messages, num_likes=num_likes
    )


@app.route("/users/<int:user_id>/likes")
def show_liked_posts(user_id):
    """Show posts liked by a user"""

    user = User.query.get_or_404(user_id)
    messages = user.likes

    return render_template("users/likes.html", user=user, messages=messages)


@app.route("/users/<int:user_id>/following", endpoint="show_following")
@login_required(context="user_details")
def show_following(user_id):
    """Show list of people this user is following."""

    user = User.query.get_or_404(user_id)
    return render_template("users/following.html", user=user)


@app.route("/users/<int:user_id>/followers", endpoint="users_followers")
@login_required(context="user_details")
def users_followers(user_id):
    """Show list of followers of this user."""

    user = User.query.get_or_404(user_id)
    return render_template("users/followers.html", user=user)


@app.route("/users/follow/<int:follow_id>", methods=["POST"], endpoint="add_follow")
@login_required(context="user_details")
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route(
    "/users/stop-following/<int:follow_id>", methods=["POST"], endpoint="stop_following"
)
@login_required(context="user_details")
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route("/users/profile", methods=["GET", "POST"], endpoint="profile")
@login_required(context="user_details")
def profile():
    """Update profile for current user."""

    form = ProfileEditForm()
    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data) is not False:
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data
            g.user.bio = form.bio.data
            db.session.add(g.user)
            db.session.commit()
            flash("Profile successfully updated")
            return redirect(f"/users/{g.user.id}")
        else:
            flash("Incorrect password")
    return render_template("users/edit.html", form=form)


@app.route("/users/delete", methods=["POST"], endpoint="delete_user")
@login_required(context="user_details")
def delete_user():
    """Delete user."""

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


@app.route("/users/account", endpoint="change_password", methods=["GET", "POST"])
@login_required(context="user_details")
def change_password():
    """View func for logged-in users to change password"""

    form = ChangePasswordForm()

    if form.validate_on_submit():
        change_password_attempt = User.change_password(
            username=g.user.username,
            current_password=form.current_password.data,
            new_password=form.new_password.data,
        )
        if change_password_attempt == g.user:
            db.session.commit()
            flash("Your password has been updated")
        else:
            flash("Current password is incorrect")
    return render_template("users/change_password.html", form=form)


##############################################################################
# Messages routes:


@app.route("/messages/new", methods=["GET", "POST"], endpoint="messages_add")
@login_required(context="user_details")
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template("messages/new.html", form=form)


@app.route("/messages/<int:message_id>", methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template("messages/show.html", message=msg)


@app.route(
    "/messages/<int:message_id>/delete", methods=["POST"], endpoint="messages_destroy"
)
@login_required(context="user_details")
def messages_destroy(message_id):
    """Delete a message."""

    msg = Message.query.get(message_id)

    # make sure logged-in user posted the message they're trying to delete

    if msg.user_id != g.user.id:
        flash("Access unauthorized")
        return redirect("/")

    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.route("/users/toggle_like/<int:message_id>", methods=["GET", "POST"])
def toggle_like(message_id):
    """Like or unlike a message"""

    message = Message.query.get(message_id)

    # redirect if user is trying to like their own post
    if message.user_id == g.user.id:
        flash("You can't like your own message")
        return redirect("/")

    check_for_like = Likes.query.filter_by(
        user_id=g.user.id, message_id=message_id
    ).first()
    if check_for_like is not None:
        db.session.delete(check_for_like)
        db.session.commit()
        return redirect("/")

    new_like = Likes(user_id=g.user.id, message_id=message_id)
    db.session.add(new_like)
    db.session.commit()
    return redirect("/")


@app.route("/users/message", methods=["POST", "GET"])
@login_required(context="user_details")
def send_direct_message():
    """Send a direct message to a specific user"""

    # redirect if not accessed via a post request
    if request.method == "GET":
        return redirect(session["previous_url"])

    send_to_id = request.form.get("send-to")
    send_to = User.query.get(send_to_id)
    form = MessageForm()
    # check if form completed or if we're just rendering template
    if form.validate_on_submit():
        # insert DirectMessageThread and DirectMessage records
        add_direct_message(form.text.data, g.user.id, send_to_id)
        flash("Your message has been sent")
        return redirect(url_for("users_show", user_id=send_to_id))

    # check for existing messages between these two users
    existing_messages = check_for_existing_messages(g.user.id, send_to_id)

    return render_template(
        "/messages/new_direct_message.html",
        send_to=send_to,
        form=form,
        existing_messages=existing_messages,
    )


##############################################################################
# Homepage and error pages


@app.route("/")
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users & of logged-in user
    """

    if g.user:
        messages = (
            Message.query.filter(
                Message.user_id.in_([following.id for following in g.user.following])
                | Message.id.in_([message.id for message in g.user.messages])
            )
            .order_by(Message.timestamp.desc())
            .limit(100)
            .all()
        )
        likes = [like.id for like in g.user.likes]
        return render_template("home.html", messages=messages, likes=likes)

    else:
        return render_template("home-anon.html")


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask


@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers["Cache-Control"] = "public, max-age=0"
    return req


@contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


def add_direct_message(text, sender_id, sent_id):
    """Manage creation of direct messages"""
    direct_message_thread = check_for_existing_thread(sender_id, sent_id)
    if direct_message_thread == None:
        direct_message_thread = DirectMessageThread(user_1=sender_id, user_2=sent_id)
        db.session.add(direct_message_thread)
        db.session.commit()

    new_direct_message = DirectMessage(
        text=text,
        direct_message_thread=direct_message_thread.id,
        sender_id=sender_id,
        sent_id=sent_id,
    )
    db.session.add(new_direct_message)
    db.session.commit()


def check_for_existing_thread(sender_id, sent_id):
    """Check if new direct message should be added to an existing direct message thread"""
    return DirectMessageThread.query.filter(
        (
            (DirectMessageThread.user_1 == sender_id)
            | (DirectMessageThread.user_2 == sender_id)
        ),
        (
            (DirectMessageThread.user_1 == sent_id)
            | (DirectMessageThread.user_2 == sent_id)
        ),
    ).first()


def check_for_existing_messages(sender_id, sent_id):
    """Query DB to check for existing messages between two users, and, if found, return them so view function can pass into template"""
    existing_thread = check_for_existing_thread(sender_id, sent_id)
    if existing_thread is not None:
        return existing_thread.messages
    return None


def render_message_metadata(message):
    if message.sender.id == g.user.id:
        return f"from you to {message.sent_to.username}:"
    if message.sent_to.id == g.user.id:
        return f"from {message.sender.username} to you:"
    return f"from {message.sender.username} to {message.sent_to.username}:"


app.jinja_env.globals.update(render_message_metadata=render_message_metadata)