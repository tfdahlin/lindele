#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: users/util.py

# Native python imports
import uuid, secrets, binascii, hashlib, hmac
import os, logging, re, datetime, time, json
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from base64 import b64encode, b64decode

# Local file imports
from settings import hash_iterations, hash_algo
from settings import BASE_PATH
from users.models import User, LoginAttempt
from util.util import access_db

# PIP library imports
from sqlalchemy import and_

# Variables and settings
curr_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(curr_dir, 'res', 'templates')

smtp_port = 465

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



def create_full_user(email, username, password):
    """Creates a user in the database given an email, username, and password.

    Arguments:
        email (str): The email to register the account with.
        username (str): The username to register the account with.
        password (str): The password to register the account with.
    """
    with access_db() as db_conn:
        generated_uuid = uuid.uuid1()
        storable_password_hash = create_storable_password(password)
        user = User(email=email, guid=generated_uuid, username=username, password_hash=storable_password_hash)
        db_conn.add(user)
        db_conn.commit()
        return generated_uuid

def fetch_user_by_email(email):
    """Fetch the user entry in the database associated with the provided email.

    Arguments:
        email (str): The email account to lookup.

    Returns:
        result (User or None): The User object associated with the provided email if it exists, else None.
    """
    with access_db() as db_conn:
        result = db_conn.query(User).\
                         filter(User.email==email).\
                         first()
        return result

def fetch_user_by_uuid(input_uuid):
    """Fetch the user entry in the database associated with the provided UUID.
    
    Arguments:
        input_uuid (UUID): The UUID to look up.

    Returns:
        result (User or None): The User object associated with the provided UUID if it exists, else None.
    """
    with access_db() as db_conn:
        result = db_conn.query(User).\
                         filter(User.guid==input_uuid).\
                         first()
        return result

def fetch_user_by_username(username):
    """Fetch the user entry in the database associated with the provided username.
    
    Arguments:
        username (str): The username to look up.

    Returns:
        result (User or None): The User object associated with the provided username if it exists, else None.
    """
    with access_db() as db_conn:
        result = db_conn.query(User).\
                         filter(User.username==username).\
                         first()
        return result

def username_taken(username):
    """Check if a given username already exists in the database.

    Arguments:
        username (str): The username to look up.

    Returns:
        result (bool): Whether or not the user exists in the database.
    """
    with access_db() as db_conn:
        result = db_conn.query(User).\
                         filter(User.username==username).\
                         first()
        if result:
            return True
        return False

def is_logged_in(request):
    """Check to see whether the request includes a session token for an authenticated user.

    Arguments:
        request (request): The request to check for authentication.

    Returns:
        logged_in (bool): True if the request is authenticated, else False.
    """
    logged_in = False
    try:
        session = request.cookies['session']
    except KeyError:
        logger.info("User has no session cookie.")
        return logged_in
    token_details = decode_session_token(session)
    if token_details:
        # Check to make sure it hasn't been invalidated.
        issued_at = datetime.datetime.fromtimestamp(token_details['iat'])
        user = fetch_user_by_uuid(uuid.UUID(token_details['uuid']))
        if not user:
            return logged_in

        if not user.last_invalidated:
            # If no token has ever been invalidated, return true.
            logger.info("User has never had a session token invalidated.")
            logged_in = True
            return logged_in
        else:
            # If a token has been invalidated, check if this one is fresh enough.
            if user.last_invalidated < issued_at:
                logged_in = True
                return logged_in
            else:
                logger.info("Session token is not fresh enough.")
    else:
        logger.info("Session token could not be interpreted.")
    return logged_in

def is_admin(request):
    """Check to see whether the request includes a session token for an authenticated user.

    Arguments:
        request (request): The request to check for authentication.

    Returns:
        result (bool): True if the request is from an authenticated admin user, else False.
    """
    # Default to a false result.
    result = False

    # If the user is not authenticated at all, immediately fail.
    if not is_logged_in(request):
        return result

    # TODO: check if the user is an admin
    # Cookies accessed by request.cookies[cookie_name]
    # Lookup user to see if they're an admin or not.
    return result

def generate_salt(n=32):
    """Generate an n-byte salt, defaulting to 32 bytes.

    The python documentation for the secrets library posits that 32 bytes is sufficient randomness
    for the expected use-case for the secrets module.
    https://docs.python.org/3/library/secrets.html#how-many-bytes-should-tokens-use

    Arguments:
        n (int): Byte length of the generated salt.

    Returns:
        result (bytes): Salt of length n bytes.
    """
    result = secrets.token_bytes(n)
    return result

def check_password(input_password, stored_password):
    """Check the input password against a given stored password hash.

    The secrets.compare_digest() function is used for the comparison, 
    rather than the == comparator, in order to prevent possible timing attacks.

    Arguments:
        input_password (str): The password to process and compare.
        stored_password (str): The hash to compare the input against.

    Returns:
        result (bool): True if the input password matches the hash, False otherwise.
    """

    # Extract the relevant hashing information from the stored hash.
    algo, iters, salt, hashed_pass = extract_hash_info(stored_password)

    # Hash the given input password in the same manner as the stored hash.
    input_hashed_pass = hashlib.pbkdf2_hmac(algo, input_password.encode('utf-8'), salt, iters)

    # Securely compare the hashes.
    result = secrets.compare_digest(hashed_pass, input_hashed_pass)
    return result

def create_storable_password(password):
    """Generate a unique salt, and create a hashed password from that.

    Arguments:
        password (str): The password to hash in a storable format.

    Returns:
        result (str): The hash generated from the input password.
    """

    # Every password gets a unique hash, in order to prevent rainbow table attacks.
    salt = generate_salt()

    # The hashing algorithm requires byte-like objects in order to perform its function,
    #  so we have to encode the input password.
    password_as_bytes = password.encode('utf-8')

    # Use the hashing algorithm and iterations in the config file, as well as the generated
    #  salt to perform the hashing.
    hashed_pass = hashlib.pbkdf2_hmac(hash_algo, password_as_bytes, salt, hash_iterations)

    # The hashed password is a byte-like object, and we need to store the hashing information
    #  along with it to check it later, so we use this to generate a storable version of the hash.
    result = create_storable_hash(hash_algo, hash_iterations, salt, hashed_pass)
    return result

def create_storable_hash(algo, iters, salt, hashed_pass):
    """Generate a storable version of a password hash from its components.

    Each password needs to have a unique salt, and it's possible that the hashing method
    may change in the future. To account for this, we store the salt used, as well as the
    information about how the hash was generated with the hash, in order to repeat the 
    process when we check passwords later.

    Arguments:
        algo (str): The hashing algorithm used by pbkdf2_hmac for generating the hash.
        iters (int): The number of iterations used for generating the hash.
        salt (bytes): Unique salt used in the generation of the hash.
        hashed_pass (bytes): The actual hash that we are storing.

    Returns:
        result (str): A storable string containing information about the hash, and the hash itself.
    """
    algo = algo.encode('utf-8')
    iters = str(iters).encode('utf-8')
    joined_hash = b'$'.join([algo, iters, salt, hashed_pass])
    storable_hash = binascii.hexlify(joined_hash)
    return storable_hash

def extract_hash_info(hash):
    """Extract each of the pieces of the hashed password for processing.

    Because each password has a unique salt, and the hashing method may change, the
    information about how the hash was generated is stored alongside the hash in a 
    single string. In order to repeat the hashing process the same way when passwords
    are checked, we need to extract this information from the stored string.

    Arguments:
        hash (str): The stored string containing the hash, and the information about the hashing process.

    Returns:
        algo (str): The hashing algorithm used.
        iters (int): The number of iterations used when creating the hash.
        salt (bytes): The unique salt used to generate the hash.
        hashed_pass (bytes): The hashed version of the password.
    """
    raw_hash = binascii.unhexlify(hash)
    algo, iters, salt, hashed_pass = raw_hash.split(b'$')
    algo = algo.decode('utf-8')
    iters = int(iters.decode('utf-8'))
    return algo, iters, salt, hashed_pass

def update_username(input_uuid, username):
    """Update the username of a given user.

    Because we will support username changes, this is how that will be accomplished.

    Arguments:
        input_uuid (uuid): UUID associated with the account that should have its username changed.
        username (str): Value to change the account's username to.

    Returns:
        success (bool): True if the username was changed successfully, False otherwise.
    """
    success = False
    if username_taken(username):
        logger.critical(f'Attempted to update username of user with UUID {input_uuid} to {username}, even though it was taken already.')
        return success
    with access_db() as db_conn:
        result = db_conn.query(User).\
                         get(input_uuid)
        if not user:
            logger.critical(f'Attempted to update username for user that doesn\'t exist with UUID {input_uuid}.')
            return success
        result.username = username
        db_conn.commit()
        success = True
        return success
    return success

def update_password(input_uuid, old_password, new_password):
    """Update the password of a given user.

    Arguments:
        input_uuid (uuid): UUID associated with the account that should have its password changed.
        old_password (str): Old password of the user, used for verification of request.
        new_password (str): New password of the user.

    Returns:
        success (bool): True if password change was successful, False otherwise.
    """
    # Fetch the user, fail if it doesn't exist.
    success = False
    user = fetch_user_by_uuid(input_uuid)
    if not user:
        return success

    # Make sure that the old password matches the stored password, fail if not.
    passwords_match = check_password(old_password, user.password_hash)
    if not passwords_match:
        return success

    # Generate a new hash, and store it for the user.
    storable_password_hash = create_storable_password(password)

    with access_db() as db_conn:
        user = db_conn.query(User).\
                         filter(User.guid==input_uuid).\
                         first()
        if not user:
            # This should never happen, unless there is a database race condition for some reason.
            # For safety sake, we make the check anyway.
            return success
        user.password_hash = storable_password_hash
        db_conn.commit()
        success = True
        return success

    return success

def validate_email(email):
    """Checks that the input email address looks like a real email address.

    It's practically impossible to correctly write a script that is always correct,
    so we're using the one from emailregex.com.

    Arguments:
        email (str): Email to validate.

    Returns:
        result (bool): True if the input looks like an email, false otherwise.
    """
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    pattern = re.compile(email_regex)
    match = pattern.match(email)

    if match:
        return True
    return False

def log_login_attempt(email, success, ip):
    """Create a database entry when a user attempts to login.

    Arguments:
        email (str): The email the login is attempted for.
        success (str): Whether the login was successful or not.
        ip (ipaddress): The ip address that the login attempt occurred from.
    """
    with access_db() as db_conn:
        curr_time = datetime.datetime.now()
        login_attempt = LoginAttempt(email=email, success=success, source_ip=ip, attempt_time=curr_time)
        db_conn.add(login_attempt)
        db_conn.commit()

def login_attempts_exceeded(email):
    """Check whether too many failed attempts have been made in the past hour.

    Arguments:
        email (str): The email of the account that failed login attempts are being made for.

    Returns:
        result (bool): True if too many attempts have been made, False otherwise.
    """
    curr_time = datetime.datetime.now()
    hour_ago = curr_time - datetime.timedelta(hours=1)
    with access_db() as db_conn:
        recent_attempts = db_conn.query(LoginAttempt)\
            .filter(\
                and_(
                    LoginAttempt.email==email,
                    LoginAttempt.attempt_time>hour_ago,
                    LoginAttempt.success==False
                ))
        num_attempts = recent_attempts.count()
        if num_attempts > 5:
            return True
    return False

def generate_hmac_digest(msg):
    """Generates an hmac-sha512 digest from the message.

    Arguments:
        msg (bytes): The message to create a digest from.

    Returns:
        digest (bytes): The hmac-sha512 digest of the input message.
    """
    key = fetch_key()
    if not key:
        return None

    # Generate the signature for the payload
    digest = hmac.new(key, msg=msg, digestmod=hashlib.sha512).digest()
    return digest

def create_session_token(user):
    """Generates a session token for a given user.
    
    Arguments:
        user (User): User for whom a token is being generated.

    Returns:
        result (str): String form of the generated jwt token.
    """
    payload = {
        'iat': int(time.time()),
        'uuid': str(user.guid),
    }
    try:
        encoded = jwt.encode(payload, fetch_jwt_key(), algorithm='HS256')
    except Exception as e:
        logger.warn('Exception encountered while encoding payload.')
        logger.warn(e)
        return None
    else:
        return encoded

def decode_session_token(token):
    """Converts a session token into the original data.

    Arguments:
        token (str): The base64 encoded encryted payload.

    Returns:
        payload (dict): The contents of the payload if decoded successfully and signature matches, None otherwise.
    """
    try:
        payload = jwt.decode(token, fetch_jwt_key(), algorithm='HS256')
    except Exception as e:
        logger.warn('Exception encountered while decoding token.')
        logger.warn(e)
    else:
        return payload

def fetch_jwt_key():
    """Fetches a key for use with hmac-sha256.

    If the users/.key file exists, it reads it from the file.
    If the file does not exist, it generates one.

    Returns:
        key (bytes): Key to be used for hmac-sha512.
    """
    # Bits to bytes
    key_size = int(256/8)

    key_file = os.path.join(BASE_PATH, 'users', '.key')
    key = None
    if os.path.exists(key_file):
        try:
            with open(key_file, 'rb') as f:
                key = f.read()
        except:
            logger.critical(f'COULD NOT OPEN FILE TO READ: {key_file}')
            return None
        else:
            return key
    else:
        # Generate a key
        key = secrets.token_bytes(key_size)
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
        except:
            logger.critical(f'COULD NOT OPEN FILE TO WRITE: {key_file}')
            return None
        else:
            return key

def get_user_from_request(request):
    """Fetches the user from the database based on the contents of their session cookie.

    Arguments:
        request (Request): The request from which the user is being extracted.

    Returns:
        user (User): The user who made the request, or None.
    """
    user = None
    try:
        session_cookie = request.cookies['session']
    except KeyError:
        return user
    token_details = decode_session_token(session_cookie)
    if not token_details:
        return user

    user_gid = uuid.UUID(token_details['uuid'])
    user = fetch_user_by_uuid(user_gid)
    return user

def set_user_volume(request):
    """Store a user's preferred volume in the database.

    Arguments:
        requests (Request): The request being made to store a preferred volume.
    """
    # Make sure volume is being passed as a parameter.
    volume = request.data['volume']
    if volume is None:
        logger.info(f'No volume sent in request.')
        return

    # Convert volume string into an integer for storage.
    volume = int(volume)

    # Fetch the UUID of the user to store this for
    user = None
    try:
        session_cookie = request.cookies['session']
    except KeyError:
        logger.info(f'No session cookie in request to set volume.')
        return
    token_details = decode_session_token(session_cookie)
    if not token_details:
        logger.info(f'Could not get session token when trying to set user volume.')
        return
    user_guid = uuid.UUID(token_details['uuid'])

    # Store the volume setting
    with access_db() as db_conn:
        user = db_conn.query(User)\
                        .filter(User.guid==user_guid)\
                        .first()
        if user:
            logger.info(f'Setting user {user.username}\'s volume to {volume}')
            user.volume = volume
            db_conn.commit()
