from quart import Blueprint, request, render_template
from objects import glob
import os
import utils
from argon2 import PasswordHasher
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

bp = Blueprint('user_password_recovery', __name__)


@bp.route('/', methods=['GET', 'POST'])
async def password_recovery():
    data = request.args
    if data.get('type') is None and request.method == 'GET':
        return await render_template("request_change.jinja") 
    
    if data.get('type') == 'submit' and request.method == 'POST':
        data = await request.form
        if data.get('email') is None:
            return await render_template("error.jinja", error_message='Email not specified')
        if data.get('username') is None:
            return await render_template("error.jinja", error_message='Username not specified')

        lost_user = glob.players.get(name=data.get('username'))
        if lost_user is None:
            return await render_template("error.jinja", error_message='User not found')
        
        receiver_email = data.get('email')
        if utils.make_md5(receiver_email) != lost_user.email_hash:
            return await render_template("error.jinja", error_message='Invalid email')

        recovery_token = utils.make_md5(f"{secrets.token_urlsafe(16)}{lost_user.id}")
        glob.rec_tokens[recovery_token] = lost_user.id

        email = os.getenv('EMAIL')
        password = os.getenv('EMAIL_PASSWORD')
        smtp_server = glob.config.smtp_server
        smtp_port = glob.config.smtp_port
        
        message = MIMEMultipart()
        message['From'] = email
        message['To'] = receiver_email
        message['Subject'] = 'Password recovery'
        message.attach(MIMEText(f'Hi, you requested a password recovery, recovery link: {glob.config.host}/user/password_recovery?type=change&token={recovery_token}', 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email, password)
            server.sendmail(email, receiver_email, message.as_string())
            server.quit()
        return await render_template("success.jinja", success_message='Recovery email sent')
    
    if data.get('type') == 'change' and request.method == 'GET':
        return await render_template("change_recover.jinja", token=data.get('token')) # change password page
    
    if data.get('type') == 'change' and request.method == 'POST':
        data = await request.form
        if data.get('token') is None:
            return await render_template("error.jinja", error_message='Token not specified')
        if data.get('password') is None:
            return await render_template("error.jinja", error_message='Password not specified')
        if data.get('confirm_password') is None:
            return await render_template("error.jinja", error_message='Confirm password not specified')
        if data.get('password') != data.get('confirm_password'):
            return await render_template("error.jinja", error_message='Passwords do not match')
        if data.get('token') not in glob.rec_tokens:
            return await render_template("error.jinja", error_message='Invalid token')
        
        new_password = data.get('password')
        new_password_hash = utils.make_md5(f"{new_password}taikotaiko")
        ph = PasswordHasher()
        new_password_hash = ph.hash(new_password_hash)
        await glob.db.execute("UPDATE users SET password_hash = $1 WHERE id = $2", [new_password_hash, glob.rec_tokens[data.get('token')]])
        del glob.rec_tokens[data.get('token')]
        return await render_template("success.jinja", success_message='Password changed successfully, you can login now')