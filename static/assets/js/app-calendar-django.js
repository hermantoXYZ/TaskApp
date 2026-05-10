/**
 * App Calendar - Django Integration
 * Menggantikan app-calendar-events.js dengan fetch ke Django API
 */

'use strict';

// Ambil CSRF Token dari cookie Django
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const CSRF_TOKEN = getCookie('csrftoken');
const API_BASE = '/api/calendar/events/';

// --------------------------------------------------------
// TOAST NOTIFICATION (global agar bisa dipanggil dari HTML onclick)
// --------------------------------------------------------
let _toastTimer = null;

window.showCalendarToast = function (msg, type) {
  // type: 'success' | 'danger' | 'warning'
  const toast = document.getElementById('calendarToast');
  const toastMsg = document.getElementById('calendarToastMsg');
  const toastIcon = document.getElementById('calendarToastIcon');
  if (!toast) return;

  // Reset semua class warna lama
  toast.className = '';
  ['toast-success', 'toast-danger', 'toast-warning', 'show', 'hiding'].forEach(c => toast.classList.remove(c));

  // Terapkan class warna baru
  toast.classList.add('show', 'toast-' + (type || 'success'));

  // Icon sesuai tipe
  const icons = {
    success: 'ri-checkbox-circle-line',
    danger: 'ri-close-circle-line',
    warning: 'ri-error-warning-line'
  };
  toastIcon.className = 'toast-icon ' + (icons[type] || icons.success);
  toastMsg.textContent = msg;

  // Auto-hide setelah 3.5 detik
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => window.hideCalendarToast(), 3500);
};

window.hideCalendarToast = function () {
  const toast = document.getElementById('calendarToast');
  if (!toast) return;
  toast.classList.add('hiding');
  setTimeout(() => {
    toast.className = '';
  }, 380);
};

let direction = 'ltr';
if (typeof isRtl !== 'undefined' && isRtl) {
  direction = 'rtl';
}

document.addEventListener('DOMContentLoaded', function () {
  (function () {
    const calendarEl = document.getElementById('calendar'),
      appCalendarSidebar = document.querySelector('.app-calendar-sidebar'),
      addEventSidebar = document.getElementById('addEventSidebar'),
      appOverlay = document.querySelector('.app-overlay'),
      calendarsColor = {
        Campus: 'primary',
        Business: 'secondary',
        Personal: 'danger',
        Family: 'warning',
        Holiday: 'success',
        Finance: 'info',
        'Self-Dev': 'dark',
        'Health & Fitness': 'success',
        Lainnya: 'secondary'
      },
      offcanvasTitle = document.querySelector('.offcanvas-title'),
      btnToggleSidebar = document.querySelector('.btn-toggle-sidebar'),
      btnSubmit = document.querySelector('#addEventBtn'),
      btnCancel = document.querySelector('.btn-cancel'),
      eventTitle = document.querySelector('#eventTitle'),
      eventStartDate = document.querySelector('#eventStartDate'),
      eventEndDate = document.querySelector('#eventEndDate'),
      eventUrl = document.querySelector('#eventURL'),
      eventLabel = $('#eventLabel'),
      eventLocation = document.querySelector('#eventLocation'),
      eventDescription = document.querySelector('#eventDescription'),
      allDaySwitch = document.querySelector('.allDay-switch'),
      selectAll = document.querySelector('.select-all'),
      filterInput = [].slice.call(document.querySelectorAll('.input-filter')),
      inlineCalendar = document.querySelector('.inline-calendar'),
      // Detail panel elements
      eventDetailPanel = document.getElementById('eventDetailPanel'),
      eventFormPanel = document.querySelector('.event-form-panel'),
      detailTitle = document.getElementById('detailTitle'),
      detailBadge = document.getElementById('detailBadge'),
      detailStart = document.getElementById('detailStart'),
      detailEnd = document.getElementById('detailEnd'),
      detailEndRow = document.getElementById('detailEndRow'),
      detailLabel = document.getElementById('detailLabel'),
      detailLocation = document.getElementById('detailLocation'),
      detailLocationRow = document.getElementById('detailLocationRow'),
      detailDesc = document.getElementById('detailDesc'),
      detailDescRow = document.getElementById('detailDescRow'),
      detailUrl = document.getElementById('detailUrl'),
      detailUrlRow = document.getElementById('detailUrlRow'),
      btnEditEvent = document.querySelector('.btn-edit-event'),
      btnDeleteEventDetail = document.querySelector('.btn-delete-event-detail');

    let eventToUpdate,
      isFormValid = false,
      inlineCalInstance;

    // --------------------------------------------------------
    // PANEL TOGGLE HELPERS
    // --------------------------------------------------------
    const calendarsColorHex = {
      Campus: '#7367f0',
      Business: '#6e6b7b',
      Personal: '#ea5455',
      Family: '#ff9f43',
      Holiday: '#28c76f',
      Finance: '#00cfe8',
      'Self-Dev': '#e83e8c',
      'Health & Fitness': '#20c997',
      Lainnya: '#858585'
    };

    function formatDate(d) {
      if (!d) return '-';
      return moment(d).format('dddd, D MMMM YYYY HH:mm');
    }

    function showDetailPanel(ev) {
      // Populate detail fields
      detailTitle.textContent = ev.title || '-';
      const calLabel = ev.extendedProps.calendar || 'Business';
      detailBadge.style.backgroundColor = calendarsColorHex[calLabel] || '#7367f0';
      detailLabel.textContent = calLabel;
      detailStart.textContent = formatDate(ev.start);

      if (ev.end && ev.end.getTime() !== ev.start.getTime()) {
        detailEnd.textContent = formatDate(ev.end);
        detailEndRow.style.display = 'flex';
      } else {
        detailEndRow.style.display = 'none';
      }

      const loc = ev.extendedProps.location;
      if (loc) {
        detailLocation.textContent = loc;
        detailLocationRow.style.display = 'flex';
      } else {
        detailLocationRow.style.display = 'none';
      }

      const desc = ev.extendedProps.description;
      if (desc) {
        detailDesc.textContent = desc;
        detailDescRow.style.display = 'flex';
      } else {
        detailDescRow.style.display = 'none';
      }

      if (ev.url) {
        detailUrl.textContent = ev.url;
        detailUrl.href = ev.url;
        detailUrlRow.style.display = 'flex';
      } else {
        detailUrlRow.style.display = 'none';
      }

      // Show detail, hide form
      eventDetailPanel.classList.add('show');
      eventFormPanel.classList.add('d-none');
      if (offcanvasTitle) offcanvasTitle.innerHTML = 'Detail Agenda';
    }

    function showFormPanel(mode) {
      // mode: 'add' | 'update'
      eventDetailPanel.classList.remove('show');
      eventFormPanel.classList.remove('d-none');
      if (mode === 'add') {
        if (offcanvasTitle) offcanvasTitle.innerHTML = 'Add To Do List';
        btnSubmit.innerHTML = 'Add';
        btnSubmit.classList.remove('btn-update-event');
        btnSubmit.classList.add('btn-add-event');
      } else {
        if (offcanvasTitle) offcanvasTitle.innerHTML = 'Update Agenda';
        btnSubmit.innerHTML = 'Update';
        btnSubmit.classList.add('btn-update-event');
        btnSubmit.classList.remove('btn-add-event');
      }
    }

    // Init Offcanvas Bootstrap
    const bsAddEventSidebar = new bootstrap.Offcanvas(addEventSidebar);

    // --------------------------------------------------------
    // SELECT2: Event Label
    // --------------------------------------------------------
    if (eventLabel.length) {
      function renderBadges(option) {
        if (!option.id) return option.text;
        return "<span class='badge badge-dot bg-" + $(option.element).data('label') + " me-2'> </span>" + option.text;
      }
      select2Focus(eventLabel);
      eventLabel.wrap('<div class="position-relative"></div>').select2({
        placeholder: 'Select value',
        dropdownParent: eventLabel.parent(),
        templateResult: renderBadges,
        templateSelection: renderBadges,
        minimumResultsForSearch: -1,
        escapeMarkup: function (es) { return es; }
      });
    }


    // --------------------------------------------------------
    // FLATPICKR
    // --------------------------------------------------------
    let fpStart, fpEnd;
    if (eventStartDate) {
      fpStart = eventStartDate.flatpickr({
        enableTime: true,
        dateFormat: 'Y-m-d H:i',
        onReady: function (selectedDates, dateStr, instance) {
          if (instance.isMobile) instance.mobileInput.setAttribute('step', null);
        }
      });
    }
    if (eventEndDate) {
      fpEnd = eventEndDate.flatpickr({
        enableTime: true,
        dateFormat: 'Y-m-d H:i',
        onReady: function (selectedDates, dateStr, instance) {
          if (instance.isMobile) instance.mobileInput.setAttribute('step', null);
        }
      });
    }
    if (inlineCalendar) {
      inlineCalInstance = inlineCalendar.flatpickr({
        monthSelectorType: 'static',
        inline: true
      });
    }

    // --------------------------------------------------------
    // FILTER: Kalender yang dipilih
    // --------------------------------------------------------
    function selectedCalendars() {
      let selected = [];
      document.querySelectorAll('.input-filter:checked').forEach(item => {
        selected.push(item.getAttribute('data-value'));
      });
      return selected;
    }

    // --------------------------------------------------------
    // FETCH EVENTS dari Django API
    // --------------------------------------------------------
    function fetchEvents(info, successCallback, failureCallback) {
      fetch(API_BASE, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(res => {
          if (!res.ok) throw new Error('Gagal memuat event');
          return res.json();
        })
        .then(data => {
          const calendars = selectedCalendars();
          const filtered = data.filter(ev =>
            calendars.includes(ev.extendedProps.calendar.toLowerCase())
          );
          successCallback(filtered);
        })
        .catch(err => {
          console.error('Calendar fetch error:', err);
          failureCallback(err);
        });
    }

    // --------------------------------------------------------
    // MODIFY SIDEBAR TOGGLER
    // --------------------------------------------------------
    function modifyToggler() {
      const fcSidebarToggleButton = document.querySelector('.fc-sidebarToggle-button');
      const fcPrevButton = document.querySelector('.fc-prev-button');
      const fcNextButton = document.querySelector('.fc-next-button');
      const fcHeaderToolbar = document.querySelector('.fc-header-toolbar');
      if (!fcSidebarToggleButton) return;
      fcPrevButton.classList.add('btn', 'btn-sm', 'btn-icon', 'btn-outline-secondary', 'me-2');
      fcNextButton.classList.add('btn', 'btn-sm', 'btn-icon', 'btn-outline-secondary', 'me-4');
      fcHeaderToolbar.classList.add('row-gap-4', 'gap-2');
      fcSidebarToggleButton.classList.remove('fc-button-primary');
      fcSidebarToggleButton.classList.add('d-lg-none', 'd-inline-block', 'ps-0');
      while (fcSidebarToggleButton.firstChild) fcSidebarToggleButton.firstChild.remove();
      fcSidebarToggleButton.setAttribute('data-bs-toggle', 'sidebar');
      fcSidebarToggleButton.setAttribute('data-overlay', '');
      fcSidebarToggleButton.setAttribute('data-target', '#app-calendar-sidebar');
      fcSidebarToggleButton.insertAdjacentHTML('beforeend', '<i class="ri-menu-line ri-24px text-body"></i>');
    }

    // --------------------------------------------------------
    // EVENT CLICK: tampilkan detail panel
    // --------------------------------------------------------
    function eventClick(info) {
      eventToUpdate = info.event;
      if (eventToUpdate.url) {
        info.jsEvent.preventDefault();
      }
      bsAddEventSidebar.show();
      showDetailPanel(eventToUpdate);

      if (eventToUpdate.extendedProps.is_readonly) {
        if (btnEditEvent) btnEditEvent.style.display = 'none';
        if (btnDeleteEventDetail) btnDeleteEventDetail.style.display = 'none';
      } else {
        if (btnEditEvent) btnEditEvent.style.display = '';
        if (btnDeleteEventDetail) btnDeleteEventDetail.style.display = '';
      }
    }

    // --------------------------------------------------------
    // INIT FULLCALENDAR
    // --------------------------------------------------------
    let calendar = new Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      events: fetchEvents,
      plugins: [dayGridPlugin, interactionPlugin, listPlugin, timegridPlugin],
      editable: true,
      dragScroll: true,
      dayMaxEvents: 2,
      eventResizableFromStart: true,
      customButtons: {
        sidebarToggle: { text: 'Sidebar' }
      },
      headerToolbar: {
        start: 'sidebarToggle, prev,next, title',
        end: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth'
      },
      direction: direction,
      initialDate: new Date(),
      navLinks: true,
      eventClassNames: function ({ event: calendarEvent }) {
        const colorName = calendarsColor[calendarEvent._def.extendedProps.calendar];
        return ['fc-event-' + colorName];
      },
      dateClick: function (info) {
        let date = moment(info.date).format('YYYY-MM-DD HH:mm');
        resetValues();
        bsAddEventSidebar.show();
        showFormPanel('add');
        fpStart.setDate(date, true);
        fpEnd.setDate(date, true);
      },
      eventClick: function (info) { eventClick(info); },
      datesSet: function () { modifyToggler(); },
      viewDidMount: function () { modifyToggler(); },
      // Drag & drop update
      eventDrop: function (info) {
        const ev = info.event;
        if (ev.extendedProps.is_readonly) {
          info.revert();
          showCalendarToast('Agenda kelas tidak dapat diubah dari sini.', 'warning');
          return;
        }
        updateEventAPI(ev.id, {
          title: ev.title,
          label: ev.extendedProps.calendar,
          start: ev.startStr,
          end: ev.endStr || ev.startStr,
          allDay: ev.allDay,
          url: ev.url || '',
          location: ev.extendedProps.location || '',
          description: ev.extendedProps.description || ''
        });
      },
      eventResize: function (info) {
        const ev = info.event;
        if (ev.extendedProps.is_readonly) {
          info.revert();
          showCalendarToast('Agenda kelas tidak dapat diubah dari sini.', 'warning');
          return;
        }
        updateEventAPI(ev.id, {
          title: ev.title,
          label: ev.extendedProps.calendar,
          start: ev.startStr,
          end: ev.endStr || ev.startStr,
          allDay: ev.allDay,
          url: ev.url || '',
          location: ev.extendedProps.location || '',
          description: ev.extendedProps.description || ''
        });
      }
    });

    calendar.render();
    modifyToggler();

    // --------------------------------------------------------
    // FORM VALIDATION
    // --------------------------------------------------------
    const eventForm = document.getElementById('eventForm');
    const fv = FormValidation.formValidation(eventForm, {
      fields: {
        eventTitle: {
          validators: { notEmpty: { message: 'Please enter event title' } }
        },
        eventStartDate: {
          validators: { notEmpty: { message: 'Please enter start date' } }
        },
        eventEndDate: {
          validators: { notEmpty: { message: 'Please enter end date' } }
        }
      },
      plugins: {
        trigger: new FormValidation.plugins.Trigger(),
        bootstrap5: new FormValidation.plugins.Bootstrap5({
          eleValidClass: '',
          rowSelector: function () { return '.mb-5'; }
        }),
        submitButton: new FormValidation.plugins.SubmitButton(),
        autoFocus: new FormValidation.plugins.AutoFocus()
      }
    })
      .on('core.form.valid', function () { isFormValid = true; })
      .on('core.form.invalid', function () { isFormValid = false; });

    // --------------------------------------------------------
    // API HELPERS
    // --------------------------------------------------------
    function buildPayload() {
      return {
        title: eventTitle.value,
        label: eventLabel.val(),
        start: eventStartDate.value,
        end: eventEndDate.value || eventStartDate.value,
        allDay: allDaySwitch.checked,
        url: eventUrl.value || '',
        location: eventLocation.value || '',
        description: eventDescription.value || ''
      };
    }

    function createEventAPI(payload) {
      return fetch(API_BASE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify(payload)
      }).then(res => res.json());
    }

    function updateEventAPI(id, payload) {
      return fetch(API_BASE + id + '/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify(payload)
      }).then(res => res.json());
    }

    function deleteEventAPI(id) {
      return fetch(API_BASE + id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': CSRF_TOKEN }
      }).then(res => {
        // DELETE biasanya return 204 No Content (tanpa body)
        if (res.status === 204 || res.status === 200) return Promise.resolve();
        return res.json();
      });
    }

    // --------------------------------------------------------
    // SUBMIT BUTTON (Add / Update)
    // --------------------------------------------------------
    btnSubmit.addEventListener('click', e => {
      if (btnSubmit.classList.contains('btn-add-event')) {
        if (isFormValid) {
          createEventAPI(buildPayload()).then(data => {
            calendar.refetchEvents();
            bsAddEventSidebar.hide();
            showCalendarToast('Agenda berhasil ditambahkan!', 'success');
          }).catch(err => console.error('Create error:', err));
        }
      } else {
        if (isFormValid) {
          updateEventAPI(eventToUpdate.id, buildPayload()).then(data => {
            calendar.refetchEvents();
            bsAddEventSidebar.hide();
            showCalendarToast('Agenda berhasil diperbarui!', 'success');
          }).catch(err => console.error('Update error:', err));
        }
      }
    });

    // --------------------------------------------------------
    // EDIT BUTTON (dari detail panel -> buka form update)
    // --------------------------------------------------------
    if (btnEditEvent) {
      btnEditEvent.addEventListener('click', () => {
        showFormPanel('update');
        // Isi form dengan data event
        eventTitle.value = eventToUpdate.title;
        fpStart.setDate(eventToUpdate.start, true);
        allDaySwitch.checked = !!eventToUpdate.allDay;
        eventToUpdate.end !== null
          ? fpEnd.setDate(eventToUpdate.end, true)
          : fpEnd.setDate(eventToUpdate.start, true);
        eventLabel.val(eventToUpdate.extendedProps.calendar).trigger('change');
        if (eventToUpdate.extendedProps.location) eventLocation.value = eventToUpdate.extendedProps.location;
        if (eventToUpdate.extendedProps.description) eventDescription.value = eventToUpdate.extendedProps.description;
        if (eventToUpdate.url) eventUrl.value = eventToUpdate.url;
      });
    }

    // --------------------------------------------------------
    // DELETE BUTTON (dari detail panel)
    // --------------------------------------------------------
    if (btnDeleteEventDetail) {
      btnDeleteEventDetail.addEventListener('click', () => {
        if (!confirm('Hapus agenda "' + eventToUpdate.title + '"?')) return;
        deleteEventAPI(eventToUpdate.id).then(() => {
          calendar.refetchEvents();
          bsAddEventSidebar.hide();
          showCalendarToast('Agenda berhasil dihapus.', 'danger');
        }).catch(err => console.error('Delete error:', err));
      });
    }

    // --------------------------------------------------------
    // RESET FORM
    // --------------------------------------------------------
    function resetValues() {
      eventTitle.value = '';
      eventUrl.value = '';
      eventLocation.value = '';
      eventDescription.value = '';
      allDaySwitch.checked = false;
      fpStart.clear();
      fpEnd.clear();
    }

    addEventSidebar.addEventListener('hidden.bs.offcanvas', function () {
      resetValues();
      eventDetailPanel.classList.remove('show');
      eventFormPanel.classList.remove('d-none');
      if (offcanvasTitle) offcanvasTitle.innerHTML = 'Add To Do List';
      btnSubmit.innerHTML = 'Add';
      btnSubmit.classList.remove('btn-update-event');
      btnSubmit.classList.add('btn-add-event');
    });

    // --------------------------------------------------------
    // SIDEBAR TOGGLE
    // --------------------------------------------------------
    if (btnToggleSidebar) {
      btnToggleSidebar.addEventListener('click', e => {
        resetValues();
        showFormPanel('add');
        appCalendarSidebar.classList.remove('show');
        appOverlay.classList.remove('show');
      });
    }

    // --------------------------------------------------------
    // FILTER CHECKBOXES
    // --------------------------------------------------------
    if (selectAll) {
      selectAll.addEventListener('click', e => {
        document.querySelectorAll('.input-filter').forEach(c => (c.checked = e.currentTarget.checked ? 1 : 0));
        calendar.refetchEvents();
      });
    }
    if (filterInput) {
      filterInput.forEach(item => {
        item.addEventListener('click', () => {
          const checked = document.querySelectorAll('.input-filter:checked').length;
          const total = document.querySelectorAll('.input-filter').length;
          selectAll.checked = checked === total;
          calendar.refetchEvents();
        });
      });
    }

    // --------------------------------------------------------
    // INLINE CALENDAR (sidebar flatpickr)
    // --------------------------------------------------------
    if (inlineCalInstance) {
      inlineCalInstance.config.onChange.push(function (date) {
        calendar.changeView(calendar.view.type, moment(date[0]).format('YYYY-MM-DD'));
        modifyToggler();
        appCalendarSidebar.classList.remove('show');
        appOverlay.classList.remove('show');
      });
    }
  })();
});
