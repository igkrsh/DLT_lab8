from peer_socket import PeerSocket
from random import randint
from Crypto.Cipher import AES
import base64
import os
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

BLOCK_SIZE = 32
PADDING = '{'

def _unpad(s):
    return s[:-ord(s[len(s)-1:])]

def _pad(s):
    return s + ((BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE))

def encrypt(key, raw):
    raw = _pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw.encode()))

def decrypt(key, enc):
    enc = base64.b64decode(enc)
    iv = enc[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

if __name__ == "__main__":
    common_key = os.urandom(BLOCK_SIZE)
    different_key = os.urandom(BLOCK_SIZE)
    peers = [
                PeerSocket(('localhost', 6001), common_key),
                PeerSocket(('localhost', 7001), common_key),
                PeerSocket(('localhost', 8001), common_key),
                PeerSocket(('localhost', 9001), different_key),
                PeerSocket(('localhost', 9101), different_key)
            ]

    main_node = randint(0, 4)
    votes = 0

    def greeting_wrapper(key):
        def greeting(sender_addr, message):
            dec_mes = decrypt(key, message)
            if dec_mes == "Primary is Traitor":
                print(str(sender_addr) + ' said ' + dec_mes, " (raw: " , message, " )")
                return "OK"
            else:
                return main_node
        return greeting


    def response(message):
        global votes
        if str(message) == str(main_node):
            votes += 1
        print('Got response ' + str(message))


    event = 'GREETING'

    for x in peers:
        x.on(event, greeting_wrapper(x.key))

    for x in peers:
        peers[main_node].send(x.addr, event, encrypt(peers[main_node].key, "Primary is Traitor"), response)
    if votes == 3:
        print("Primary node is the Impostor!!")
