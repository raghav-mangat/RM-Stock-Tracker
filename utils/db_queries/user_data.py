from models.database import db, User

def add_new_user(name, email, password_hash):
    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash,
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

