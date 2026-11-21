# אתר הגיוס של המועדון הרקטי בטכניון

אתר בעמוד אחד (`index.html`) עם היסטוריה, הצוותים, תחרות מרקיעים, השוואה למועדונים בעולם, פיד חדשות שמתעדכן אוטומטית, טופס הרשמה ואזור צוות מוגן בסיסמה.

## מה יש בתיקייה

| קובץ | תפקיד |
|---|---|
| `index.html` | האתר עצמו. אין צורך בבנייה: מעלים אותו וזהו. |
| `feed.json` | פיד החדשות שהאתר טוען. GitHub Action בונה אותו מחדש כל 6 שעות. |
| `feed-manual.json` | פריטים שכתבתם בעברית. הם תמיד נשארים בראש הפיד. |
| `scripts/update_feed.py` | הסקריפט שאוסף חדשות מ-SpaceNews, NASASpaceflight, European Spaceflight, Space.com, ESA ו-arXiv (מנועים היברידיים ומוצקים, משגרים, טילי שיוט, ראמג'ט). |
| `.github/workflows/feed.yml` | מריץ את הסקריפט אוטומטית. |
| `apps-script/Code.gs` | צד השרת של הטופס: שומר נרשמים בגיליון Google ובודק את סיסמת הצוות. |

## העלאה לאוויר (כ-15 דקות, בחינם)

### 1. גיליון הנרשמים (Google Sheets)
1. פתחו גיליון חדש בחשבון של המועדון, ואז **Extensions → Apps Script**.
2. הדביקו את `apps-script/Code.gs` ושמרו.
3. **Project Settings → Script Properties** והוסיפו:
   - `ADMIN_PASSWORD` – סיסמת הצוות.
   - `NOTIFY_EMAIL` – (רשות) כתובת שתקבל מייל על כל נרשם חדש.
4. **Deploy → New deployment → Web app**, עם *Execute as: Me* ו-*Who has access: Anyone*. אשרו את ההרשאות.
5. העתיקו את כתובת ה-`/exec`.

### 2. חיבור האתר
ב-`index.html`, בראש ה-`<script>`:
```js
APPS_SCRIPT_URL: "https://script.google.com/macros/s/XXXX/exec",
ADMIN_HASH: "..."   // SHA-256 של אותה סיסמה
```
לחישוב ה-hash: `echo -n 'הסיסמה' | sha256sum` (או כל מחשבון SHA-256).
הסיסמה הזמנית כרגע היא **Markiim-2027**. החליפו אותה לפני שמפרסמים.

### 3. אירוח (GitHub Pages)
1. צרו מאגר חדש ב-GitHub (למשל `technion-rocketry.github.io`) והעלו את כל התיקייה.
2. **Settings → Pages → Deploy from branch → main / root**.
3. **Settings → Actions → General → Workflow permissions → Read and write**, כדי שהפיד יוכל להתעדכן.
4. ב-**Actions** הריצו פעם אחת ידנית את *Update rocketry feed*.

אפשר לחבר דומיין משלכם, או לבקש מהפקולטה להפנות אליו קישור.

## האבטחה בקצרה
- הנרשמים נשמרים רק בגיליון של המועדון. בדפדפן הם לא נשמרים.
- רשימת הנרשמים נשלחת רק אחרי שהשרת (Apps Script) בודק את הסיסמה. ה-hash באתר הוא רק שער ראשון.
- יש בטופס "מלכודת" לבוטים, הגבלת קצב ונטרול של נוסחאות בגיליון.
- כדי לתת גישה לחברי צוות, שתפו אותם בגיליון עצמו או תנו להם את הסיסמה.

## עדכון תוכן
- **פריט חדשות בעברית:** מוסיפים אותו ל-`feed-manual.json` עם השדות `title`, `summary`, `source`, `url`, `date` (YYYY-MM-DD) ו-`cats`. הקטגוריות האפשריות: `orbital`, `launch`, `academic`, `missiles`, `student`.
- **אירועים קרובים:** המערך `ev` בתוך `index.html` (חפשו "next-up events").
- **ציר הזמן וטקסטים:** עורכים ישירות ב-`index.html`.

## השלב הבא: כלי עבודה לכל המועדון
האזור המוגן בנוי כך שאפשר להרחיב אותו: לכל נרשם יש סטטוס (חדש, נוצר קשר, הצטרף), ואפשר להוסיף לאותו Apps Script גם משימות, נוכחות בהרצאות או מלאי רכש, כל אחד בלשונית משלו בגיליון.
