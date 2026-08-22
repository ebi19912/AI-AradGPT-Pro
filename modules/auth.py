import hashlib
from modules.database import get_user

def check_login(username, password):
    user = get_user(username)
    if user:
        stored_hash = user[1]
        input_hash = hashlib.sha256(password.encode()).hexdigest()

        if stored_hash == input_hash:
            return {
                "username": user[0],
                "balance": user[2],
                "role": user[3]
            }

    return None