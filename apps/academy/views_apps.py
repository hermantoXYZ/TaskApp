from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import render, get_object_or_404, redirect
# Tambahkan 'View' untuk StartChatView
from django.views.generic import TemplateView, View 
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from .models import (
    ChatRoom, ChatMessage
)
from django.db import transaction

# Database functions (Tambahkan Q dan Max untuk Chat)
from django.db.models import Sum, Q, Max 

import random
"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to kanban/urls.py file for more pages.
"""


class AcademyView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context
    

class KanbanAcademyView(AcademyView):
    template_name = "kanban/app_kanban.html"
    permission_required = [] 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        context.update({
            "title": "Profile",
            "heading": "Edit Profile",
        })
        
        return context
    

class ChatAcademyViews(LoginRequiredMixin, AcademyView):
    template_name = "chat/app_chat.html"

    def _get_user_details(self, user):
        """
        Helper untuk standarisasi data user (Dosen/Mahasiswa/Admin)
        agar avatar dan nama tampil sesuai role.
        """
        avatar_url = "/static/img/avatars/5.png"
        role = "Admin/Staff"
        name = user.first_name or user.username
        email = user.email
        phone = '-'
        
        # Cek apakah Mahasiswa
        if hasattr(user, 'usermhs'):
            role = f"Mahasiswa - {user.username}"
            name = f"{user.first_name}"
            if user.usermhs.photo:
                avatar_url = user.usermhs.photo.url
            phone = user.usermhs.telp
        # Cek apakah Dosen
        elif hasattr(user, 'userdosen'):
            role = "Dosen"
            name = f"{user.first_name}"
            if user.userdosen.photo:
                avatar_url = user.userdosen.photo.url
            phone = user.userdosen.telp
            
        
        return {
            'id': user.id,
            'name': name,
            'role': role,
            'avatar': avatar_url,
            'is_online': True, # Placeholder status online
            'email': email,  # <-- Kirim Email
            'phone': phone   # <-- Kirim No HP
        }

    def get(self, request, *args, **kwargs):
        # 1. Init Context & Layout
        context = self.get_context_data(**kwargs)
        user = request.user
        room_uuid = kwargs.get('room_uuid')

        # ---------------------------------------------------
        # LOGIC 1: SIDEBAR (Room List) - SUDAH SUPPORT GROUP
        # ---------------------------------------------------
        chat_rooms = ChatRoom.objects.filter(
            Q(participants=user) | 
            Q(group__course__coaches__nip=user) # Akses Dosen via Course Group
        ).annotate(
            last_msg_time=Max('messages__created_at')
        ).distinct().order_by('-last_msg_time')

        sidebar_chats = []
        for room in chat_rooms:
            # Default value
            chat_name = "Unknown"
            chat_avatar = "/static/img/avatars/default.png"
            is_group = False

            # [LOGIC BARU] Cek apakah ini Group atau Private
            if getattr(room, 'room_type', 'private') == 'group':
                # Jika Group, ambil nama dari room.name
                chat_name = room.name if room.name else f"Group {room.id}"
                chat_avatar = "https://cdn-icons-png.flaticon.com/512/681/681494.png" # Icon Group
                is_group = True
            else:
                # Jika Private, cari lawan bicara (Partner)
                partner = room.participants.exclude(id=user.id).first()
                if partner:
                    info = self._get_user_details(partner)
                    chat_name = info['name']
                    chat_avatar = info['avatar']
                else:
                    continue # Skip jika private room rusak (tidak ada partner)

            
            last_msg = room.messages.last()
            unread_count = room.messages.filter(is_read=False).exclude(sender=user).count()

            sidebar_chats.append({
                'room_id': room.id,
                'name': chat_name,
                'avatar': chat_avatar,
                'is_group': is_group, # <--- Kirim status grup ke template
                'last_message': last_msg.content if last_msg else "Belum ada pesan",
                'time': last_msg.created_at if last_msg else room.created_at,
                'unread_count': unread_count
            })

        # ---------------------------------------------------
        # LOGIC 2: CONTACTS
        # ---------------------------------------------------
        other_users = User.objects.exclude(id=user.id)[:20]
        contacts = []
        for u in other_users:
            contacts.append(self._get_user_details(u))

        # ---------------------------------------------------
        # LOGIC 3: ACTIVE ROOM (Detail Chat)
        # ---------------------------------------------------
        active_room = None
        messages = []
        active_partner_info = None

        if room_uuid:
            # Gunakan filter Q yang sama agar Dosen tidak kena 404 Not Found
            active_room = get_object_or_404(
                ChatRoom.objects.filter(
                    Q(participants=user) | 
                    Q(group__course__coaches__nip=user)
                ).distinct(),
                id=room_uuid
            )
            
            messages = active_room.messages.select_related('sender').order_by('created_at')
            active_room.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

            if getattr(active_room, 'room_type', 'private') == 'group':
                # Ambil member ASLI (Dosen tidak masuk list ini karena bukan participants)
                group_members = []
                for participant in active_room.participants.all():
                    group_members.append(self._get_user_details(participant))

                active_partner_info = {
                    'name': active_room.name,
                    'role': 'Group Chat',
                    'avatar': "https://cdn-icons-png.flaticon.com/512/681/681494.png",
                    'is_online': False,
                    'email': '-',
                    'phone': '-',
                    'members': group_members 
                }
            else:
                partner = active_room.participants.exclude(id=user.id).first()
                if partner:
                    active_partner_info = self._get_user_details(partner)

        context.update({
            "sidebar_chats": sidebar_chats,
            "contacts": contacts,
            "active_room": active_room,
            "messages": messages,
            "active_partner": active_partner_info,
            "user_avatar": self._get_user_details(user)['avatar']
        })

        return self.render_to_response(context)

    # === UPDATE METHOD POST JUGA (AGAR DOSEN BISA BALAS CHAT JIKA MAU) ===
    def post(self, request, *args, **kwargs):
        room_uuid = kwargs.get('room_uuid')
        if not room_uuid:
            return redirect('chat-index')

        # Izinkan Dosen kirim pesan meski bukan participant
        active_room = get_object_or_404(
            ChatRoom.objects.filter(
                Q(participants=request.user) | 
                Q(group__course__coaches__nip=request.user)
            ).distinct(),
            id=room_uuid
        )
        
        message_content = request.POST.get('message')

        if message_content:
            with transaction.atomic():
                ChatMessage.objects.create(
                    room=active_room,
                    sender=request.user,
                    content=message_content
                )
                active_room.save()

        return redirect('chat-detail', room_uuid=room_uuid)


class StartChatView(LoginRequiredMixin, View):
    def get(self, request, target_user_id, *args, **kwargs):
        current_user = request.user
        target_user = get_object_or_404(User, id=target_user_id)

        existing_rooms = ChatRoom.objects.filter(participants=current_user).filter(participants=target_user)
        
        if existing_rooms.exists():
            # Jika ada, redirect ke room tersebut
            return redirect('chat-detail', room_uuid=existing_rooms.first().id)
        
        # 2. Jika belum, buat Room Baru
        with transaction.atomic():
            new_room = ChatRoom.objects.create() # Default type 'private'
            new_room.participants.add(current_user, target_user)
        
        return redirect('chat-detail', room_uuid=new_room.id)