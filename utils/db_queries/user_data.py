from models.database import db, User
from werkzeug.security import generate_password_hash

def add_new_user(name, email, password, is_verified=False):
    password_hash = get_password_hash(password)
    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        is_verified=is_verified
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user

def get_user_by_id(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()

def get_user_by_name(name):
    return db.session.execute(db.select(User).where(User.name == name)).scalar()

def get_user_by_email(email):
    return db.session.execute(db.select(User).where(User.email == email)).scalar()

def change_user_password(user, password):
    user.password_hash = get_password_hash(password)
    db.session.commit()

def get_password_hash(password):
    hash_and_salted_password = generate_password_hash(
        password,
        method='pbkdf2:sha256',
        salt_length=8
    )
    return hash_and_salted_password

def verify_user(user):
    user.is_verified = True
    db.session.commit()