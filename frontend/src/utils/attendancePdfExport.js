import { groupEventsByPerson, eventTypeOf, eventTimeOf, eventDateOf } from './attendanceReport'
import { personAvatarUrl, resolveAvatarUrl } from './avatar'
import { isoToJalali } from './jalali'

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function faDigits(value) {
  return String(value ?? '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[digit] || digit)
}

function eventLabel(type) {
  return type === 'in' ? 'ورود' : 'خروج'
}

function sourceLabel(source) {
  return source === 'manager' ? 'ثبت مدیر' : 'لینک پرسنل'
}

function formatHours(minutes) {
  const total = Math.max(0, Number(minutes) || 0)
  if (!total) return '۰'
  const hours = Math.floor(total / 60)
  const rest = total % 60
  if (!hours) return `${faDigits(rest)} دقیقه`
  if (!rest) return `${faDigits(hours)} ساعت`
  return `${faDigits(hours)}:${faDigits(String(rest).padStart(2, '0'))}`
}

function personAvatar(person) {
  return resolveAvatarUrl(
    personAvatarUrl(person),
    person.userAvatarUrl,
    person.user_avatar_url,
    person.avatarUrl,
    person.avatar_url,
  )
}

function initials(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '؟'
  return parts.slice(0, 2).map((part) => part[0]).join('')
}

/**
 * Printable PDF for attendance reports — includes profile photo, name, and job title (سمت).
 */
export function exportAttendanceReportPdf({
  events = [],
  title = 'گزارش ورود و خروج',
  subtitle = '',
  organizationName = 'کارنومند',
} = {}) {
  const people = groupEventsByPerson(events)
  if (!people.length) return false

  const peopleHtml = people.map((person) => {
    const avatar = personAvatar(person)
    const role = person.userRole || person.role || '—'
    const department = person.userDepartment || person.department || '—'
    const rows = (person.events || []).map((event, index) => {
      const dateIso = eventDateOf(event)
      return `
        <tr>
          <td>${faDigits(index + 1)}</td>
          <td>${escapeHtml(eventLabel(eventTypeOf(event)))}</td>
          <td>${faDigits(dateIso ? isoToJalali(dateIso) || dateIso : '—')}</td>
          <td dir="ltr">${faDigits(eventTimeOf(event) || '—')}</td>
          <td>${escapeHtml(sourceLabel(event.source))}</td>
          <td>${escapeHtml(event.note || '—')}</td>
        </tr>
      `
    }).join('')

    return `
      <section class="person-card">
        <header class="person-head">
          <div class="avatar-wrap">
            ${avatar
              ? `<img class="avatar" src="${escapeHtml(avatar)}" alt="" />`
              : `<div class="avatar avatar-fallback">${escapeHtml(initials(person.userName))}</div>`}
          </div>
          <div class="person-meta">
            <h2>${escapeHtml(person.userName || 'بدون نام')}</h2>
            <p><span>سمت:</span> ${escapeHtml(role)}</p>
            <p><span>بخش:</span> ${escapeHtml(department)}</p>
            <p class="muted">${faDigits(person.checkins || 0)} ورود · ${faDigits(person.checkouts || 0)} خروج · کارکرد ${escapeHtml(formatHours(person.workedMinutes))}</p>
          </div>
        </header>
        <table>
          <thead>
            <tr>
              <th>ردیف</th>
              <th>نوع</th>
              <th>تاریخ</th>
              <th>ساعت</th>
              <th>منبع</th>
              <th>یادداشت</th>
            </tr>
          </thead>
          <tbody>${rows || `<tr><td colspan="6">رویدادی ثبت نشده است.</td></tr>`}</tbody>
        </table>
      </section>
    `
  }).join('')

  const html = `<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(title)}</title>
  <style>
    @page { size: A4; margin: 14mm; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: #163532;
      font-family: Tahoma, "Segoe UI", Vazirmatn, sans-serif;
      background: #fff;
      font-size: 12px;
      line-height: 1.6;
    }
    .doc-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      padding-bottom: 14px;
      margin-bottom: 18px;
      border-bottom: 2px solid #34908b;
    }
    .doc-head h1 { margin: 0 0 6px; font-size: 18px; }
    .doc-head p { margin: 0; color: #4d6662; }
    .brand { font-weight: 800; color: #1f5c59; }
    .person-card {
      break-inside: avoid;
      page-break-inside: avoid;
      margin-bottom: 18px;
      padding: 14px;
      border: 1px solid #d7e8e5;
      border-radius: 14px;
      background: #f8fcfb;
    }
    .person-head {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }
    .avatar-wrap { flex: 0 0 auto; }
    .avatar {
      width: 64px;
      height: 64px;
      border-radius: 16px;
      object-fit: cover;
      border: 2px solid #fff;
      box-shadow: 0 0 0 1px #cfe3df;
      display: block;
      background: #dcefec;
    }
    .avatar-fallback {
      display: grid;
      place-items: center;
      font-weight: 800;
      color: #1f5c59;
      font-size: 18px;
    }
    .person-meta h2 { margin: 0 0 4px; font-size: 15px; }
    .person-meta p { margin: 0; }
    .person-meta span { color: #607874; font-weight: 700; }
    .person-meta .muted { margin-top: 4px; color: #607874; font-size: 11px; }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td {
      border: 1px solid #d7e8e5;
      padding: 7px 8px;
      text-align: right;
      vertical-align: top;
    }
    th { background: #e8f4f2; color: #1f5c59; font-size: 11px; }
    @media print {
      .no-print { display: none !important; }
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  <header class="doc-head">
    <div>
      <h1>${escapeHtml(title)}</h1>
      <p>${escapeHtml(subtitle || 'خروجی گزارش حضور و غیاب')}</p>
    </div>
    <div class="brand">${escapeHtml(organizationName)}</div>
  </header>
  ${peopleHtml}
  <script>
    window.addEventListener('load', () => {
      setTimeout(() => { window.focus(); window.print(); }, 250);
    });
  </script>
</body>
</html>`

  const popup = window.open('', '_blank', 'noopener,noreferrer,width=960,height=720')
  if (!popup) return false
  popup.document.open()
  popup.document.write(html)
  popup.document.close()
  return true
}
