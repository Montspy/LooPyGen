from pprint import pprint
from jose import jwe
import json
import os


def encrypt_config(config, secret):
    # Derive key
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    key = kdf.derive(secret)

    # Encrypt
    cypher = jwe.encrypt(json.dumps(config), key, algorithm="dir", encryption="A256GCM")
    enc_config = {
        "cypher": cypher.decode("utf-8"),
        "salt": "0x" + salt.hex()
    }
    return enc_config

def decrypt_config(enc_config, secret):
    # Derive key
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt = bytes.fromhex(enc_config['salt'].replace("0x", ""))
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    key = kdf.derive(secret)

    cypher = enc_config['cypher'].encode('utf-8')
    config = json.loads(jwe.decrypt(cypher, key))
    return config

def main():
    secret = b"Passphrase132,.<>/'\""

    with open('test-config.json') as f:
        config = json.load(f)
    pprint(config, indent=2)

    enc_config = encrypt_config(config, secret)
    pprint(enc_config, indent=2)
    with open('enc-config.json', 'w') as f:
        json.dump(enc_config, f)

    dec_config = decrypt_config(enc_config, secret)
    pprint(dec_config, indent=2)
    with open('dec-config.json', 'w') as f:
        json.dump(dec_config, f)

    print(json.dumps(config) == json.dumps(dec_config))

if __name__ == "__main__":
    main()

