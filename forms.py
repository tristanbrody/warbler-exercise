from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField("text", validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField("Username", validators=[DataRequired()])
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Length(min=6)])
    image_url = StringField("(Optional) Image URL")


class ChangePasswordForm(FlaskForm):

    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[Length(min=6)])
    confirm_new_password = PasswordField(
        "Confirm new password", validators=[Length(min=6)]
    )

    # extend validate function to cross-validate 'confirm password' field
    def validate(self):
        if not super().validate():
            return False
        result = True
        seen = set()
        for field in [self.new_password, self.confirm_new_password]:
            if self.new_password.data != self.confirm_new_password.data:
                field.errors.append("New password and confirmation do not match.")
                result = False
            elif self.new_password.data == self.current_password.data:
                field.errors.append(
                    "New password must be different from current password"
                )
                result = False
            else:
                seen.add(field.data)
        return result


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[Length(min=6)])


class ProfileEditForm(FlaskForm):
    """Form to edit profile"""

    username = StringField("Username")
    email = StringField("E-mail")
    image_url = StringField("Image URL")
    header_image_url = StringField("Header Image URL")
    bio = TextAreaField("Bio")
    password = PasswordField(
        "Password required to confirm changes", validators=[Length(min=6)]
    )
