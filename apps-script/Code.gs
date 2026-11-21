/**
 * Technion Rocket Club – recruitment backend (Google Apps Script + Google Sheets)
 *
 * Setup (5 minutes):
 *  1. Create a new Google Sheet (e.g. "TRC Leads"), then Extensions → Apps Script.
 *  2. Paste this file as Code.gs and save.
 *  3. Project Settings → Script Properties → add:
 *       ADMIN_PASSWORD = <the team password>
 *       NOTIFY_EMAIL   = technion.rocketry@gmail.com   (optional – email on every new lead)
 *  4. Deploy → New deployment → type "Web app":
 *       Execute as: Me   ·   Who has access: Anyone
 *  5. Copy the /exec URL into CONFIG.APPS_SCRIPT_URL in index.html.
 */

// Spreadsheet that stores the leads (needed when the script is a standalone project).
const SPREADSHEET_ID = '15GXF_dXaexAKizjsQ-ybrr21LWiypG-ETceO1SSQz9w';
const SHEET_NAME = 'Leads';
const HEADERS = ['id', 'createdAt', 'name', 'email', 'phone', 'faculty', 'year', 'teams',
                 'hours', 'experience', 'why', 'source', 'status'];
const STATUSES = ['new', 'contacted', 'joined', 'inactive'];

function sheet_() {
  const ss = SPREADSHEET_ID ? SpreadsheetApp.openById(SPREADSHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
    sh.setRightToLeft(true);
  }
  return sh;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function clean_(v, max) {
  v = v == null ? '' : String(v);
  // stop spreadsheet formula injection
  if (/^[=+\-@]/.test(v)) v = "'" + v;
  return v.slice(0, max || 300);
}

function checkPassword_(pw) {
  const real = PropertiesService.getScriptProperties().getProperty('ADMIN_PASSWORD');
  if (!real || pw !== real) {
    Utilities.sleep(800); // slow down guessing
    throw new Error('unauthorized');
  }
}

function doGet() {
  return json_({ ok: true, service: 'trc-leads' });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    const body = JSON.parse(e.postData.contents || '{}');
    const sh = sheet_();

    if (body.action === 'register') {
      const l = body.lead || {};
      if (!l.name || !/^\S+@\S+\.\S+$/.test(l.email || '')) return json_({ ok: false, error: 'invalid' });
      // light rate limit: max 30 registrations per 10 minutes overall
      const cache = CacheService.getScriptCache();
      const n = Number(cache.get('rl') || 0);
      if (n > 30) return json_({ ok: false, error: 'busy' });
      cache.put('rl', String(n + 1), 600);

      lock.waitLock(10000);
      const id = Utilities.getUuid().slice(0, 8);
      const teams = Array.isArray(l.teams) ? l.teams.join(', ') : l.teams;
      sh.appendRow([id, new Date().toISOString(), clean_(l.name, 120), clean_(l.email, 160),
        clean_(l.phone, 40), clean_(l.faculty, 80), clean_(l.year, 40), clean_(teams, 300),
        clean_(l.hours, 20), clean_(l.experience, 500), clean_(l.why, 1000), clean_(l.source, 60), 'new']);

      const to = PropertiesService.getScriptProperties().getProperty('NOTIFY_EMAIL');
      if (to) {
        MailApp.sendEmail(to, 'TRC – נרשם/ת חדש/ה: ' + l.name,
          [l.name, l.email, l.phone, l.faculty, l.year, teams, l.why].filter(Boolean).join('\n'));
      }
      return json_({ ok: true, id: id });
    }

    if (body.action === 'list') {
      checkPassword_(body.password);
      const values = sh.getDataRange().getValues();
      const head = values.shift();
      const leads = values.map(r => {
        const o = {};
        head.forEach((h, i) => o[h] = r[i] instanceof Date ? r[i].toISOString() : r[i]);
        return o;
      });
      return json_({ ok: true, leads: leads });
    }

    if (body.action === 'status') {
      checkPassword_(body.password);
      if (STATUSES.indexOf(body.status) < 0) return json_({ ok: false, error: 'bad status' });
      lock.waitLock(10000);
      const ids = sh.getRange(2, 1, Math.max(sh.getLastRow() - 1, 1), 1).getValues().map(r => String(r[0]));
      const i = ids.indexOf(String(body.id));
      if (i < 0) return json_({ ok: false, error: 'not found' });
      sh.getRange(i + 2, HEADERS.indexOf('status') + 1).setValue(body.status);
      return json_({ ok: true });
    }

    return json_({ ok: false, error: 'unknown action' });
  } catch (err) {
    return json_({ ok: false, error: String(err.message || err) });
  } finally {
    try { lock.releaseLock(); } catch (e) {}
  }
}
