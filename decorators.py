from flask import g, flash, redirect, url_for

def login_required(some_var):
    def additional_layer(func):
        def wrap(*args, **kwargs):
            if g.user:
                return func(*args, **kwargs)
            else:
                flash("Please login first")
                return redirect(url_for('login'))
        return wrap
    return additional_layer