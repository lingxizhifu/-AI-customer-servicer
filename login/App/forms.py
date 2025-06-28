from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

class LoginForm(FlaskForm):
    username = StringField('账号', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    captcha = StringField('验证码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    username = StringField('账号', validators=[
        DataRequired(), 
        Length(min=3, max=20, message='账号长度需在3-20个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, max=18, message='密码长度需在6-18个字符之间')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(),
        EqualTo('password', message='两次密码不一致')
    ])
    captcha = StringField('验证码', validators=[DataRequired()])
    submit = SubmitField('注册')