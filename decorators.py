from flask import g, flash, redirect, url_for

def login_required(context):
    def login_wrapper(func):
        def wrap(*args, **kwargs):
            if g.user:
                return func(*args, **kwargs)
            elif context == 'logout':
                flash("You aren't currently logged in")
                return redirect(url_for('login'))
            elif context == 'user_details':
                flash("Access unauthorized.", "danger")
                return redirect(url_for('login'))
        return wrap
    return login_wrapper