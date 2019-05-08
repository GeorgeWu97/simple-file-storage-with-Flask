from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for, g, flash, session
from config import Config
from flask_login import LoginManager, UserMixin
from app import app, db
from app.models import User

# u = User(username='alice')
# db.session.add(u)
# db.session.commit()

# users = User.query.all()
# for u in users:
# 	print(u.id, u.username, u.password_hash)



# 运行实例
if __name__ == '__main__':
    app.run(debug = True)
