from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from collections import defaultdict
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

from .models import (
    Course, CourseDiscussion, CourseDiscussionReply, CourseDiscussionLike,
    CourseParticipant, CourseAgenda, CourseMaterial, CourseAssignment,
    CourseAnnouncement, UserDosen, UserMhs,
)


# ─────────────────────────────────────────────
# Helper – akses course
# ─────────────────────────────────────────────

def _get_course_access(request, course_uuid):
    """
    Returns (course, is_dosen, is_student).
    Raises PermissionError jika user tidak punya akses ke course.
    """
    course = get_object_or_404(Course.objects.prefetch_related('coaches'), uuid=course_uuid)
    user = request.user

    is_dosen = UserDosen.objects.filter(nip=user).exists()
    is_student = False

    if not is_dosen:
        is_student = CourseParticipant.objects.filter(
            course=course, mahasiswa__nim=user
        ).exists()

    if not is_dosen and not is_student and not user.is_superuser:
        raise PermissionError("Anda tidak memiliki akses ke course ini.")

    return course, is_dosen, is_student


TYPE_ICONS = {
    'general':    'ri-discuss-line',
    'material':   'ri-book-open-line',
    'assignment': 'ri-task-line',
    'question':   'ri-question-answer-line',
}

TYPE_COLORS = {
    'general':    'secondary',
    'material':   'info',
    'assignment': 'warning',
    'question':   'primary',
}

FEED_CONFIG = {
    'agenda': {
        'icon':        'ri-calendar-event-line',
        'color':       'primary',
        'action_text': 'membuat agenda pada',
        'disc_type':   'general',
    },
    'material': {
        'icon':        'ri-book-open-line',
        'color':       'success',
        'action_text': 'menambahkan materi pada',
        'disc_type':   'material',
    },
    'assignment': {
        'icon':        'ri-file-list-3-line',
        'color':       'warning',
        'action_text': 'menambahkan tugas pada',
        'disc_type':   'assignment',
    },
    'discussion': {
        'icon':        'ri-discuss-line',
        'color':       'info',
        'action_text': 'membuka diskusi di',
        'disc_type':   'general',
    },
    'announcement': {
        'icon':        'ri-megaphone-line',
        'color':       'danger',
        'action_text': 'memposting pengumuman di',
        'disc_type':   'general',
    },
}


# ─────────────────────────────────────────────
# Helper – auto-linked discussion
# ─────────────────────────────────────────────

def _purge_auto_disc_if_disabled(course, item_type, obj):
    """
    Hapus thread otomatis yang terikat ke agenda/materi/tugas/pengumuman bila diskusi
    dinonaktifkan, agar tidak tertinggal baris di admin / DB.
    """
    if item_type == 'agenda':
        CourseDiscussion.objects.filter(
            course=course,
            agenda=obj,
            material__isnull=True,
            assignment__isnull=True,
        ).delete()
    elif item_type == 'material':
        CourseDiscussion.objects.filter(course=course, material=obj).delete()
    elif item_type == 'assignment':
        CourseDiscussion.objects.filter(course=course, assignment=obj).delete()
    elif item_type == 'announcement':
        CourseDiscussion.objects.filter(course=course, announcement=obj).delete()


def _feed_linked_discussion(course, item_type, obj):
    """
    Untuk halaman feed (GET): ambil thread yang sudah ada di DB.
    Jika allow_discussion=True tapi thread belum ada, buat otomatis
    (misalnya ketika checkbox diaktifkan lewat Django Admin atau cara lain
    tanpa melalui form simpan dosen yang memanggil _sync_linked_discussion_on_content_save).
    """
    if not getattr(obj, 'allow_discussion', False):
        return None

    # Tentukan fallback user untuk kolom created_by (wajib NOT NULL)
    def _fallback_user():
        """Ambil coach pertama course, atau superuser pertama sebagai fallback."""
        coach = course.coaches.select_related('nip').order_by('nip_id').first()
        if coach:
            return coach.nip
        from django.contrib.auth.models import User
        return User.objects.filter(is_superuser=True).first()

    if item_type == 'agenda':
        disc = CourseDiscussion.objects.filter(
            course=course, agenda=obj,
            material__isnull=True, assignment__isnull=True,
        ).first()
        if not disc:
            fallback = _fallback_user()
            if fallback:
                disc = CourseDiscussion.objects.create(
                    course=course,
                    discussion_type='general',
                    agenda=obj,
                    title=obj.title,
                    created_by=fallback,
                )
        return disc

    if item_type == 'material':
        disc = CourseDiscussion.objects.filter(course=course, material=obj).first()
        if not disc:
            fallback = _fallback_user()
            if fallback:
                disc = CourseDiscussion.objects.create(
                    course=course,
                    discussion_type='material',
                    agenda=obj.agenda if obj.agenda else None,
                    material=obj,
                    title=obj.title,
                    created_by=fallback,
                )
        return disc

    if item_type == 'assignment':
        disc = CourseDiscussion.objects.filter(course=course, assignment=obj).first()
        if not disc:
            fallback = _fallback_user()
            if fallback:
                disc = CourseDiscussion.objects.create(
                    course=course,
                    discussion_type='assignment',
                    agenda=obj.agenda if obj.agenda else None,
                    assignment=obj,
                    title=obj.title,
                    created_by=fallback,
                )
        return disc

    if item_type == 'announcement':
        disc = CourseDiscussion.objects.filter(course=course, announcement=obj).first()
        if not disc:
            fallback = _fallback_user()
            if fallback:
                disc = CourseDiscussion.objects.create(
                    course=course,
                    discussion_type='general',
                    announcement=obj,
                    title=obj.title,
                    created_by=fallback,
                )
        return disc

    return None


def _sync_linked_discussion_on_content_save(course, item_type, obj, fallback_user, agenda_obj=None):
    """
    Dipanggil setelah agenda/materi/tugas disimpan lewat form dosen.
    allow_discussion True  -> buat thread terikat jika belum ada.
    allow_discussion False -> hapus thread terikat bila ada.
    """
    if not getattr(obj, 'allow_discussion', False):
        _purge_auto_disc_if_disabled(course, item_type, obj)
        return
    if item_type == 'agenda':
        disc = CourseDiscussion.objects.filter(
            course=course, agenda=obj,
            material__isnull=True, assignment__isnull=True,
        ).first()
        if not disc:
            CourseDiscussion.objects.create(
                course=course,
                discussion_type='general',
                agenda=obj,
                title=obj.title,
                created_by=fallback_user,
            )
    elif item_type == 'material':
        disc = CourseDiscussion.objects.filter(course=course, material=obj).first()
        if not disc:
            CourseDiscussion.objects.create(
                course=course,
                discussion_type='material',
                agenda=agenda_obj,
                material=obj,
                title=obj.title,
                created_by=fallback_user,
            )
    elif item_type == 'assignment':
        disc = CourseDiscussion.objects.filter(course=course, assignment=obj).first()
        if not disc:
            CourseDiscussion.objects.create(
                course=course,
                discussion_type='assignment',
                agenda=agenda_obj,
                assignment=obj,
                title=obj.title,
                created_by=fallback_user,
            )
    elif item_type == 'announcement':
        disc = CourseDiscussion.objects.filter(course=course, announcement=obj).first()
        if not disc:
            CourseDiscussion.objects.create(
                course=course,
                discussion_type='general',
                announcement=obj,
                title=obj.title,
                created_by=fallback_user,
            )


# ─────────────────────────────────────────────
# Helper – build unified activity feed
# ─────────────────────────────────────────────

def _build_activity_feed(request, course, is_dosen, filter_type=''):
    """
    Build a unified activity feed from agendas, published materials,
    published assignments, and manually-created student discussions.
    Returns a list of feed-item dicts sorted by created_at descending.
    """
    user = request.user
    feed_items = []

    # Dosen tampil di kartu agenda/materi/tugas: pembuat agenda, atau pengampu course.
    fallback_coach = (
        course.coaches.select_related('nip').order_by('nip_id').first()
    )

    show_agenda = not filter_type or filter_type == 'agenda' or filter_type == 'discussion'
    show_material = not filter_type or filter_type == 'material' or filter_type == 'discussion'
    show_assignment = not filter_type or filter_type == 'assignment' or filter_type == 'discussion'
    show_manual_discussion = not filter_type or filter_type == 'discussion'
    show_announcement = not filter_type or filter_type == 'announcement'

    # ── 1. Agendas ──────────────────────────────────────────────────
    if show_agenda:
        agendas = (
            CourseAgenda.objects
            .filter(course=course)
            .select_related('created_by__nip')
            .order_by('-created_at')
        )
        for agenda in agendas:
            creator_dosen = agenda.created_by or fallback_coach
            creator_user  = creator_dosen.nip if creator_dosen else user
            disc = _feed_linked_discussion(course, 'agenda', agenda)
            cfg  = FEED_CONFIG['agenda']

            # photo
            photo_url = None
            if creator_dosen and creator_dosen.photo:
                try:
                    photo_url = creator_dosen.photo.url
                except Exception:
                    pass

            # Ambil lampiran media (AgendaMediaItem) untuk ditampilkan di feed
            media_items = []
            for item in agenda.media_items.select_related('media_file').all():
                mf = item.media_file
                media_items.append({
                    'name': mf.name if mf else '',
                    'file_type':  mf.file_type if mf else '',
                    'file_url':   mf.file.url if mf and mf.file else None,
                    'video_url':  mf.video_url or None if mf else None,
                    'size':       mf.file_size_display if mf else None,
                })

            feed_items.append({
                'item_type':        'agenda',
                'source':           agenda,
                'disc':             disc,
                'created_by_user':  creator_user,
                'photo_url':        photo_url,
                'created_at':       agenda.created_at,
                'action_text':      cfg['action_text'],
                'course_name':      course.name,
                'session_name':     agenda.title,
                'title':            agenda.title,
                'description': getattr(agenda, 'description', None) or agenda.title,
                'icon':             cfg['icon'],
                'color':            cfg['color'],
                'attachment_url':   None,
                'attachment_name':  None,
                'attachment_icon':  '',
                'is_published':     True,
                'extra': {
                    'agenda_date': agenda.agenda_date,
                    'location':    agenda.location,
                    'is_online':   agenda.is_online,
                    'meeting_url': agenda.meeting_url,
                    'agenda_type': agenda.agenda_type,
                    'media_items': media_items,
                },
            })

    # ── 2. Materials ─────────────────────────────────────────────────
    if show_material:
        mat_qs = CourseMaterial.objects.filter(agenda__course=course)
        if not is_dosen:
            mat_qs = mat_qs.filter(is_published=True)
        materials = mat_qs.select_related('agenda__created_by__nip').order_by('-created_at')

        for mat in materials:
            creator_dosen = (
                (mat.agenda.created_by if mat.agenda else None) or fallback_coach
            )
            creator_user  = creator_dosen.nip if creator_dosen else user
            disc = _feed_linked_discussion(course, 'material', mat)
            cfg  = FEED_CONFIG['material']

            photo_url = None
            if creator_dosen and creator_dosen.photo:
                try:
                    photo_url = creator_dosen.photo.url
                except Exception:
                    pass

            feed_items.append({
                'item_type':        'material',
                'source':           mat,
                'disc':             disc,
                'created_by_user':  creator_user,
                'photo_url':        photo_url,
                'created_at':       mat.created_at,
                'action_text':      cfg['action_text'],
                'course_name':      course.name,
                'session_name':     mat.agenda.title if mat.agenda else '',
                'title':            mat.title,
                'description':      mat.text_content[:200] if mat.text_content else '',
                'icon':             cfg['icon'],
                'color':            cfg['color'],
                'attachment_url':   None,
                'attachment_name':  None,
                'attachment_icon':  'ri-article-line',
                'attachment_color': '#696cff',
                'is_published':     mat.is_published,
                'extra': {
                    'mat_id':        mat.id,
                    'course_uuid':   str(course.uuid),
                },
            })

    # ── 3. Assignments ───────────────────────────────────────────────
    if show_assignment:
        asgn_qs = CourseAssignment.objects.filter(agenda__course=course)
        if not is_dosen:
            asgn_qs = asgn_qs.filter(is_published=True)
        assignments = asgn_qs.select_related('agenda__created_by__nip').order_by('-created_at')

        for asgn in assignments:
            creator_dosen = (
                (asgn.agenda.created_by if asgn.agenda else None) or fallback_coach
            )
            creator_user  = creator_dosen.nip if creator_dosen else user
            disc = _feed_linked_discussion(course, 'assignment', asgn)
            cfg  = FEED_CONFIG['assignment']

            photo_url = None
            if creator_dosen and creator_dosen.photo:
                try:
                    photo_url = creator_dosen.photo.url
                except Exception:
                    pass

            att_url  = asgn.file_instruction.url  if asgn.file_instruction  else None
            att_name = asgn.file_instruction.name.split('/')[-1] if asgn.file_instruction else None

            feed_items.append({
                'item_type':        'assignment',
                'source':           asgn,
                'disc':             disc,
                'created_by_user':  creator_user,
                'photo_url':        photo_url,
                'created_at':       asgn.created_at,
                'action_text':      cfg['action_text'],
                'course_name':      course.name,
                'session_name':     asgn.agenda.title if asgn.agenda else '',
                'title':            asgn.title,
                'description':      (asgn.description or '')[:200],
                'icon':             cfg['icon'],
                'color':            cfg['color'],
                'attachment_url':   att_url,
                'attachment_name':  att_name,
                'attachment_icon':  'ri-file-list-3-line',
                'attachment_color': '#e67e22',
                'is_published':     asgn.is_published,
                'extra': {
                    'due_date':        asgn.due_date,
                    'max_score':       asgn.max_score,
                    'assignment_type': asgn.assignment_type,
                    'allow_late':      asgn.allow_late_submission,
                    'asgn_id':         asgn.id,
                    'course_uuid':     str(course.uuid),
                },
            })

    # ── 4. Announcements (CourseAnnouncement) ──────────────────────
    if show_announcement:
        announcements = (
            CourseAnnouncement.objects
            .filter(course=course)
            .select_related('created_by__nip')
            .order_by('-is_pinned', '-created_at')
        )
        PRIORITY_COLORS = {
            'low':    '#8592a3',
            'normal': '#696cff',
            'high':   '#ff9f43',
            'urgent': '#ea5455',
        }
        for ann in announcements:
            creator_dosen = ann.created_by or fallback_coach
            creator_user  = creator_dosen.nip if creator_dosen else user
            cfg = FEED_CONFIG['announcement']
            disc = _feed_linked_discussion(course, 'announcement', ann)

            photo_url = None
            if creator_dosen and creator_dosen.photo:
                try:
                    photo_url = creator_dosen.photo.url
                except Exception:
                    pass

            feed_items.append({
                'item_type':        'announcement',
                'source':           ann,
                'disc':             disc,
                'created_by_user':  creator_user,
                'photo_url':        photo_url,
                'created_at':       ann.created_at,
                'action_text':      cfg['action_text'],
                'course_name':      course.name,
                'session_name':     '',
                'title':            ann.title,
                'description':      ann.content[:200] if ann.content else '',
                'icon':             cfg['icon'],
                'color':            cfg['color'],
                'attachment_url':   None,
                'attachment_name':  None,
                'attachment_icon':  '',
                'attachment_color': '',
                'is_published':     True,
                'extra': {
                    'priority':       ann.priority,
                    'priority_color': PRIORITY_COLORS.get(ann.priority, '#696cff'),
                    'is_pinned':      ann.is_pinned,
                    'content':        ann.content,
                    'allow_discussion': ann.allow_discussion,
                },
            })

    # ── 5. Manual student discussions (no linked source) ────────────
    if show_manual_discussion:
        student_discs = (
            CourseDiscussion.objects
            .filter(course=course, agenda__isnull=True,
                    material__isnull=True, assignment__isnull=True,
                    announcement__isnull=True)
            .select_related('created_by')
            .prefetch_related('likes', 'replies')
            .order_by('-created_at')
        )
        for disc in student_discs:
            cfg = FEED_CONFIG['discussion']
            feed_items.append({
                'item_type':        'discussion',
                'source':           disc,
                'disc':             disc,
                'created_by_user':  disc.created_by,
                'photo_url':        None,
                'created_at':       disc.created_at,
                'action_text':      cfg['action_text'],
                'course_name':      course.name,
                'session_name':     '',
                'title':            disc.title,
                'description':      '',
                'icon':             TYPE_ICONS.get(disc.discussion_type, cfg['icon']),
                'color':            TYPE_COLORS.get(disc.discussion_type, cfg['color']),
                'attachment_url':   None,
                'attachment_name':  None,
                'attachment_icon':  '',
                'attachment_color': '',
                'is_published':     True,
                'extra': {
                    'disc_type': disc.discussion_type,
                    'is_pinned': disc.is_pinned,
                    'is_closed': disc.is_closed,
                },
            })

    # ── Sort newest first ────────────────────────────────────────────
    feed_items.sort(key=lambda x: x['created_at'], reverse=True)

    # Pengumuman (announcement) tidak butuh CourseDiscussion thread, tampilkan selalu
    feed_items = [
        fi for fi in feed_items
        if fi['item_type'] in ('discussion', 'announcement') or fi['disc'] is not None
    ]

    # Filter "Diskusi": hanya baris yang punya CourseDiscussion di DB / feed.
    if filter_type == 'discussion':
        feed_items = [fi for fi in feed_items if fi['disc'] is not None]

    # ── Annotate like / reply counts ─────────────────────────────────
    all_disc_ids = [fi['disc'].id for fi in feed_items if fi['disc']]
    user_liked_ids = set(
        CourseDiscussionLike.objects
        .filter(user=user, discussion_id__in=all_disc_ids, reply__isnull=True)
        .values_list('discussion_id', flat=True)
    )
    for fi in feed_items:
        d = fi['disc']
        if d:
            d.user_liked   = d.id in user_liked_ids
            d.like_count_  = d.like_count()
            d.reply_count_ = d.reply_count()

    # ── Prefetch top replies untuk inline display ─────────────────────

    inline_replies_qs = (
        CourseDiscussionReply.objects
        .filter(discussion_id__in=all_disc_ids, parent__isnull=True)
        .select_related('created_by')
        .order_by('created_at')
    )
    replies_map = defaultdict(list)
    for reply in inline_replies_qs:
        replies_map[reply.discussion_id].append(reply)

    for fi in feed_items:
        d = fi['disc']
        if d:
            d.inline_replies_ = replies_map.get(d.id, [])

    # ── Like count + user_liked untuk top-level replies ───────────────
    all_top_reply_ids = [
        r.id
        for fi in feed_items
        if fi['disc'] and hasattr(fi['disc'], 'inline_replies_')
        for r in fi['disc'].inline_replies_
    ]
    if all_top_reply_ids:
        user_liked_reply_ids = set(
            CourseDiscussionLike.objects
            .filter(user=user, reply_id__in=all_top_reply_ids)
            .values_list('reply_id', flat=True)
        )

        # Prefetch children (nested replies)
        children_qs = (
            CourseDiscussionReply.objects
            .filter(parent_id__in=all_top_reply_ids)
            .select_related('created_by')
            .order_by('created_at')
        )
        children_map = defaultdict(list)
        for child in children_qs:
            children_map[child.parent_id].append(child)

        # Like data untuk children
        all_child_ids = [c.id for clist in children_map.values() for c in clist]
        user_liked_child_ids = set(
            CourseDiscussionLike.objects
            .filter(user=user, reply_id__in=all_child_ids)
            .values_list('reply_id', flat=True)
        ) if all_child_ids else set()

        for fi in feed_items:
            d = fi['disc']
            if d and hasattr(d, 'inline_replies_'):
                for reply in d.inline_replies_:
                    reply.user_liked_  = reply.id in user_liked_reply_ids
                    reply.like_count_  = reply.like_count()
                    reply.children_    = children_map.get(reply.id, [])
                    for child in reply.children_:
                        child.user_liked_ = child.id in user_liked_child_ids
                        child.like_count_ = child.like_count()
    else:
        for fi in feed_items:
            d = fi['disc']
            if d and hasattr(d, 'inline_replies_'):
                for reply in d.inline_replies_:
                    reply.user_liked_ = False
                    reply.like_count_ = 0
                    reply.children_   = []

    return feed_items




# ─────────────────────────────────────────────
# Base view
# ─────────────────────────────────────────────

class DiscussionBaseView(LoginRequiredMixin, View):
    template_name = None

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, {})
        context.update(kwargs)
        return context

    def render(self, context):
        return render(self.request, self.template_name, context)


# ─────────────────────────────────────────────
# 1. Activity Feed – Social Media Style
# ─────────────────────────────────────────────

class CourseDiscussionListView(DiscussionBaseView):
    template_name = "discussion_list.html"

    def get(self, request, course_uuid, *args, **kwargs):
        try:
            course, is_dosen, is_student = _get_course_access(request, course_uuid)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('app-academy-dashboard')

        filter_type = request.GET.get('type', '')
        feed_items  = _build_activity_feed(request, course, is_dosen, filter_type)

        context = self.get_context_data(
            course=course,
            feed_items=feed_items,
            is_dosen=is_dosen,
            is_student=is_student,
            filter_type=filter_type,
        )
        return self.render(context)


class CourseDiscussionDeleteView(DiscussionBaseView):
    """
    Hapus satu discussion.
    Hanya dosen atau admin yang boleh hapus.
    """
    def post(self, request, course_uuid, disc_id):
        try:
            course, is_dosen, is_student = _get_course_access(request, course_uuid)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('app-academy-dashboard')

        if not is_dosen:
            messages.error(request, "Anda tidak punya hak untuk menghapus diskusi.")
            return redirect('course-discussion-list', course_uuid=course_uuid)

        try:
            disc = CourseDiscussion.objects.get(id=disc_id, course=course)
        except CourseDiscussion.DoesNotExist:
            messages.error(request, "Diskusi tidak ditemukan.")
            return redirect('course-discussion-list', course_uuid=course_uuid)

        title_for_msg = disc.title or f"diskusi (ID:{disc_id})"
        disc.delete()

        messages.success(request,
            f"Diskusi '{title_for_msg}' berhasil dihapus."
        )
        next_url = request.POST.get("next") or request.GET.get("next") or \
                   request.META.get("HTTP_REFERER") or \
                   reverse_lazy("course-discussion-list", args=[course_uuid])

        return redirect(next_url)


# ─────────────────────────────────────────────
# 3. Detail Diskusi + Reply
# ─────────────────────────────────────────────

class CourseDiscussionDetailView(DiscussionBaseView):
    template_name = "discussion_detail.html"

    def _get_discussion(self, course, disc_id):
        return get_object_or_404(
            CourseDiscussion.objects
            .select_related('created_by', 'agenda', 'material', 'assignment', 'course')
            .prefetch_related(
                'likes',
                'replies__created_by',
                'replies__likes',
                'replies__children__created_by',
                'replies__children__likes',
            ),
            id=disc_id, course=course
        )

    def get(self, request, course_uuid, disc_id, *args, **kwargs):
        try:
            course, is_dosen, is_student = _get_course_access(request, course_uuid)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('app-academy-dashboard')

        disc = self._get_discussion(course, disc_id)

        # Kumpulkan semua reply + nested children
        top_replies = disc.replies.filter(parent__isnull=True)

        # User sudah like diskusi ini?
        user_liked_disc = disc.likes.filter(user=request.user).exists()

        # User sudah like reply apa saja?
        all_reply_ids = list(disc.replies.values_list('id', flat=True))
        user_liked_replies = set(
            CourseDiscussionLike.objects
            .filter(user=request.user, reply_id__in=all_reply_ids)
            .values_list('reply_id', flat=True)
        )

        # Tambah helper ke setiap reply
        for reply in top_replies:
            reply.user_liked = reply.id in user_liked_replies
            for child in reply.children.all():
                child.user_liked = child.id in user_liked_replies

        disc.user_liked   = user_liked_disc
        disc.type_icon    = TYPE_ICONS.get(disc.discussion_type, 'ri-discuss-line')
        disc.type_color   = TYPE_COLORS.get(disc.discussion_type, 'secondary')

        context = self.get_context_data(
            course=course,
            disc=disc,
            top_replies=top_replies,
            is_dosen=is_dosen,
            is_student=is_student,
        )
        return self.render(context)

    def post(self, request, course_uuid, disc_id, *args, **kwargs):
        """Kirim reply baru."""
        try:
            course, is_dosen, is_student = _get_course_access(request, course_uuid)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('app-academy-dashboard')

        disc = get_object_or_404(CourseDiscussion, id=disc_id, course=course)

        if disc.is_closed and not is_dosen:
            messages.warning(request, 'Diskusi ini sudah ditutup.')
            return redirect('course-discussion-detail', course_uuid=course.uuid, disc_id=disc.id)

        body      = request.POST.get('body', '').strip()
        parent_id = request.POST.get('parent_id') or None

        if not body:
            messages.error(request, 'Komentar tidak boleh kosong.')
            return redirect('course-discussion-detail', course_uuid=course.uuid, disc_id=disc.id)

        reply = CourseDiscussionReply(discussion=disc, body=body, created_by=request.user)
        if parent_id:
            parent = get_object_or_404(CourseDiscussionReply, id=parent_id, discussion=disc, parent__isnull=True)
            reply.parent = parent

        reply.save()
        messages.success(request, 'Komentar berhasil dikirim.')

        # Jika request dari feed (ada referrer berupa discussion-list), balik ke feed
        referer = request.POST.get('next', '')
        if referer:
            return redirect(referer)
        return redirect('course-discussion-detail', course_uuid=course.uuid, disc_id=disc.id)


# ─────────────────────────────────────────────
# 5. Toggle Pin (Dosen Only)
# ─────────────────────────────────────────────

class CourseDiscussionTogglePinView(DiscussionBaseView):
    def post(self, request, course_uuid, disc_id, *args, **kwargs):
        try:
            course, is_dosen, _ = _get_course_access(request, course_uuid)
        except PermissionError as e:
            return JsonResponse({'error': str(e)}, status=403)

        if not is_dosen and not request.user.is_superuser:
            return JsonResponse({'error': 'Hanya dosen yang bisa pin.'}, status=403)

        disc = get_object_or_404(CourseDiscussion, id=disc_id, course=course)
        disc.is_pinned = not disc.is_pinned
        disc.save(update_fields=['is_pinned'])
        return JsonResponse({'pinned': disc.is_pinned})


# ─────────────────────────────────────────────
# 6. Toggle Close (Dosen Only)
# ─────────────────────────────────────────────

class CourseDiscussionToggleCloseView(DiscussionBaseView):
    def post(self, request, course_uuid, disc_id, *args, **kwargs):
        try:
            course, is_dosen, _ = _get_course_access(request, course_uuid)
        except PermissionError as e:
            return JsonResponse({'error': str(e)}, status=403)

        if not is_dosen and not request.user.is_superuser:
            return JsonResponse({'error': 'Hanya dosen yang bisa menutup diskusi.'}, status=403)

        disc = get_object_or_404(CourseDiscussion, id=disc_id, course=course)
        disc.is_closed = not disc.is_closed
        disc.save(update_fields=['is_closed'])
        return JsonResponse({'closed': disc.is_closed})


# ─────────────────────────────────────────────
# 7. Like Toggle (AJAX)
# ─────────────────────────────────────────────

class DiscussionLikeToggleView(DiscussionBaseView):
    def post(self, request, course_uuid, disc_id, *args, **kwargs):
        try:
            course, _, _ = _get_course_access(request, course_uuid)
        except PermissionError as e:
            return JsonResponse({'error': str(e)}, status=403)

        disc = get_object_or_404(CourseDiscussion, id=disc_id, course=course)

        existing = CourseDiscussionLike.objects.filter(
            discussion=disc, reply__isnull=True, user=request.user
        ).first()

        if existing:
            existing.delete()
            liked = False
        else:
            CourseDiscussionLike.objects.create(discussion=disc, user=request.user)
            liked = True

        return JsonResponse({'liked': liked, 'count': disc.like_count()})


# ─────────────────────────────────────────────
# 8. Reply Like Toggle (AJAX)
# ─────────────────────────────────────────────

class ReplyLikeToggleView(DiscussionBaseView):
    def post(self, request, course_uuid, reply_id, *args, **kwargs):
        try:
            course, _, _ = _get_course_access(request, course_uuid)
        except PermissionError as e:
            return JsonResponse({'error': str(e)}, status=403)

        reply = get_object_or_404(
            CourseDiscussionReply,
            id=reply_id, discussion__course=course
        )

        existing = CourseDiscussionLike.objects.filter(
            reply=reply, discussion__isnull=True, user=request.user
        ).first()

        if existing:
            existing.delete()
            liked = False
        else:
            CourseDiscussionLike.objects.create(reply=reply, user=request.user)
            liked = True

        return JsonResponse({'liked': liked, 'count': reply.like_count()})


# ─────────────────────────────────────────────
# 9. Hapus Reply
# ─────────────────────────────────────────────

class DiscussionReplyDeleteView(DiscussionBaseView):
    def post(self, request, course_uuid, reply_id, *args, **kwargs):
        try:
            course, is_dosen, _ = _get_course_access(request, course_uuid)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('app-academy-dashboard')

        reply = get_object_or_404(
            CourseDiscussionReply,
            id=reply_id, discussion__course=course
        )

        if reply.created_by != request.user and not is_dosen and not request.user.is_superuser:
            messages.error(request, 'Anda tidak bisa menghapus komentar ini.')
        else:
            disc_id = reply.discussion_id
            reply.delete()
            messages.success(request, 'Komentar berhasil dihapus.')
            return redirect('course-discussion-detail', course_uuid=course.uuid, disc_id=disc_id)

        return redirect('course-discussion-list', course_uuid=course.uuid)
