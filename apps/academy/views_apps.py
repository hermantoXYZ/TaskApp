import json
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
    ChatRoom, ChatMessage, CalendarEvent,
    StudentPortfolio, CategoryPortfolio, Course,
    UserMhs, KanbanBoard, KanbanTask, KanbanActivity,
)
from django.db.models import Q
from .models import CourseAgenda
from django.utils import timezone
from .forms import StudentPortfolioForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from .decorators_prodi import ProdiOrAdminMixin
from .decorators_dosen import DosenRequiredMixin
from django.db.models import Sum, Q, Max 
import random
from django.db.models import F
from django.utils import timezone

class AcademyView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context
    

import json

class KanbanAcademyView(LoginRequiredMixin, AcademyView):
    template_name = "kanban/app_kanban.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Produktivitas",
            "heading": "Kanban Mahasiswa",
        })
        return context


# ============================================================
# KANBAN API VIEWS
# ============================================================

# Helper serializer task
def _serialize_task(task):
    assignees = []
    for u in task.assignees.select_related('usermhs').all():
        name = u.first_name or u.username
        avatar = '/static/img/avatars/5.png'
        try:
            if u.usermhs.photo:
                avatar = u.usermhs.photo.url
        except Exception:
            pass
        try:
            if u.userdosen.photo:
                avatar = u.userdosen.photo.url
        except Exception:
            pass
        assignees.append({'id': u.id, 'name': name, 'avatar': avatar})
    return {
        'id': str(task.id),
        'title': task.title,
        'due_date': task.due_date.isoformat() if task.due_date else None,
        'label': task.label or '',
        'label_color': task.label_color or 'bg-label-primary',
        'comments': task.comments or '',
        'attachments': task.attachments.url if task.attachments else '',
        'order': task.order,
        'board_id': str(task.board_id),
        'assignees': assignees,
        'creator_name': task.creator.first_name or task.creator.username if task.creator else 'System',
        'created_at': task.created_at.strftime('%d %b %Y %H:%M') if task.created_at else '',
        'updated_at': task.updated_at.strftime('%d %b %Y %H:%M') if getattr(task, 'updated_at', None) else '',
        'activities': [
            {
                'user': a.user.first_name or a.user.username if a.user else 'System',
                'avatar': (a.user.usermhs.photo.url if hasattr(a.user, 'usermhs') and a.user.usermhs.photo else '/static/img/avatars/5.png') if a.user else '/static/img/avatars/5.png',
                'text': a.text,
                'created_at': a.created_at.strftime('%d %b %Y %H:%M')
            } for a in task.activities.select_related('user').all()
        ]
    }


class KanbanBoardListCreateView(LoginRequiredMixin, View):
    """GET: list boards milik user atau board di mana user jadi assignee | POST: buat board baru"""

    def get(self, request, *args, **kwargs):
        # Ambil board yang dimiliki user ATAU di mana user menjadi assignee di salah satu tasknya
        boards = KanbanBoard.objects.filter(
            Q(user=request.user) | Q(tasks__assignees=request.user)
        ).distinct().prefetch_related('tasks', 'tasks__assignees')
        
        data = []
        for board in boards:
            data.append({
                'id': str(board.id),
                'title': board.title,
                'order': board.order,
                'tasks': [_serialize_task(t) for t in board.tasks.all()],
                'is_owner': board.user_id == request.user.id
            })
        return JsonResponse(data, safe=False)

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        title = body.get('title', '').strip()
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)

        order = KanbanBoard.objects.filter(user=request.user).count()
        board = KanbanBoard.objects.create(
            user=request.user,
            title=title,
            order=order,
        )
        return JsonResponse({'id': str(board.id), 'title': board.title, 'order': board.order}, status=201)


class KanbanBoardDetailView(LoginRequiredMixin, View):
    """PUT: rename board | DELETE: hapus board"""

    def _get_board(self, request, board_id):
        board = KanbanBoard.objects.filter(
            Q(id=board_id) & 
            (Q(user=request.user) | Q(tasks__assignees=request.user))
        ).distinct().first()
        if not board:
            from django.http import Http404
            raise Http404("Board not found or no permission")
        return board

    def put(self, request, board_id, *args, **kwargs):
        board = self._get_board(request, board_id)
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        board.title = body.get('title', board.title)
        board.order = body.get('order', board.order)
        board.save()
        return JsonResponse({'id': str(board.id), 'title': board.title, 'order': board.order})

    def delete(self, request, board_id, *args, **kwargs):
        board = self._get_board(request, board_id)
        board.delete()
        return JsonResponse({'message': 'Board deleted'})


class KanbanTaskListCreateView(LoginRequiredMixin, View):
    """POST: buat task baru di board"""

    def post(self, request, board_id, *args, **kwargs):
        board = KanbanBoard.objects.filter(
            Q(id=board_id) & 
            (Q(user=request.user) | Q(tasks__assignees=request.user))
        ).distinct().first()
        if not board:
            from django.http import Http404
            raise Http404("Board not found or no permission")
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        title = body.get('title', '').strip()
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)

        order = board.tasks.count()
        task = KanbanTask.objects.create(
            board=board,
            creator=request.user,
            title=title,
            due_date=body.get('due_date') or None,
            label=body.get('label', '') or '',
            label_color=body.get('label_color', 'bg-label-primary') or 'bg-label-primary',
            comments=body.get('comments', '') or '',
            order=order,
        )
        if 'attachments' in request.FILES:
            task.attachments = request.FILES['attachments']
            task.save()
        # assignees opsional saat create
        assignee_ids = body.get('assignee_ids', [])
        if assignee_ids:
            task.assignees.set(User.objects.filter(id__in=assignee_ids))

        KanbanActivity.objects.create(
            task=task,
            user=request.user,
            text='created this task.'
        )

        return JsonResponse(_serialize_task(task), status=201)


class KanbanTaskDetailView(LoginRequiredMixin, View):
    """POST: update task (pakai POST agar mendukung file form-data) | DELETE: hapus task"""

    def _get_task(self, request, task_id):
        task = get_object_or_404(KanbanTask, id=task_id)
        if task.board.user_id != request.user.id and not task.assignees.filter(id=request.user.id).exists():
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to edit this task.")
        return task

    def post(self, request, task_id, *args, **kwargs):
        task = self._get_task(request, task_id)
        
        # Pindah board jika ada board_id baru
        new_board_id = request.POST.get('board_id')
        if new_board_id and str(task.board.id) != str(new_board_id):
            # Cek hak akses new_board sama seperti _get_board
            new_board = KanbanBoard.objects.filter(
                Q(id=new_board_id) & 
                (Q(user=request.user) | Q(tasks__assignees=request.user))
            ).distinct().first()
            if new_board:
                task.board = new_board

        task.title       = request.POST.get('title', task.title)
        task.due_date    = request.POST.get('due_date') or None
        task.label       = request.POST.get('label', task.label)
        task.label_color = request.POST.get('label_color', task.label_color)
        task.comments    = request.POST.get('comments', task.comments)
        
        if 'order' in request.POST:
            task.order = request.POST.get('order')
            
        if 'attachments' in request.FILES:
            task.attachments = request.FILES['attachments']

        task.save()
        task.refresh_from_db()

        # Update assignees jika dikirim (bisa multiple values)
        assignee_ids = request.POST.getlist('assignee_ids') or request.POST.getlist('assignee_ids[]')
        if 'assignee_ids' in request.POST or 'assignee_ids[]' in request.POST:
            task.assignees.set(User.objects.filter(id__in=assignee_ids))

        KanbanActivity.objects.create(
            task=task,
            user=request.user,
            text='updated this task.'
        )

        return JsonResponse(_serialize_task(task))

    def delete(self, request, task_id, *args, **kwargs):
        task = self._get_task(request, task_id)
        task.delete()
        return JsonResponse({'message': 'Task deleted'})


class KanbanReorderView(LoginRequiredMixin, View):
    """POST: reorder boards atau tasks setelah drag-drop"""

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        reorder_type = body.get('type')  # 'board' atau 'task'

        if reorder_type == 'board':
            # [{id: uuid, order: 0}, ...]
            for item in body.get('items', []):
                board = KanbanBoard.objects.filter(
                    Q(id=item['id']) & 
                    (Q(user=request.user) | Q(tasks__assignees=request.user))
                ).distinct().first()
                if board:
                    board.order = item.get('order', board.order)
                    board.save()
            return JsonResponse({'message': 'Boards reordered'})

        elif reorder_type == 'task':
            # [{id: uuid, board_id: uuid, order: 0}, ...]
            for item in body.get('items', []):
                task = KanbanTask.objects.filter(
                    Q(id=item['id']) & 
                    (Q(board__user=request.user) | Q(assignees=request.user))
                ).distinct().first()

                if task:
                    board_changed = False
                    if 'board_id' in item:
                        new_board = KanbanBoard.objects.filter(
                            Q(id=item['board_id']) & 
                            (Q(user=request.user) | Q(tasks__assignees=request.user))
                        ).distinct().first()

                        if new_board and str(task.board.id) != str(new_board.id):
                            task.board = new_board
                            board_changed = True
                            KanbanActivity.objects.create(
                                task=task,
                                user=request.user,
                                text=f'moved this task to board "{new_board.title}".'
                            )
                    task.order = item.get('order', task.order)
                    task.save()
            return JsonResponse({'message': 'Tasks reordered'})

        return JsonResponse({'error': 'Invalid type'}, status=400)


class KanbanUserSearchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        users_qs = User.objects.exclude(id=request.user.id)
        if q:
            users_qs = users_qs.filter(
                Q(username__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        users_qs = users_qs.select_related('usermhs', 'userdosen')[:20]
        results = []
        for u in users_qs:
            name = u.first_name or u.username
            avatar = '/static/img/avatars/5.png'
            try:
                if u.usermhs.photo: avatar = u.usermhs.photo.url
            except Exception: pass
            try:
                if u.userdosen.photo: avatar = u.userdosen.photo.url
            except Exception: pass
            results.append({'id': u.id, 'text': name, 'avatar': avatar})
        return JsonResponse({'results': results})

class ChatAcademyViews(LoginRequiredMixin, AcademyView):
    template_name = "chat/app_chat.html"

    def _get_user_details(self, user):
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


# ============================================================
# CALENDAR EVENT API VIEWS
# ============================================================

class CalendarEventListCreateView(LoginRequiredMixin, View):
    """GET: ambil semua event milik user | POST: buat event baru"""

    def get(self, request, *args, **kwargs):
        events = CalendarEvent.objects.filter(user=request.user)
        data = []
        for e in events:
            data.append({
                'id': e.pk,
                'title': e.title,
                'start': e.start_date.isoformat() if e.start_date else None,
                'end': e.end_date.isoformat() if e.end_date else None,
                'allDay': e.all_day,
                'url': e.url or '',
                'extendedProps': {
                    'calendar': e.label,
                    'location': e.location or '',
                    'description': e.description or '',
                    'is_readonly': False
                }
            })
            

        course_agendas = CourseAgenda.objects.none()
        if hasattr(request.user, 'usermhs'):
            course_agendas = CourseAgenda.objects.filter(
                course__participants__mahasiswa__nim=request.user,
                agenda_date__isnull=False
            ).distinct()
        elif hasattr(request.user, 'userdosen'):
            course_agendas = CourseAgenda.objects.filter(
                Q(course__coaches__nip=request.user) |
                Q(lecturer__nip=request.user) |
                Q(created_by__nip=request.user),
                agenda_date__isnull=False
            ).distinct()

        from django.utils import timezone
        for a in course_agendas:
            end_date = a.agenda_date + timezone.timedelta(hours=2) if a.agenda_date else None
            desc = a.learning_outcome if a.learning_outcome else f"Tipe: {a.agenda_type}"
            data.append({
                'id': f"agenda_{a.id}",
                'title': f"[{a.course.code}] {a.title}",
                'start': a.agenda_date.isoformat() if a.agenda_date else None,
                'end': end_date.isoformat() if end_date else None,
                'allDay': False,
                'url': '', 
                'extendedProps': {
                    'calendar': 'Campus', 
                    'location': a.location or ('Online' if a.is_online else ''),
                    'description': desc,
                    'agenda_type': a.agenda_type,
                    'is_readonly': True
                }
            })

        return JsonResponse(data, safe=False)

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        event = CalendarEvent.objects.create(
            user=request.user,
            title=body.get('title', 'Untitled'),
            label=body.get('label', 'Business'),
            start_date=body.get('start'),
            end_date=body.get('end') or body.get('start'),
            all_day=body.get('allDay', False),
            url=body.get('url', '') or '',
            location=body.get('location', '') or '',
            description=body.get('description', '') or '',
        )
        return JsonResponse({'id': event.pk, 'message': 'Event created'}, status=201)


class CalendarEventDetailView(LoginRequiredMixin, View):
    """PUT: update | DELETE: hapus event berdasarkan pk"""

    def _get_event(self, request, pk):
        return get_object_or_404(CalendarEvent, pk=pk, user=request.user)

    def put(self, request, pk, *args, **kwargs):
        event = self._get_event(request, pk)
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        event.title       = body.get('title', event.title)
        event.label       = body.get('label', event.label)
        event.start_date  = body.get('start', event.start_date)
        event.end_date    = body.get('end') or body.get('start') or event.end_date
        event.all_day     = body.get('allDay', event.all_day)
        event.url         = body.get('url', '') or ''
        event.location    = body.get('location', '') or ''
        event.description = body.get('description', '') or ''
        event.save()
        return JsonResponse({'id': event.pk, 'message': 'Event updated'})

    def delete(self, request, pk, *args, **kwargs):
        event = self._get_event(request, pk)
        event.delete()
        return JsonResponse({'message': 'Event deleted'})


# ============================================================
# PORTFOLIO MAHASISWA VIEWS
# ============================================================

class StudentPortfolioListView(LoginRequiredMixin, AcademyView):
    template_name = "portfolio/student_portfolio_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        portfolios = StudentPortfolio.objects.filter(user=self.request.user).select_related(
            'category_portfolio', 'course'
        )
        context.update({
            "title": "Portofolio Saya",
            "heading": "Portofolio Mahasiswa",
            "portfolios": portfolios,
        })
        return context


class StudentPortfolioAddView(LoginRequiredMixin, AcademyView):
    """Tambah portfolio baru oleh mahasiswa"""
    template_name = "portfolio/student_portfolio_form.html"

    def _build_form(self, request, data=None, files=None):
        form = StudentPortfolioForm(data=data, files=files)
        # Batasi pilihan course hanya yang diikuti mahasiswa ybs
        form.fields['course'].queryset = Course.objects.filter(
            participants__mahasiswa__nim=request.user, is_active=True
        ).distinct()
        form.fields['course'].required = False
        form.fields['category_portfolio'].required = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Tambah Portofolio",
            "heading": "Tambah Portofolio",
            "form": self._build_form(self.request),
            "is_edit": False,
        })
        return context

    def post(self, request, *args, **kwargs):
        form = self._build_form(request, data=request.POST, files=request.FILES)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.user = request.user
            portfolio.verification_status = 'verified'
            portfolio.verified_at = timezone.now()
            portfolio.save()
            messages.success(request, "Portofolio berhasil ditambahkan dan diverifikasi otomatis!")
            return redirect('portfolio-list')

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class StudentPortfolioEditView(LoginRequiredMixin, AcademyView):
    """Edit portfolio milik mahasiswa sendiri"""
    template_name = "portfolio/student_portfolio_form.html"

    def _get_portfolio(self, request, pk):
        return get_object_or_404(StudentPortfolio, id=pk, user=request.user)

    def _build_form(self, request, instance, data=None, files=None):
        form = StudentPortfolioForm(data=data, files=files, instance=instance)
        form.fields['course'].queryset = Course.objects.filter(
            participants__mahasiswa__nim=request.user, is_active=True
        ).distinct()
        form.fields['course'].required = False
        form.fields['category_portfolio'].required = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        portfolio = self._get_portfolio(self.request, self.kwargs['pk'])
        context.update({
            "title": "Edit Portofolio",
            "heading": "Edit Portofolio",
            "form": self._build_form(self.request, instance=portfolio),
            "portfolio": portfolio,
            "is_edit": True,
        })
        return context

    def post(self, request, *args, **kwargs):
        portfolio = self._get_portfolio(request, kwargs['pk'])
        form = self._build_form(request, instance=portfolio, data=request.POST, files=request.FILES)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.verification_status = 'verified'
            if not portfolio.verified_at:
                from django.utils import timezone
                portfolio.verified_at = timezone.now()
            portfolio.save()
            messages.success(request, "Portofolio berhasil diperbarui dan diverifikasi otomatis!")
            return redirect('portfolio-list')

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class StudentPortfolioDeleteView(LoginRequiredMixin, View):
    """Hapus portfolio milik mahasiswa sendiri (POST only)"""

    def post(self, request, pk, *args, **kwargs):
        portfolio = get_object_or_404(StudentPortfolio, id=pk, user=request.user)
        portfolio.delete()
        messages.success(request, "Portofolio berhasil dihapus.")
        return redirect('portfolio-list')


# ============================================================
# ADMIN PORTFOLIO VIEWS (Prodi / Superuser)
# ============================================================

class AdminPortfolioListView(ProdiOrAdminMixin, AcademyView):
    """Daftar semua portofolio mahasiswa untuk admin/prodi — dengan filter & verifikasi."""
    template_name = "portfolio/admin_portfolio_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q       = self.request.GET.get('q', '').strip()
        vstatus = self.request.GET.get('vstatus', '')   # pending / verified / rejected
        atype   = self.request.GET.get('atype', '')

        qs = StudentPortfolio.objects.select_related(
            'user', 'category_portfolio', 'course', 'verified_by'
        ).order_by('-created_at')

        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__username__icontains=q)
            )
        if vstatus:
            qs = qs.filter(verification_status=vstatus)
        if atype:
            qs = qs.filter(activity_type=atype)

        context.update({
            "title":            "Manajemen Portofolio Mahasiswa",
            "portfolios":       qs,
            "q":                q,
            "sel_vstatus":      vstatus,
            "sel_atype":        atype,
            "activity_choices": StudentPortfolio.ACTIVITY_TYPE_CHOICES,
            "total_pending":    StudentPortfolio.objects.filter(verification_status='pending').count(),
            "total_verified":   StudentPortfolio.objects.filter(verification_status='verified').count(),
            "total_rejected":   StudentPortfolio.objects.filter(verification_status='rejected').count(),
        })
        return context

class AdminPortfolioDeleteView(ProdiOrAdminMixin, View):
    """Hapus portfolio mahasiswa (khusus Admin / Prodi)."""
    def post(self, request, pk, *args, **kwargs):
        portfolio = get_object_or_404(StudentPortfolio, id=pk)
        portfolio.delete()
        messages.success(request, "Portofolio mahasiswa berhasil dihapus.")
        return redirect('admin-portfolio-list')

class DosenPortfolioListView(DosenRequiredMixin, AcademyView):
    template_name = "portfolio/dosen_portfolio_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q       = self.request.GET.get('q', '').strip()
        vstatus = self.request.GET.get('vstatus', '')
        atype   = self.request.GET.get('atype', '')

        # Dosen hanya lihat mahasiswa yang satu group
        user = self.request.user
        qs = StudentPortfolio.objects.select_related(
            'user', 'category_portfolio', 'course', 'verified_by'
        ).order_by('-created_at')

        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__username__icontains=q)
            )
        if vstatus:
            qs = qs.filter(verification_status=vstatus)
        if atype:
            qs = qs.filter(activity_type=atype)

        context.update({
            "title":            "Manajemen Portofolio (Dosen)",
            "portfolios":       qs,
            "q":                q,
            "sel_vstatus":      vstatus,
            "sel_atype":        atype,
            "activity_choices": StudentPortfolio.ACTIVITY_TYPE_CHOICES,
            "total_pending":    qs.filter(verification_status='pending').count(),
            "total_verified":   qs.filter(verification_status='verified').count(),
            "total_rejected":   qs.filter(verification_status='rejected').count(),
        })

        return context

class PortfolioVerifyView(ProdiOrAdminMixin, View):
    def post(self, request, pk, *args, **kwargs):

        portfolio = get_object_or_404(StudentPortfolio, id=pk)
        action    = request.POST.get('action')       

        if action == 'verify':
            portfolio.verification_status = 'verified'
            portfolio.verified_by         = request.user
            portfolio.verified_at         = timezone.now()
            messages.success(request, f"Portofolio '{portfolio.title}' berhasil diverifikasi.")
        elif action == 'reject':
            portfolio.verification_status = 'rejected'
            portfolio.verified_by         = request.user
            portfolio.verified_at         = timezone.now()
            messages.warning(request, f"Portofolio '{portfolio.title}' ditolak.")
        elif action == 'reset':
            portfolio.verification_status = 'pending'
            portfolio.verified_by         = None
            portfolio.verified_at         = None
            messages.info(request, f"Status portofolio '{portfolio.title}' direset ke Pending.")

        portfolio.save()
        return redirect('admin-portfolio-list')


class PublicPortfolioView(View):
    template_name = "portfolio/public_portfolio.html"

    def get(self, request, username, *args, **kwargs):
        owner = get_object_or_404(User, username=username)

        # Hanya tampilkan yang published + verified
        portfolios = StudentPortfolio.objects.filter(
            user=owner,
            status='published',
            verification_status='verified',
        ).select_related('category_portfolio', 'course').order_by('-is_featured', '-created_at')

        # Increment view_count untuk setiap portfolio secara bulk (atomic)
        from django.db.models import F
        portfolios.update(view_count=F('view_count') + 1)

        # Info profil mahasiswa
        try:
            usermhs = owner.usermhs
        except Exception:
            usermhs = None

        # Pisahkan berdasarkan activity_type
        total_all = StudentPortfolio.objects.filter(user=owner, status='published').count()
        projects = portfolios.filter(activity_type='project').order_by('-is_featured', '-created_at')
        
        # Aktivitas lain seperti internship, research, publication, dll (non-project & non-award)
        services = portfolios.exclude(
            activity_type__in=['project', 'competition', 'certificate']
        ).order_by('-created_at')

        # Penghargaan & Sertifikasi
        awards = portfolios.filter(activity_type__in=['competition', 'certificate']).order_by('-created_at')

        context = {
            'owner':      owner,
            'usermhs':    usermhs,
            'projects':   projects,
            'services':   services,
            'awards':     awards,
            'total_all':  total_all,
            'is_own':     request.user.is_authenticated and request.user == owner,
        }
        return render(request, self.template_name, context)

class PublicPortfolioDetailView(View):

    template_name = "portfolio/public_portfolio_detail.html"

    def get(self, request, username, slug, *args, **kwargs):
        owner = get_object_or_404(User, username=username)
        portfolio = get_object_or_404(
            StudentPortfolio, 
            user=owner, 
            slug=slug, 
            status='published', 
            verification_status='verified'
        )

        # Increment view_count untuk item spesifik ini
 
        StudentPortfolio.objects.filter(id=portfolio.id).update(view_count=F('view_count') + 1)
        portfolio.refresh_from_db(fields=['view_count'])

        try:
            usermhs = owner.usermhs
        except Exception:
            usermhs = None

        context = {
            'owner': owner,
            'usermhs': usermhs,
            'portfolio': portfolio,
            'is_own': request.user.is_authenticated and request.user == owner,
        }
        return render(request, self.template_name, context)