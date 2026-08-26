export function eventTypeOf(event) {
  return event?.eventType || event?.event_type || ''
}

export function eventTimeOf(event) {
  const explicit = event?.eventTime || event?.event_time
  if (explicit) return String(explicit).slice(0, 5)
  const at = event?.eventAt || event?.event_at
  if (!at) return ''
  const match = String(at).match(/T(\d{2}:\d{2})/)
  return match ? match[1] : ''
}

export function eventDateOf(event) {
  const explicit = event?.eventDate || event?.event_date
  if (explicit) return String(explicit).slice(0, 10)
  const at = event?.eventAt || event?.event_at
  if (!at) return ''
  return String(at).slice(0, 10)
}

function eventIdOf(event) {
  return Number(event?.id || 0)
}

function eventInstant(event) {
  const at = event?.eventAt || event?.event_at
  if (at) {
    const parsed = Date.parse(at)
    if (!Number.isNaN(parsed)) return parsed
  }
  const date = eventDateOf(event)
  const time = eventTimeOf(event) || '00:00'
  if (!date) return eventIdOf(event)
  const parsed = Date.parse(`${date}T${time}:00`)
  return Number.isNaN(parsed) ? eventIdOf(event) : parsed
}

export function compareEvents(left, right) {
  const delta = eventInstant(left) - eventInstant(right)
  if (delta) return delta
  return eventIdOf(left) - eventIdOf(right)
}

export function pairEvents(events) {
  const sorted = [...(events || [])].sort(compareEvents)
  const pairs = []
  let pendingIn = null
  for (const event of sorted) {
    if (eventTypeOf(event) === 'in') {
      if (pendingIn) pairs.push({ inEvent: pendingIn, outEvent: null })
      pendingIn = event
    } else {
      pairs.push({ inEvent: pendingIn, outEvent: event })
      pendingIn = null
    }
  }
  if (pendingIn) pairs.push({ inEvent: pendingIn, outEvent: null })
  return pairs
}

function personMeta(event) {
  return {
    userId: String(event.userId ?? event.user_id ?? ''),
    userName: event.userName || event.user_name || 'بدون نام',
    userRole: event.userRole || event.user_role || '',
    userDepartment: event.userDepartment || event.user_department || '',
    userPhone: event.userPhone || event.user_phone || '',
    userAvatar: event.userAvatar || event.user_avatar || event.avatar || '',
    userAvatarUrl: event.userAvatarUrl || event.user_avatar_url || event.avatarUrl || event.avatar_url || '',
    avatarUrl: event.userAvatarUrl || event.user_avatar_url || event.avatarUrl || event.avatar_url || '',
  }
}

export function computeWorkedMinutes(events) {
  const sorted = [...(events || [])].sort(compareEvents)
  let openIn = null
  let total = 0
  for (const event of sorted) {
    const instant = eventInstant(event)
    if (eventTypeOf(event) === 'in') {
      openIn = instant
    } else if (openIn != null) {
      total += Math.max(0, instant - openIn)
      openIn = null
    }
  }
  return Math.round(total / 60000)
}

export function groupEventsByPerson(events) {
  const map = new Map()
  for (const event of events || []) {
    const meta = personMeta(event)
    const userId = meta.userId || `event-${event?.id || map.size}`
    if (!map.has(userId)) {
      map.set(userId, { ...meta, userId, events: [] })
    }
    map.get(userId).events.push(event)
  }

  return [...map.values()]
    .map((person) => {
      const sorted = [...person.events].sort(compareEvents)
      const last = sorted[sorted.length - 1]
      const days = new Set(sorted.map((event) => eventDateOf(event)).filter(Boolean))
      return {
        ...person,
        events: sorted,
        checkins: sorted.filter((event) => eventTypeOf(event) === 'in').length,
        checkouts: sorted.filter((event) => eventTypeOf(event) === 'out').length,
        presentDays: days.size,
        workedMinutes: computeWorkedMinutes(sorted),
        hasOpenShift: Boolean(last && eventTypeOf(last) === 'in'),
      }
    })
    .sort((left, right) => String(left.userName).localeCompare(String(right.userName), 'fa'))
}

export function buildTodayPairs(events) {
  return groupEventsByPerson(events)
    .flatMap((person) =>
      pairEvents(person.events).map((pair) => {
        const sample = pair.inEvent || pair.outEvent
        return {
          id: `${person.userId}-${pair.inEvent?.id || 'x'}-${pair.outEvent?.id || 'x'}`,
          ...personMeta(sample || person),
          inEvent: pair.inEvent,
          outEvent: pair.outEvent,
          sortAt: eventInstant(pair.inEvent || pair.outEvent),
        }
      }),
    )
    .sort((left, right) => left.sortAt - right.sortAt)
}

export function groupPersonDays(events) {
  const byDate = new Map()
  for (const event of [...(events || [])].sort(compareEvents)) {
    const date = eventDateOf(event)
    if (!date) continue
    if (!byDate.has(date)) byDate.set(date, [])
    byDate.get(date).push(event)
  }
  return [...byDate.entries()].map(([date, dayEvents]) => {
    const last = dayEvents[dayEvents.length - 1]
    return {
      date,
      pairs: pairEvents(dayEvents),
      eventCount: dayEvents.length,
      workedMinutes: computeWorkedMinutes(dayEvents),
      hasOpenShift: Boolean(last && eventTypeOf(last) === 'in'),
    }
  })
}

export function applyTimeToEvent(event, time) {
  const nextTime = String(time || '').slice(0, 5)
  const date = eventDateOf(event)
  return {
    ...event,
    eventTime: nextTime,
    event_time: nextTime,
    eventAt: date ? `${date}T${nextTime}:00` : event.eventAt,
    event_at: date ? `${date}T${nextTime}:00` : event.event_at,
  }
}
