from __future__ import unicode_literals
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
import json
import string
import random, pytz
from django.utils import timezone
import traceback
from apis.models import *
from django.views.decorators.csrf import csrf_exempt
# from appadmin.forms import AddSuperAdminForm
from django.contrib.auth import authenticate,login
from django.db import transaction
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token
from django.db import connection
from apis.serializers import *
from random import randint

import uuid 
import time
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from multiprocessing import Lock

from threading import Thread
from django.contrib.auth.hashers import make_password

import calendar
from django.core.files.storage import default_storage
from django.views.decorators.cache import never_cache
from django.template.loader import get_template 

# import boto3
# from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from django.core.serializers.json import DjangoJSONEncoder

from django.http.response import JsonResponse, HttpResponse
import pdb;
from authy.api import AuthyApiClient
from twilio.rest import Client
import os
import ffmpy


from django.core.paginator import Paginator
from decimal import Decimal
from django.shortcuts import render
from rest_framework.decorators import api_view,renderer_classes
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.files.storage import FileSystemStorage

import decimal 
import math 
import arrow
import random

from pyfcm import FCMNotification



#===========================
#Sign Up and send otp
#===========================

@csrf_exempt
@api_view(['POST'])
def SignUp(request):
    try:
        with transaction.atomic():
            phonee = User.objects.filter(phone = request.data['phone']).exists()
            user = User.objects.filter(username = request.data['username']).exists()
            if phonee or user:
                if phonee:
                    errorr = errorPhoneExist
                else:
                    errorr = errorUsernameExist
                return Response({"message" : errorr, "status" : "0"}, status=status.HTTP_406_NOT_ACCEPTABLE)  
            else:
                firebase_token = request.data.get('firebase_token') if request.data.get('firebase_token') else ""
                
                authuser = User.objects.create(display_name = request.data['display_name'],
                                        phone = request.data['phone'],
                                        username = request.data['username'],
                                        password = make_password(request.data['password']),
                                        deviceId = request.data['deviceId'],
                                        deviceType = request.data['deviceType'],
                                        country_code = request.data['country_code'],
                                        firebase_token = firebase_token ,
                                        role=2
                                        )
                g = Group.objects.get(name='User')
                g.user_set.add(authuser)
                token = Token.objects.create(user=authuser)
                if authuser:
                    userobj = User.objects.get(id=authuser.id)
                    userDetail = {
                                    'token': token.key,
                                    'id': authuser.id,
                                    'display_name': authuser.display_name,
                                    'username': authuser.username,
                                    'password': authuser.password,
                                    'deviceId':authuser.deviceId,
                                    'deviceType':authuser.deviceType,
                                    'phone':authuser.phone,
                                    'created_date':authuser.created_date,
                                    'onOffNotification':authuser.onOffNotification,
                                    'image':authuser.image,
                                    'is_otp_verified':authuser.is_otp_verified,
                                    'total_friends':authuser.total_friends,
                                    'accept_Chats_from':authuser.accept_Chats_from,
                                    'read_receipt':authuser.read_receipt,
                                    'add_phone_contact':authuser.add_phone_contact,
                                    'friend_request':authuser.friend_request,
                                    'new_messages':authuser.new_messages,
                                    'new_comments':authuser.new_comments,
                                    'from_us':authuser.from_us,
                                    'country_code':authuser.country_code
                                    }
                    return Response({"message" : "success","dataModel":userDetail, "status" : "1"}, status=status.HTTP_200_OK)
    except Exception:
        print(traceback.format_exc())
        return Response({"message" : "error", "status" : "0"}, status=status.HTTP_406_NOT_ACCEPTABLE)


#====================================
# Api for send message
#====================================

@api_view(['POST'])
def sendMessage(request):
    try:
        with transaction.atomic():
            try:
        
                API_key = request.META.get('HTTP_AUTHORIZATION')
                token1 = Token.objects.get(key=API_key)
                user = token1.user
                checkGroup = user.groups.filter(name='User').exists()
                if checkGroup == False:
                    return Response({"message" : errorMessageUnauthorised, "status" : "0"}, status=status.HTTP_401_UNAUTHORIZED)
            except:
                return Response({"message": errorMessageUnauthorised, "status": "0"},status=status.HTTP_401_UNAUTHORIZED)
            
            receiver_id = request.data['receiver_id']
            is_file = request.data['is_file']
            rec = User.objects.get(id = request.data['receiver_id'])
            userblock = BlockUser.objects.filter(user_id = user.id, blocked_user =request.data['receiver_id'])
            userblockby = BlockUser.objects.filter(user_id = request.data['receiver_id'], blocked_user =user.id)
            if userblock or userblockby:
                return Response({"message" : "user is blocked", "status" : "0"}, status=status.HTTP_406_NOT_ACCEPTABLE)
                 
            else:
                tempp=[]
                friends_list = UserFriend.objects.filter(friend_id = request.data['receiver_id'],friendstatus = 1,user_id=user.id)|UserFriend.objects.filter(friend_id = user.id,friendstatus=1,user_id=request.data['receiver_id'])
                print("<+===========================>",friends_list,"======================>")
                print("=====================",rec.accept_Chats_from)
                if (friends_list and rec.accept_Chats_from ==1) or (friends_list and rec.accept_Chats_from ==0) or ( (not friends_list and rec.accept_Chats_from ==0) and (user.accept_Chats_from==0)):

                    # tempS = datetime.datetime.utcnow().replace(tzinfo=utc)
                    if int(is_file) == 1 or int(is_file) == 2 or int(is_file) == 3:
                        file = request.FILES.get('file')
                        
                        fileUrl = ""
                        if file is not None:
                            
                            fs = FileSystemStorage()
                            filename = fs.save("chatfiles/"+str(user.id)+'_'+str(int(round(time.time() * 1000)))+"/"+file.name, file)
                            uploaded_file_url = fs.url(filename)
                            message = uploaded_file_url
                            is_file = int(is_file)
                            if int(is_file) == 3:
                                file = request.FILES.get('thumbnail')
                                fileUrl = ""
                                if file is not None:
                                    fs = FileSystemStorage()
                                    filename = fs.save("chatfiles/"+str(user.id)+'_'+str(int(round(time.time() * 1000)))+"/"+file.name, file)
                                    uploadedthumb_file_url = fs.url(filename)
                                    message = uploaded_file_url
                            else:
                                uploadedthumb_file_url = ""
                            if int(is_file) == 3:
                                file = request.FILES.get('file')
                                print(file)
                                # video_file_path = settings.MEDIA_ROOT + '/'
                                # print(video_file_path)
                                # video = ffmpeg_streaming.input('/home/netset/Downloads/20202410092449.mp4')
                                # print(video)
                                if (file.name.endswith(".mp4")): #or .avi, .mpeg, whatever.
                                # ffmpeg -i $video -vcodec h264 -acodec mp2
                                    print(os.system("ffmpeg -i {0} -f file -vcodec h264 -acodec mp2".format("/home/netset/Downloads/20202410092449.mp4")))
                            if int(is_file) == 2:
                                dura = request.data['duration']
                            else:
                                dura = ""
                    else:
                        message = request.data['message']
                        is_file = 0
                        uploadedthumb_file_url = ""
                        dura = ""
                    
                    tempp=[]
                    
                    
                    message = Message(sender_id=user.id, receiver_id=receiver_id, message=message, is_file=is_file,thumbnail =uploadedthumb_file_url,duration=dura)
                    message.save()
                    if is_file == 0:
                        msggnoti = request.data['message']
                    elif is_file ==1:
                        msggnoti = "Image"
                    elif is_file ==2:
                        msggnoti = "Audio"
                    elif is_file ==3:
                        msggnoti = "Video"

                    print(message,"kkkkkkkk")
                    message_detail = MessageSerializer(message)
                    msgg = message_detail.data
                    msgg['sender_id']=int(msgg['sender'])
                    msgg['receiver_id']=int(msgg['receiver'])
                    print(rec.onOffNotification)
                    notiuser = UserNotification.objects.filter(user_id=rec.id,otheruser_id = user.id,status = 1)
                    if notiuser:
                        print("notification nhi gyi =================================")
                        return Response({"message" : "Message sent successfully", "status" : "1","dataArray":msgg}, status=status.HTTP_200_OK)
                        
                    else:
                        if rec.onOffNotification == 1 and rec.new_messages == 1:
                            print("jjjjnotification gyi")
                            notify = SendChatNotification(user.id, str(user.username), str(user.image), rec.id, str(rec.username) , str(rec.image), msggnoti, str(user.username) + " has sent you a message")
                        
                        return Response({"message" : "Message sent successfully", "status" : "1","dataArray":msgg}, status=status.HTTP_200_OK) 
                else:
                    return Response({"message" : "Add user as a friend", "status" : "0"}, status=status.HTTP_406_NOT_ACCEPTABLE)
                             
    except Exception as e:
        print(traceback.format_exc())
        return Response({"message" : e, "status" : "0"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
