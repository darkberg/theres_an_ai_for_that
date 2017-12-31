import string, hashlib, hmac, random

from settings import settings

SECRET = settings.DB_SECRET


def hash_str(s):
    x = hmac.new(SECRET.encode('utf-8'), s.encode('utf-8')).hexdigest()
    return x


# Return string with hash and value
def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
    x = h.split('|')[0]
    if make_secure_val(x) == h:
        return x


def make_salt():
    return ''.join(random.choice(string.ascii_lowercase) for x in range(10))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256((name + pw + salt).encode('utf-8')).hexdigest()
    return '%s,%s' % (h, salt)


def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return make_pw_hash(name, pw, salt) == h
