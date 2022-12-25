import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

def encrypt_msg(msg, pub_key_file):
    # Load the public key
    with open(pub_key_file, "rb") as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )

    # Encrypt the message
    encrypted_message = public_key.encrypt(
        msg.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Encode the encrypted message in base64
    encrypted_message = base64.b64encode(encrypted_message)

    return encrypted_message

def decrypt_msg(msg, priv_key_file):
    # Load the private key
    with open(priv_key_file, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )

    # Decrypt the message
    encrypted_message = base64.b64decode(msg)
    message = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return message.decode()

def generate_keys(pub_key_file, priv_key_file):
    # Generate a private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Serialize the private key to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Save the private key to a file
    with open(priv_key_file, "wb") as f:
        f.write(private_key_pem)

    # Extract the public key from the private key
    public_key = private_key.public_key()

    # Serialize the public key to PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Save the public key to a file
    with open(pub_key_file, "wb") as f:
        f.write(public_key_pem)