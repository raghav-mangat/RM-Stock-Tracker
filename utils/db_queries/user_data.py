from models.database import db, User

def add_new_user(first_name, last_name, email, username, password, is_verified=False):
    new_user = User(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_verified=is_verified
    )
    new_user.password = password
    db.session.add(new_user)
    db.session.commit()
    return new_user

def get_user_by_id(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()

def get_user_by_username(username):
    return db.session.execute(db.select(User).where(User.username == username)).scalar()

def get_user_by_email(email):
    return db.session.execute(db.select(User).where(User.email == email)).scalar()

def change_user_password(user, password):
    user.password = password
    db.session.commit()

def verify_user(user):
    user.is_verified = True
    db.session.commit()