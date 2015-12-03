import json
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from userprofile.models import UserProfile
import sys


def server_auth(original_function):
    """
    server access authentication
    request should include username and access token
    attaches user object to request if successful
    :param original_function:
    :return:
    """
    def wrapper(request):
        username=""
        token=""

        try:
            username = request.GET['username']
            token = request.GET['token']
        except:
            username = request.POST['username']
            token = request.POST['token']

        if not (username and token):
            return error_response("Please provide username and access token for authentication")

        authorized = verify_token(username=username, token=token)

        if authorized:
            user=User.objects.get(username=username)
            request.user=user
            return original_function(request)
        else:
            return error_response("Authentication error")
    return wrapper


def error_response(error, response=None):
    if not response:
        response = dict()

    response['message'] = error
    response['success'] = False

    return HttpResponse(json.dumps(response))


def verify_token(username, token):
    """
    :param username: string
    :param token: string
    :return: true or false
    """

    # check user account existance
    try:
        user=User.objects.get(username=username)
    except User.DoesNotExist:
        return False

    # check token
    try:
        exist_token = Token.objects.get(user=user)
    except Token.DoesNotExist:
        return False

    if token != exist_token.key:
        return False
    return True


@csrf_exempt
def create_account(request):
    """
    :param request: POST method
                        json format '{"username": "username_value",
                                    "email":"email_value" ,
                                    "password": "password_value,}'
    :return:new UserProfile object
    """
    response=dict()
    response['success']=False
    response['message']=""
    try:
        username = request.POST['username']
        password = request.POST['password']
        email= request.POST['email']

        if User.objects.filter(username=username).exists():
            return error_response("username exists")

        if User.objects.filter(email=email).exists():
            return error_response("email exists")

        new_user = User.objects.create_user(username=username,
                                            email=email,
                                            password=password)
        token=Token.objects.create(user=new_user)
        new_user_profile = UserProfile(user = new_user)
        new_user_profile.save()

        response['success']=True
        response['message']="success"
        response['token']=token.key

    except ValueError:
        return error_response("Please provide username, password and email")

    return HttpResponse(json.dumps(response))


@csrf_exempt
def account_login(request):
    """

    :param request: GET method
    :return:
    """
    response=dict()

    username = request.POST['username']
    password = request.POST['password']

    user=authenticate(username=username, password=password)

    response['message']=""
    response['userid']=""
    response['success']=False

    if user is not None:
        if user.is_active:
            response['success']=True
            response['message']="sucess"
            token = Token.objects.get(user=user)
            response['token']=token.key

        else:
            # Return a 'disabled account' error message
            response['message']="disabled account"

    else:
        # Return an 'invalid login' error message.
        response['message']="invalid login"


    return HttpResponse(json.dumps(response))


@csrf_exempt
@server_auth
def account_logout(request):
    """
    log user out, reset access token
    :param request: POST method
    :return:
    """
    response=dict()
    response['success']=False

    user=request.user

    try:
        exist_token = Token.objects.get(user=user)
    except Token.DoesNotExist:
        return error_response("server error")

    exist_token.delete()
    Token.objects.create(user=user)

    response['success']=True
    response['message']="success"

    return HttpResponse(json.dumps(response))


@csrf_exempt
@server_auth
def change_password(request):
    """
    change user account password
    :param request:
    :return:
    """

    new_password=request.POST['new_password']
    old_password=request.POST['old_password']
    username=request.POST['username']
    response=dict()

    user=authenticate(username=username, password=old_password)
    token_user=request.user

    if not user:
        print "auth error"
        return error_response("Invalid username or old password")
    else:
        user.set_password(new_password)
        user.save()
        response['success']=True
        response['message']="success"

        return HttpResponse(json.dumps(response))