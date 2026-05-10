/**
 * App Kanban – Django Backend Integration
 * Semua operasi board & task disimpan ke database via REST API.
 */

'use strict';

(async function () {
  // ─── DOM refs ───────────────────────────────────────────────────────────────
  const kanbanSidebar = document.querySelector('.kanban-update-item-sidebar');
  const kanbanWrapper = document.querySelector('.kanban-wrapper');
  const commentEditor = document.querySelector('.comment-editor');
  const kanbanAddNewBoard = document.querySelector('.kanban-add-new-board');
  const kanbanAddNewInput = [].slice.call(document.querySelectorAll('.kanban-add-board-input'));
  const kanbanAddBoardBtn = document.querySelector('.kanban-add-board-btn');
  const datePicker = document.querySelector('#due-date');
  const select2El = $('.select2');
  const assetsPath = document.querySelector('html').getAttribute('data-assets-path');

  // ─── API helpers ────────────────────────────────────────────────────────────
  function getCsrfToken() {
    // coba dari meta tag dulu, fallback ke cookie
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    return document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
  }

  async function apiGet(url) {
    const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!res.ok) throw new Error(`GET ${url} → ${res.status}`);
    return res.json();
  }

  async function apiPost(url, data) {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `POST ${url} → ${res.status}`);
    }
    return res.json();
  }

  async function apiPostForm(url, formData) {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `POST ${url} → ${res.status}`);
    }
    return res.json();
  }

  async function apiPut(url, data) {
    const res = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `PUT ${url} → ${res.status}`);
    }
    return res.json();
  }

  async function apiDelete(url) {
    const res = await fetch(url, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
    });
    if (!res.ok) throw new Error(`DELETE ${url} → ${res.status}`);
    return res.json();
  }

  // ─── State ──────────────────────────────────────────────────────────────────
  // Dipenuhi dari API saat load
  let boardsData = [];          // [{id, title, order, tasks:[{id,title,...}]}]
  let activeTaskId = null;     // UUID task yang sedang diedit di sidebar
  let activeBoardId = null;     // UUID board task tsb

  // ─── Fetch boards dari Django ────────────────────────────────────────────────
  try {
    boardsData = await apiGet('/api/kanban/boards/');
  } catch (e) {
    console.error('Gagal memuat data kanban:', e);
    boardsData = [];
  }

  // ─── jKanban board format ────────────────────────────────────────────────────
  function toJKanbanBoards(data) {
    return data.map(b => ({
      id: b.id,
      title: b.title,
      item: b.tasks.map(t => ({
        id: t.id,
        title: buildItemHTML(t),
        // custom data attrs untuk sidebar
        'data-task-id': t.id,
        'data-badge': labelColor2Badge(t.label_color),
        'data-badge-text': t.label || '',
        'data-due-date': t.due_date || '',
        'data-comments': t.comments || '',
        'data-attachments': t.attachments || '',
      }))
    }));
  }

  /** Konversi label_color "bg-label-primary" → "primary" */
  function labelColor2Badge(lc) {
    if (!lc) return 'primary';
    return lc.replace('bg-label-', '');
  }

  /** HTML konten item kanban */
  function buildItemHTML(task) {
    const badge = task.label_color ? task.label_color.replace('bg-label-', '') : 'primary';
    const label = task.label || '';
    let html = '';

    // Tampilkan lampiran (gambar atau file lain)
    if (task.attachments) {
      const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(task.attachments.split('?')[0]);
      if (isImage) {
        html += `<div class="mb-2 kanban-image-cover">
                   <img src="${task.attachments}" class="img-fluid rounded w-100" style="max-height: 160px; object-fit: cover;" alt="Attachment">
                 </div>`;
      } else {
        const fileName = task.attachments.split('/').pop().split('?')[0];
        html += `<div class="mb-2">
                   <a href="${task.attachments}" target="_blank" class="badge bg-label-secondary text-wrap text-start w-100" style="word-break: break-all;">
                     <i class="ri-file-download-line align-middle me-1"></i><span class="align-middle">${fileName}</span>
                   </a>
                 </div>`;
      }
    }

    if (label) {
      html += renderHeader(badge, label);
    } else {
      // Tambah dropdown meskipun tidak ada label
      html += `<div class='d-flex justify-content-end mb-1'>${renderDropdown()}</div>`;
    }
    html += `<span class='kanban-text'>${escHtml(task.title)}</span>`;
    
    let ts = '';
    if (task.creator_name) ts += `By: <span class='fw-medium text-body'>${escHtml(task.creator_name)}</span>`;
    if (task.created_at) ts += ts ? `<br>Created: ${task.created_at}` : `Created: ${task.created_at}`;
    if (task.updated_at && task.updated_at !== task.created_at) ts += `<br>Updated: ${task.updated_at}`;
    if (ts) {
      html += `<div class='text-muted' style='font-size: 0.7rem; margin-top: 4px; line-height: 1.3;'>${ts}</div>`;
    }

    html += renderFooter(task.attachments || '', task.comments || '', task.assignees || []);
    return html;
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ─── Render helpers (dari template asli) ─────────────────────────────────────
  function renderBoardDropdown() {
    return (
      "<div class='dropdown'>" +
      "<i class='dropdown-toggle ri-more-2-line ri-20px cursor-pointer' id='board-dropdown' data-bs-toggle='dropdown' aria-haspopup='true' aria-expanded='false'></i>" +
      "<div class='dropdown-menu dropdown-menu-end' aria-labelledby='board-dropdown'>" +
      "<a class='dropdown-item delete-board' href='javascript:void(0)'> <i class='ri-delete-bin-7-line'></i> <span class='align-middle'>Delete</span></a>" +
      "<a class='dropdown-item rename-board' href='javascript:void(0)'><i class='ri-edit-2-fill'></i> <span class='align-middle'>Rename</span></a>" +
      '</div>' +
      '</div>'
    );
  }

  function renderDropdown() {
    return (
      "<div class='dropdown kanban-tasks-item-dropdown'>" +
      "<i class='dropdown-toggle ri-more-2-line' id='kanban-tasks-item-dropdown' data-bs-toggle='dropdown' aria-haspopup='true' aria-expanded='false'></i>" +
      "<div class='dropdown-menu dropdown-menu-end' aria-labelledby='kanban-tasks-item-dropdown'>" +
      "<a class='dropdown-item delete-task' href='javascript:void(0)'>Delete</a>" +
      '</div>' +
      '</div>'
    );
  }

  function renderHeader(color, text) {
    return (
      "<div class='d-flex justify-content-between flex-wrap align-items-center mb-2'>" +
      "<div class='item-badges d-flex'> " +
      "<div class='badge rounded-pill bg-label-" + color + "'> " + escHtml(text) + '</div>' +
      '</div>' +
      renderDropdown() +
      '</div>'
    );
  }

  function renderFooter(attachments, comments, assignees) {
    // Avatar assignees
    let avatarsHtml = '';
    if (assignees && assignees.length) {
      avatarsHtml = "<div class='avatar-group d-flex align-items-center ms-auto'>";
      assignees.slice(0, 4).forEach(a => {
        avatarsHtml += `<div class='avatar avatar-xs pull-up' title='${escHtml(a.name)}' data-bs-toggle='tooltip' data-bs-placement='top'>`;
        avatarsHtml += `<img src='${a.avatar}' alt='${escHtml(a.name)}' class='rounded-circle'>`;
        avatarsHtml += `</div>`;
      });
      if (assignees.length > 4) avatarsHtml += `<span class='badge bg-secondary rounded-pill ms-1'>+${assignees.length - 4}</span>`;
      avatarsHtml += '</div>';
    }
    return (
      "<div class='d-flex justify-content-between align-items-center flex-wrap mt-2'>" +
      "<div> <span class='align-middle me-3'><i class='ri-attachment-2 ri-20px me-1'></i>" +
      "<span class='attachments'>" + (attachments ? '1' : '0') + '</span>' +
      "</span> <span class='align-middle'><i class='ri-wechat-line ri-20px me-1'></i>" +
      '<span>' + (comments ? '1' : '0') + ' </span>' +
      '</span></div>' +
      avatarsHtml +
      '</div>'
    );
  }

  // ─── Init Offcanvas ──────────────────────────────────────────────────────────
  const kanbanOffcanvas = new bootstrap.Offcanvas(kanbanSidebar);

  // ─── Flatpickr ──────────────────────────────────────────────────────────────
  let fpInstance;
  if (datePicker) {
    fpInstance = datePicker.flatpickr({
      monthSelectorType: 'static',
      altInput: true,
      altFormat: 'j F, Y',
      dateFormat: 'Y-m-d',
    });
  }

  // ─── Select2 label ───────────────────────────────────────────────────────────
  if (select2El.length) {
    function renderLabels(option) {
      if (!option.id) return option.text;
      return "<div class='badge " + $(option.element).data('color') + " rounded-pill'> " + option.text + '</div>';
    }
    select2El.each(function () {
      var $this = $(this);
      select2Focus($this);
      $this.wrap("<div class='position-relative'></div>").select2({
        placeholder: 'Select Label',
        dropdownParent: $this.parent(),
        templateResult: renderLabels,
        templateSelection: renderLabels,
        escapeMarkup: function (es) { return es; }
      });
    });
  }

  // ─── Select2 AJAX Assignees ──────────────────────────────────────────────────
  const $assigneeSel = $('#kanban-assignees');
  // dropdownParent WAJIB mengarah ke offcanvas agar dropdown tidak tertutup overlay
  const $offcanvasBody = $('.kanban-update-item-sidebar .offcanvas-body');

  function renderAssigneeOption(u) {
    if (!u.id) return u.text || '';
    const avatar = u.avatar || '/static/img/avatars/5.png';
    const name = escHtml(u.text || u.name || '');
    return $(`<span><img src="${avatar}" class="rounded-circle me-1" width="22" height="22" onerror="this.src='/static/img/avatars/5.png'"> ${name}</span>`);
  }

  if ($assigneeSel.length) {
    $assigneeSel.select2({
      placeholder: 'Ketik nama untuk mencari...',
      allowClear: true,
      minimumInputLength: 0,
      dropdownParent: $offcanvasBody,
      ajax: {
        url: '/api/kanban/users/',
        dataType: 'json',
        delay: 250,
        data: params => ({ q: params.term || '' }),
        processResults: data => ({ results: data.results }),
        cache: true,
      },
      templateResult: renderAssigneeOption,
      templateSelection: renderAssigneeOption,
      escapeMarkup: m => m,
    });
  }

  // Helper: refresh avatar bar di bawah select assignee
  function refreshAssigneeAvatars() {
    const selected = $assigneeSel.select2('data');
    const bar = document.getElementById('assignee-avatars');
    if (!bar) return;
    bar.innerHTML = selected.map(u =>
      `<img src="${u.avatar || '/static/img/avatars/5.png'}" class="rounded-circle" width="30" height="30" title="${escHtml(u.text || u.name)}" data-bs-toggle="tooltip">`
    ).join('');
    // Init tooltips
    bar.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
  }
  $assigneeSel.on('change', refreshAssigneeAvatars);

  // ─── Quill comment editor ────────────────────────────────────────────────────
  let quillEditor;
  if (commentEditor) {
    quillEditor = new Quill(commentEditor, {
      modules: { toolbar: '.comment-toolbar' },
      placeholder: 'Tulis komentar...',
      theme: 'snow',
    });
  }

  // ─── Init jKanban ────────────────────────────────────────────────────────────
  const kanban = new jKanban({
    element: '.kanban-wrapper',
    gutter: '12px',
    widthBoard: '250px',
    dragItems: true,
    boards: toJKanbanBoards(boardsData),
    dragBoards: true,
    addItemButton: true,
    buttonContent: '+ Add Item',
    itemAddOptions: {
      enabled: true,
      content: '+ Tambah Task',
      class: 'kanban-title-button btn btn-default btn-md shadow-none text-capitalize fw-normal text-heading',
      footer: false,
    },

    // ── Klik task → buka sidebar edit ─────────────────────────────────────────
    click: function (el) {
      const taskId = el.getAttribute('data-eid');
      const boardEl = el.closest('.kanban-board');
      const boardId = boardEl ? boardEl.getAttribute('data-id') : null;

      // Cari data task dari state
      const board = boardsData.find(b => b.id === boardId);
      const task = board ? board.tasks.find(t => t.id === taskId) : null;
      if (!task) return;

      activeTaskId = taskId;
      activeBoardId = boardId;

      // Isi form sidebar
      kanbanSidebar.querySelector('#title').value = task.title;
      if (fpInstance) fpInstance.setDate(task.due_date || '');

      // Select2 label
      const labelOpt = kanbanSidebar.querySelector(`#label option[value="${task.label}"]`);
      if (labelOpt) {
        $('.kanban-update-item-sidebar').find(select2El).val(task.label).trigger('change');
      } else {
        $('.kanban-update-item-sidebar').find(select2El).val(null).trigger('change');
      }

      // Populate assignees Select2
      $assigneeSel.val(null).trigger('change');  // reset
      if (task.assignees && task.assignees.length) {
        task.assignees.forEach(a => {
          // Buat option baru jika belum ada
          if (!$assigneeSel.find(`option[value="${a.id}"]`).length) {
            $assigneeSel.append(new Option(a.name, a.id, true, true));
            // Simpan avatar ke data option agar templateSelection bisa pakai
            $assigneeSel.find(`option[value="${a.id}"]`).data('avatar', a.avatar);
          }
        });
        $assigneeSel.val(task.assignees.map(a => a.id)).trigger('change');
      }
      refreshAssigneeAvatars();

      // Tampilkan info attachment saat ini di sidebar
      const currentAttachmentDiv = kanbanSidebar.querySelector('#current-attachment');
      if (currentAttachmentDiv) {
        if (task.attachments) {
          const fileName = task.attachments.split('/').pop().split('?')[0];
          currentAttachmentDiv.innerHTML = `<a href="${task.attachments}" target="_blank" class="text-primary mt-1 d-inline-block" style="font-size: 0.85rem;"><i class="ri-attachment-2 align-middle me-1"></i><span class="align-middle">Lihat File: ${fileName}</span></a>`;
          currentAttachmentDiv.classList.remove('d-none');
        } else {
          currentAttachmentDiv.innerHTML = '';
          currentAttachmentDiv.classList.add('d-none');
        }
      }

      // Quill comment
      if (quillEditor) {
        quillEditor.root.innerHTML = task.comments || '';
      }

      // Render activity history
      const activityTab = kanbanSidebar.querySelector('#tab-activity');
      if (activityTab) {
        if (task.activities && task.activities.length > 0) {
          activityTab.innerHTML = task.activities.map(act => `
            <div class="media mb-4 d-flex align-items-center">
              <div class="avatar me-3 flex-shrink-0">
                <img src="${act.avatar}" alt="Avatar" class="rounded-circle" onerror="this.src='/static/img/avatars/5.png'">
              </div>
              <div class="media-body ms-1">
                <p class="mb-0">
                  <span class="fw-medium">${escHtml(act.user)}</span> ${escHtml(act.text)}
                </p>
                <small class="text-muted">${act.created_at}</small>
              </div>
            </div>
          `).join('');
        } else {
          activityTab.innerHTML = '<div class="text-center text-muted mt-4">Belum ada aktivitas.</div>';
        }
      }

      kanbanOffcanvas.show();
    },

    // ── Tombol "+ Tambah Task" di tiap board ──────────────────────────────────
    buttonClick: function (el, boardId) {
      const addNew = document.createElement('form');
      addNew.setAttribute('class', 'new-item-form');
      addNew.innerHTML =
        '<div class="mb-4">' +
        '<textarea class="form-control add-new-item" rows="2" placeholder="Judul task..." autofocus required></textarea>' +
        '</div>' +
        '<div class="mb-4">' +
        '<button type="submit" class="btn btn-primary btn-sm me-4">Tambah</button>' +
        '<button type="button" class="btn btn-outline-secondary btn-sm cancel-add-item">Batal</button>' +
        '</div>';
      kanban.addForm(boardId, addNew);

      addNew.addEventListener('submit', async function (e) {
        e.preventDefault();
        const title = e.target[0].value.trim();
        if (!title) return;

        try {
          const newTask = await apiPost(`/api/kanban/boards/${boardId}/tasks/`, { title });

          // Update state
          const board = boardsData.find(b => b.id === boardId);
          if (board) board.tasks.push(newTask);

          // jKanban render
          kanban.addElement(boardId, {
            id: newTask.id,
            title: buildItemHTML(newTask),
            'data-task-id': newTask.id,
          });

          // pasang event dropdown di item baru
          attachDropdownEvents(boardId);
          addNew.remove();
        } catch (err) {
          console.error('Gagal tambah task:', err);
          alert('Gagal menyimpan task: ' + err.message);
        }
      });

      addNew.querySelector('.cancel-add-item').addEventListener('click', () => addNew.remove());
    },

    // ── Drag-drop board selesai → kirim reorder ke API ─────────────────────
    dropBoard: async function (el) {
      const allBoards = [].slice.call(document.querySelectorAll('.kanban-board'));
      const items = allBoards.map((b, i) => ({ id: b.getAttribute('data-id'), order: i }));
      try {
        await apiPost('/api/kanban/reorder/', { type: 'board', items });
        items.forEach(item => {
          const b = boardsData.find(b => b.id === item.id);
          if (b) b.order = item.order;
        });
      } catch (err) {
        console.error('Gagal reorder board:', err);
      }
    },

    // ── Drag-drop task selesai → kirim reorder/pindah board ke API ───────────
    // dropEl(el, target, source, sibling)
    // el     = item yang dipindah
    // target = board container tujuan (.kanban-drag)
    // source = board container asal
    dropEl: async function (el, target, source, sibling) {
      const taskId = el.getAttribute('data-eid');
      const newBoardEl = target ? target.closest('.kanban-board') : null;
      const newBoardId = newBoardEl ? newBoardEl.getAttribute('data-id') : null;
      if (!taskId || !newBoardId) return;

      // Hitung order baru semua task di board tujuan agar tidak bentrok
      const siblings = [].slice.call(target.querySelectorAll('.kanban-item'));
      const itemsPayload = siblings.map((s, idx) => ({
        id: s.getAttribute('data-eid'),
        board_id: newBoardId,
        order: idx
      }));

      try {
        await apiPost('/api/kanban/reorder/', {
          type: 'task',
          items: itemsPayload,
        });

        // Update state in-memory
        // 1. Hapus task dari board lama
        let movedTask = null;
        boardsData.forEach(b => {
          const idx = b.tasks.findIndex(t => t.id === taskId);
          if (idx !== -1) {
            movedTask = b.tasks.splice(idx, 1)[0];
          }
        });

        // 2. Update urutan di board baru
        if (movedTask) {
          const destBoard = boardsData.find(b => b.id === newBoardId);
          if (destBoard) {
            movedTask.board_id = newBoardId;
            destBoard.tasks.push(movedTask);
            // Sortir ulang tasks di board tujuan sesuai urutan payload
            destBoard.tasks.sort((a, b) => {
              const idxA = itemsPayload.findIndex(p => p.id === a.id);
              const idxB = itemsPayload.findIndex(p => p.id === b.id);
              return idxA - idxB;
            });
            // Update property order di state
            destBoard.tasks.forEach((t, i) => t.order = i);
          }
        }
      } catch (err) {
        console.error('Gagal reorder task:', err);
      }
    },
  });

  // ─── Pasang event dropdown (delete) untuk item yang sudah dirender ───────────
  function attachDropdownEvents(boardId) {
    const selector = boardId
      ? `.kanban-board[data-id="${boardId}"] .delete-task`
      : '.delete-task';
    const deleteTaskBtns = [].slice.call(document.querySelectorAll(selector));
    deleteTaskBtns.forEach(btn => {
      // hapus listener lama agar tidak double
      btn.replaceWith(btn.cloneNode(true));
    });
    const freshBtns = [].slice.call(document.querySelectorAll(selector));
    freshBtns.forEach(btn => {
      btn.addEventListener('click', async function (e) {
        e.stopPropagation();
        const item = this.closest('.kanban-item');
        const taskId = item ? item.getAttribute('data-eid') : null;
        if (!taskId) return;
        if (!confirm('Hapus task ini?')) return;
        try {
          await apiDelete(`/api/kanban/tasks/${taskId}/`);
          boardsData.forEach(b => {
            b.tasks = b.tasks.filter(t => t.id !== taskId);
          });
          kanban.removeElement(taskId);
        } catch (err) {
          console.error('Gagal hapus task:', err);
          alert('Gagal menghapus task: ' + err.message);
        }
      });
    });

    // Prevent sidebar saat klik dropdown
    const dropdowns = [].slice.call(document.querySelectorAll('.kanban-tasks-item-dropdown'));
    dropdowns.forEach(d => {
      d.addEventListener('click', e => e.stopPropagation());
    });
  }

  attachDropdownEvents(null); // init untuk semua item yang sudah ada

  // ─── Sidebar: tombol Update ──────────────────────────────────────────────────
  const updateBtn = document.getElementById('kanban-update-btn');
  const updateSpinner = document.getElementById('kanban-update-spinner');
  if (updateBtn) {
    updateBtn.addEventListener('click', async function () {
      if (!activeTaskId) return;
      const title = kanbanSidebar.querySelector('#title').value.trim();
      const dueDate = kanbanSidebar.querySelector('#due-date').value;
      const label = $('.kanban-update-item-sidebar').find(select2El).val();
      const labelColor = label
        ? 'bg-label-' + ($('.kanban-update-item-sidebar').find(`#label option[value="${label}"]`).data('color') || label).replace('bg-label-', '')
        : 'bg-label-primary';
      const comments = quillEditor ? quillEditor.root.innerHTML : '';

      if (!title) { alert('Judul tidak boleh kosong.'); return; }

      if (updateSpinner) updateSpinner.classList.remove('d-none');
      updateBtn.disabled = true;
      try {
        // Gunakan FormData untuk mendukung upload file
        const formData = new FormData();
        formData.append('title', title);
        if (dueDate) formData.append('due_date', dueDate);
        if (label) formData.append('label', label);
        if (labelColor) formData.append('label_color', labelColor);
        if (comments) formData.append('comments', comments);

        // Ambil assignee IDs dari Select2
        const assigneeIds = $assigneeSel.val() ? $assigneeSel.val().map(Number) : [];
        assigneeIds.forEach(id => formData.append('assignee_ids', id));

        const fileInput = kanbanSidebar.querySelector('#attachments');
        if (fileInput && fileInput.files.length > 0) {
          formData.append('attachments', fileInput.files[0]);
        }

        const updated = await apiPostForm(`/api/kanban/tasks/${activeTaskId}/`, formData);

        // Update state
        boardsData.forEach(b => {
          const t = b.tasks.find(t => t.id === activeTaskId);
          if (t) Object.assign(t, updated);
        });

        // Update DOM
        const itemEl = document.querySelector(`.kanban-item[data-eid="${activeTaskId}"]`);
        if (itemEl) {
          itemEl.innerHTML = buildItemHTML(updated);
          attachDropdownEvents(null);
          // Re-init tooltips untuk avatar baru
          itemEl.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
        }
        kanbanOffcanvas.hide();
      } catch (err) {
        console.error('Gagal update task:', err);
        alert('Gagal memperbarui task: ' + err.message);
      } finally {
        if (updateSpinner) updateSpinner.classList.add('d-none');
        updateBtn.disabled = false;
      }
    });
  }

  // ─── Sidebar: tombol Delete ──────────────────────────────────────────────────
  const deleteBtn = document.getElementById('kanban-delete-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async function () {
      if (!activeTaskId) return;
      if (!confirm('Yakin hapus task ini?')) return;
      try {
        await apiDelete(`/api/kanban/tasks/${activeTaskId}/`);
        boardsData.forEach(b => { b.tasks = b.tasks.filter(t => t.id !== activeTaskId); });
        kanban.removeElement(activeTaskId);
        activeTaskId = null;
        kanbanOffcanvas.hide();
      } catch (err) {
        console.error('Gagal hapus task:', err);
        alert('Gagal menghapus task: ' + err.message);
      }
    });
  }

  // Reset quill + assignees saat offcanvas ditutup
  kanbanSidebar.addEventListener('hidden.bs.offcanvas', function () {
    const qlEditor = kanbanSidebar.querySelector('.ql-editor');
    if (qlEditor && qlEditor.firstElementChild) qlEditor.firstElementChild.innerHTML = '';
    $assigneeSel.val(null).trigger('change');
    const bar = document.getElementById('assignee-avatars');
    if (bar) bar.innerHTML = '';
    activeTaskId = null;
  });

  // ─── Tooltip re-init saat offcanvas dibuka ───────────────────────────────────
  if (kanbanSidebar) {
    kanbanSidebar.addEventListener('shown.bs.offcanvas', function () {
      const tipTriggers = [].slice.call(kanbanSidebar.querySelectorAll('[data-bs-toggle="tooltip"]'));
      tipTriggers.forEach(el => new bootstrap.Tooltip(el));
    });
  }

  // ─── PerfectScrollbar ────────────────────────────────────────────────────────
  if (kanbanWrapper) new PerfectScrollbar(kanbanWrapper);

  // ─── Add New Board toggle ────────────────────────────────────────────────────
  const kanbanContainer = document.querySelector('.kanban-container');

  if (kanbanAddBoardBtn) {
    kanbanAddBoardBtn.addEventListener('click', () => {
      kanbanAddNewInput.forEach(el => { el.value = ''; el.classList.toggle('d-none'); });
    });
  }

  if (kanbanContainer) kanbanContainer.appendChild(kanbanAddNewBoard);

  // Rename board
  function attachRenameEvents() {
    const renameBtns = [].slice.call(document.querySelectorAll('.rename-board'));
    renameBtns.forEach(btn => {
      btn.replaceWith(btn.cloneNode(true));
    });
    [].slice.call(document.querySelectorAll('.rename-board')).forEach(btn => {
      btn.addEventListener('click', async function () {
        const boardEl = this.closest('.kanban-board');
        const boardId = boardEl ? boardEl.getAttribute('data-id') : null;
        const titleEl = boardEl ? boardEl.querySelector('.kanban-title-board') : null;
        if (!boardId || !titleEl) return;
        const newTitle = prompt('Nama board baru:', titleEl.textContent.trim());
        if (!newTitle || !newTitle.trim()) return;
        try {
          await apiPut(`/api/kanban/boards/${boardId}/`, { title: newTitle.trim() });
          titleEl.textContent = newTitle.trim();
          const b = boardsData.find(b => b.id === boardId);
          if (b) b.title = newTitle.trim();
        } catch (err) {
          alert('Gagal rename board: ' + err.message);
        }
      });
    });
  }

  // Delete board
  function attachDeleteBoardEvents() {
    const deleteBtns = [].slice.call(document.querySelectorAll('.delete-board'));
    deleteBtns.forEach(btn => { btn.replaceWith(btn.cloneNode(true)); });
    [].slice.call(document.querySelectorAll('.delete-board')).forEach(btn => {
      btn.addEventListener('click', async function () {
        const boardEl = this.closest('.kanban-board');
        const boardId = boardEl ? boardEl.getAttribute('data-id') : null;
        if (!boardId) return;
        if (!confirm('Hapus board beserta semua tasknya?')) return;
        try {
          await apiDelete(`/api/kanban/boards/${boardId}/`);
          boardsData = boardsData.filter(b => b.id !== boardId);
          kanban.removeBoard(boardId);
        } catch (err) {
          alert('Gagal hapus board: ' + err.message);
        }
      });
    });
  }

  // Pasang dropdown dan editability ke semua title board yang sudah dirender
  function setupBoardTitles() {
    const kanbanTitleBoards = [].slice.call(document.querySelectorAll('.kanban-title-board'));
    kanbanTitleBoards.forEach(function (elem) {
      elem.addEventListener('mouseenter', function () { this.contentEditable = 'true'; });
      // blur → rename
      elem.addEventListener('blur', async function () {
        const boardEl = this.closest('.kanban-board');
        const boardId = boardEl ? boardEl.getAttribute('data-id') : null;
        const newTitle = this.textContent.trim();
        if (!boardId || !newTitle) return;
        const board = boardsData.find(b => b.id === boardId);
        if (board && board.title !== newTitle) {
          try {
            await apiPut(`/api/kanban/boards/${boardId}/`, { title: newTitle });
            board.title = newTitle;
          } catch (err) {
            console.error('Gagal rename board:', err);
          }
        }
        this.contentEditable = 'false';
      });
      if (!elem.nextElementSibling || !elem.nextElementSibling.classList.contains('dropdown')) {
        elem.insertAdjacentHTML('afterend', renderBoardDropdown());
      }
    });
    attachDeleteBoardEvents();
    attachRenameEvents();
  }

  setupBoardTitles();

  // ─── Add New Board Form submit ───────────────────────────────────────────────
  if (kanbanAddNewBoard) {
    kanbanAddNewBoard.addEventListener('submit', async function (e) {
      e.preventDefault();
      const title = this.querySelector('.form-control').value.trim();
      if (!title) return;

      try {
        const newBoard = await apiPost('/api/kanban/boards/', { title });
        boardsData.push({ ...newBoard, tasks: [] });

        kanban.addBoards([{ id: newBoard.id, title: newBoard.title }]);

        // Setup title & dropdown untuk board baru
        const lastBoard = document.querySelector('.kanban-board:last-child');
        if (lastBoard) {
          const header = lastBoard.querySelector('.kanban-title-board');
          if (header && (!header.nextElementSibling || !header.nextElementSibling.classList.contains('dropdown'))) {
            header.insertAdjacentHTML('afterend', renderBoardDropdown());
          }
          header && header.addEventListener('mouseenter', function () { this.contentEditable = 'true'; });
          header && header.addEventListener('blur', async function () {
            const boardId2 = lastBoard.getAttribute('data-id');
            const nt = this.textContent.trim();
            const b = boardsData.find(b => b.id === boardId2);
            if (b && b.title !== nt && nt) {
              try { await apiPut(`/api/kanban/boards/${boardId2}/`, { title: nt }); b.title = nt; }
              catch (err) { console.error(err); }
            }
            this.contentEditable = 'false';
          });
        }
        attachDeleteBoardEvents();
        attachRenameEvents();

        // Hide input
        kanbanAddNewInput.forEach(el => el.classList.add('d-none'));
        if (kanbanContainer) kanbanContainer.appendChild(kanbanAddNewBoard);
      } catch (err) {
        console.error('Gagal tambah board:', err);
        alert('Gagal membuat board: ' + err.message);
      }
    });
  }

  // ─── Cancel add board ────────────────────────────────────────────────────────
  const cancelAddNew = document.querySelector('.kanban-add-board-cancel-btn');
  if (cancelAddNew) {
    cancelAddNew.addEventListener('click', function () {
      kanbanAddNewInput.forEach(el => el.classList.toggle('d-none'));
    });
  }

})();