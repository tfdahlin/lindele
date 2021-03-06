#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: util/decorators.py

# Native python imports
from functools import wraps
import logging

# Local file imports
from users.util import is_logged_in, is_admin

# PIP library imports
from pycnic.errors import HTTP_400, HTTP_401, HTTP_403

# Variables and settings
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def requires_params(*params):
    """Determine if all necessary parameters are present, return 400 if not.

    Arguments:
        params (list or strings): Required parameters for the request.

    Raises:
        HTTP_400: Raised if at least one parameter is missing.
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not params:
                logger.warn("reqire_params decorator used without any parameters specified.")
                return f(*args, **kwargs)

            missing_params = []

            # Iterate through required params to find if any are missing.
            for param in params:
                # Append all missing params to the list of missing params.
                if param not in args[0].request.data:
                    missing_params.append(param)

            # If there were any missing parameters, return a descriptive error.
            if len(missing_params) > 0:
                logger.info('require_params decorator found missing parameters in request.')
                raise HTTP_400(f"Error, missing parameters: {', '.join(missing_params)}")
            return f(*args, **kwargs)
        return wrapped
    return wrapper

def requires_login():
    """Check that the request is coming from an authenticated user.

    Raises:
        HTTP_401: Raised if the request is not associated with an authenticated user.
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not is_logged_in(args[0].request):
                raise HTTP_401("You must be logged in to do this.")
            return f(*args, **kwargs)
        return wrapped
    return wrapper

def requires_admin():
    """Check that the request is coming from an authenticated admin.

    Raises:
        HTTP_401: Raised if the user is not logged in.
        HTTP_403: Raised if the user is not an admin.
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not is_logged_in(args[0].request):
                raise HTTP_401("You must be logged in to do this.")
            if not is_admin(args[0].request):
                raise HTTP_403("You must be an admin to do this.")
            return f(*args, **kwargs)
        return wrapped
    return wrapper