from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.timezone import utc
import datetime
import uuid
from django.utils import timezone
from time import strptime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class User(AbstractUser):
    pass
    id = models.BigAutoField(primary_key = True)
    display_name = models.CharField(max_length=191, default="")
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    location = models.CharField(max_length=191, default="")
    deviceId = models.CharField(max_length=191, default="")
    deviceType = models.CharField(max_length=100, default="")
    timezone = models.CharField(max_length=191, default="")
    created_date = models.DateField(auto_now=True, blank=True, null=True)
    onOffNotification = models.IntegerField(default=1)
    role = models.IntegerField(default=0)  # 1 admin 2 user
    image=models.CharField(default="",max_length=191)
    lastUpdated=models.DateTimeField(null=True)
    phone = models.CharField(max_length=15, blank=True)
    is_otp_verified = models.IntegerField(default=0)
    total_friends = models.IntegerField(default=0)
    accept_Chats_from =  models.IntegerField(default=0)
    read_receipt = models.IntegerField(default=0)
    add_phone_contact = models.IntegerField(default=0)
    friend_request = models.IntegerField(default=1)
    new_messages = models.IntegerField(default=1)
    new_comments = models.IntegerField(default=1)
    from_us = models.IntegerField(default=1)
    country_code = models.CharField(max_length=10, blank=True)
    firebase_token = models.TextField(max_length=255, default="")
    active_status = models.IntegerField(default=1)
    

    class Meta:
            verbose_name = ('auth_user')
            verbose_name_plural = ('auth_users')
            db_table = 'auth_user'


class Message(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='sender', related_name='sender', db_index=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='receiver', related_name='receiver', db_index=True)
    timestamp = models.DateTimeField('timestamp', auto_now_add=True, editable=False, db_index=True)
    message = models.TextField('message')
    is_read = models.IntegerField(default=0)
    is_file = models.IntegerField(default=0)
    sender_status = models.IntegerField(default=1)
    receiver_status = models.IntegerField(default=1)
    thumbnail = models.TextField('thumbnail',default="")
    duration = models.CharField(max_length=200,default="")

    def __str__(self):
        return str(self.id)

    def characters(self):
        """
        Toy function to count body characters.
        :return: body's char number
        """
        return len(self.message)

    def notify_ws_clients(self):
        """
        Inform client there is a new message.
        """
        timestamp = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        notification = {
            'type': 'recieve_group_message',
            'message': {"id" : self.id, "timestamp" : timestamp, "message" : self.message,"duration" : self.duration,"thumbnail" : self.thumbnail, "is_read" : self.is_read, "is_file" : self.is_file, "receiver_id" : int(self.receiver_id), "sender_id" : int(self.sender_id), "receiver_status" : self.receiver_status, "sender_status" : self.sender_status, "sender_first_name" : self.sender.first_name, "sender_last_name" : self.sender.last_name, "sender_image" : self.sender.image, "sender_username" : self.sender.username, "receiver_first_name" : self.receiver.first_name, "receiver_last_name" : self.receiver.last_name, "receiver_image" : self.receiver.image, "receiver_username" : self.receiver.username}
        }
        
        
        channel_layer = get_channel_layer()
        
        print(self.sender.id)
        print(self.receiver.id)
        print(notification)
        async_to_sync(channel_layer.group_send)("{}".format(self.sender.id), notification)
        async_to_sync(channel_layer.group_send)("{}".format(self.receiver.id), notification)
        
    def notify_ws_client_for_read(self):
        timestamp = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        notification = {
            'type': 'recieve_group_message',
            'message': {"id" : self.id, "timestamp" : timestamp, "message" : self.message,"duration" : self.duration,"thumbnail" : self.thumbnail, "is_read" : self.is_read, "is_file" : self.is_file, "receiver_id" : int(self.receiver_id), "sender_id" : int(self.sender_id), "receiver_status" : self.receiver_status, "sender_status" : self.sender_status, "sender_first_name" : self.sender.first_name, "sender_last_name" : self.sender.last_name, "sender_image" : self.sender.image, "sender_username" : self.sender.username, "receiver_first_name" : self.receiver.first_name, "receiver_last_name" : self.receiver.last_name, "receiver_image" : self.receiver.image, "receiver_username" : self.receiver.username}
        }
        
        
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)("{}".format(self.sender.id), notification)
        
        

    def save(self, *args, **kwargs):
        """
        Trims white spaces, saves the message and notifies the recipient via WS
        if the message is new.
        """
        new = self.id
        self.message = self.message.strip()  # Trimming whitespaces from the body
        super(Message, self).save(*args, **kwargs)
        if new is None:
            self.notify_ws_clients()

    # Meta
    class Meta:
        verbose_name = 'message'
        verbose_name_plural = 'messages'
        ordering = ('-timestamp',)
