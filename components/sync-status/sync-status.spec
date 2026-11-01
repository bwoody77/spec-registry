// SyncStatus — the small pill that says where an offline queue stands: a
// coloured dot and one short phrase.
//
// Born twice, in Vector (its charter pilot app, shop app and flight debrief)
// and in the avento shell header, as two copies that were 96% the same. One
// registry component now, so a fix to the pill reaches both (Vector #3539).
//
// States, checked in priority order (the rule is `syncPillState` below, a fn
// so it is unit-tested and emits to every target):
//   held > 0     → red    "{N} held"     the server refused a save; a person must act
//   pending > 0  → amber  "{N} waiting"  queued on this device, sends when it can
//   !known       → gray   "Checking…"    the caller has no status yet
//   !isOnline    → gray   "Offline"
//   otherwise    → green  "Synced"
//
// `held` outranks everything because a save the server refused is not resolved
// by getting signal back: it is the one state where the queue has stopped
// making progress on its own.
//
// A COUNT outranks "Offline". Being offline is already plain from the device
// and the screen; how many records are captured and NOT yet filed is the fact
// a user cannot otherwise recover. Showing "Offline" over "3 waiting" spends
// the one always-visible indicator on the thing they already know.
//
// "Checking…" sits under the two counts: a count a caller already has is a
// fact, and only Offline and Synced are claims an unanswered queue cannot
// back. `known` defaults to true, so a caller that always has its status
// never passes it; one that boots before its outbox answers passes false
// until the first status arrives (a green Synced over checks already queued on
// a cold start is the one wrong answer this pill must not give).
//
// The prop is `isOnline`, NOT `online`. An older compiler read any prop whose
// name started with "on" as an event handler and never subscribed to it, so a
// pill fed `online` kept its mount-time value forever. The compiler now needs
// an uppercase letter after "on" (/^on[A-Z]/ in ast-to-ir.ts), but every
// caller already passes `isOnline`, so the name stays.
//
// role=status, so a screen reader hears "2 waiting" when an edit queues and
// "Synced" when it files, without moving focus. `data-sync-state` carries the
// rung for tests and styling hooks that should not read the translated words.
//
// Deliberately NOT built on Badge: the dot is the affordance that makes this
// read as a connectivity indicator rather than as a record's status, and the
// ladder is state logic a generic badge has no place knowing.

fn syncPillState(known: boolean, isOnline: boolean, pending: number, held: number) -> string {
  if held > 0 { return 'held' }
  if pending > 0 { return 'waiting' }
  if !known { return 'checking' }
  if !isOnline { return 'offline' }
  return 'synced'
}

component SyncStatus(isOnline: boolean = true, pending: number = 0, held: number = 0, known: boolean = true) {
  @computed {
    state: syncPillState(known, isOnline, pending, held)
    hasHeld: state == 'held'
    hasPending: state == 'waiting'
    // Checking… and Offline share the neutral gray; only the words differ.
    isGray: state == 'checking' || state == 'offline'
    label: hasHeld ? t("{held} held") : hasPending ? t("{pending} waiting") : state == 'checking' ? t('Checking…') : state == 'offline' ? t('Offline') : t('Synced')
    pillBg: hasHeld ? semantic.destructive-bg : hasPending ? semantic.warning-bg : isGray ? semantic.surface-sunken : semantic.success-bg
    pillFg: hasHeld ? semantic.destructive-text : hasPending ? semantic.warning-text : isGray ? semantic.text-tertiary : semantic.success-text
    dotBg: hasHeld ? semantic.destructive : hasPending ? semantic.warning : isGray ? semantic.text-disabled : semantic.success
  }
  block {
    role: 'status'
    data-sync-state: state
    padding-x: 10px
    padding-y: 4px
    border-radius: 999px
    background: pillBg
    layout: horizontal, gap: 5px, align: center
    block {
      width: 6px
      height: 6px
      border-radius: 999px
      background: dotBg
    }
    text(label) { color: pillFg, style: type.label-sm-strong, letter-spacing: "0.02em" }
  }
}
