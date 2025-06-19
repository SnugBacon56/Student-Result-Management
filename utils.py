from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os

# --- Password Hashing ---
def newPassword(raw_password):
    return generate_password_hash(raw_password)

# --- Password Verification ---
def checkPassword(hashed_password, plain_password):
    return check_password_hash(hashed_password, plain_password)

# --- Image Upload Helper ---
def save_image(file, upload_folder):
    # Get file extension (e.g., jpg, png)
    ext = file.filename.rsplit('.', 1)[-1].lower()

    # Generate UUID filename
    filename = f"{uuid.uuid4()}.{ext}"

    # Full path to save
    path = os.path.join(upload_folder, filename)

    # Save image
    file.save(path)

    return filename
