/**
 * i18n.js - interface language.
 *
 * One flat dictionary per language. Keys are dotted paths that mirror where
 * the string is used, so a missing translation is obvious in a diff rather
 * than hidden behind a helper.
 *
 * Two rules the rest of the app relies on:
 *
 *   1. `t()` never throws and never renders an empty box. A missing key falls
 *      back to English, then to the key itself. A half-translated build should
 *      degrade to readable, not to blank.
 *   2. Language is stored in the state store, not here. Views are pure
 *      functions of state, so switching language re-renders them for free -
 *      there is no separate "apply translations" pass to forget to call.
 *
 * Direction is handled at the document level (`dir="rtl"`), and the stylesheets
 * use logical properties, so no component knows which way the page runs. The
 * exceptions are deliberate: log lines, timestamps, evidence ids and code
 * blocks are pinned LTR, because a stack trace mirrored into RTL is unreadable.
 */

const EN = {
  /* --- chrome ------------------------------------------------------------ */
  "app.tagline": "Evidence-first incident analysis",
  "app.skipLink": "Skip to analysis results",
  "app.inputPanel": "Input panel",
  "app.inputPanel.title": "Show or hide the input panel",
  "app.theme.toLight": "Switch to light theme",
  "app.theme.toDark": "Switch to dark theme",
  "app.lang.title": "Switch interface language",
  "app.sidebar.aria": "Incident input",

  "step.1": "Load an incident",
  "step.2": "Evidence",
  "step.3": "Analyse",

  /* --- tabs -------------------------------------------------------------- */
  "tab.summary": "Summary",
  "tab.evidence": "Evidence",
  "tab.timeline": "Timeline",
  "tab.hypotheses": "Hypotheses",
  "tab.risks": "Reasoning risks",
  "tab.actions": "Next actions",
  "tab.report": "Postmortem",
  "tabs.aria": "Analysis sections",

  /* --- status bar -------------------------------------------------------- */
  "status.idle": "Ready — load a sample or paste evidence",
  "status.running": "Analysing…",
  "status.done": "Analysis complete",
  "status.error": "Failed: {error}",
  "status.grounding": "grounding {value}",
  "status.grounding.title":
    "Share of model claims that cite evidence actually present in the input",
  "status.model": "model {model}",

  "provider.notRun": "not run yet",
  "provider.offline": "offline engine",
  "provider.offline.title":
    "No language model was used. Only the deterministic engine produced this analysis.",
  "provider.online.title":
    "Model-assisted analysis, verified against the input evidence",

  /* --- input panel ------------------------------------------------------- */
  "input.title.label": "Incident title",
  "input.title.placeholder": "Checkout failures after v2.4.1",
  "input.chars": "{count} chars",
  "input.file": "file",
  "input.file.title": 'Load a file into "{label}"',

  "field.description.label": "Incident description",
  "field.description.placeholder": "What is failing, since when, and who noticed?",
  "field.description.help": "One or two sentences. This is context, not evidence.",
  "field.logs.label": "Application logs",
  "field.logs.placeholder": "2026-05-02T10:14:03Z ERROR checkout ...",
  "field.logs.help": "Paste raw lines. Timestamps are used to build the timeline.",
  "field.errors.label": "Error traces",
  "field.errors.placeholder": "Traceback (most recent call last): ...",
  "field.alerts.label": "Monitoring alerts",
  "field.alerts.placeholder": "[FIRING] CheckoutErrorRate > 5% for 10m",
  "field.deployNotes.label": "Recent deployment notes",
  "field.deployNotes.placeholder": "v2.4.1 - switched payment client to connection pooling",
  "field.deployNotes.help": "A deploy before an incident is a lead, not a cause.",
  "field.userReports.label": "User complaints / support tickets",
  "field.userReports.placeholder": '"Card declined at checkout" x14 since 10:20',

  /* --- samples ----------------------------------------------------------- */
  "samples.loading": "loading examples…",
  "samples.none": "No example incidents found in data/samples/.",
  "samples.loaded": 'Loaded "{title}"',

  /* --- run panel --------------------------------------------------------- */
  "run.devilsAdvocate": "Argue against the leading hypothesis",
  "run.devilsAdvocate.help": "Runs a second pass that tries to falsify the top answer.",
  "run.redact": "Redact emails, IPs and tokens before sending",
  "run.redact.help": "Nothing that looks like a secret leaves this machine.",
  "run.analyse": "Analyse incident",
  "run.analysing": "Analysing…",
  "run.cancel": "Cancel",
  "run.clear": "Clear everything",
  "run.shortcut": "from anywhere",
  "run.disclaimer":
    "IncidentIQ proposes hypotheses. It does not decide the root cause — run the " +
    "suggested test before you believe any of them.",
  "run.needInput": "Add some evidence first — a description or a few log lines.",
  "run.unsupportedToast":
    "{count} model claim(s) could not be traced to the input. See the Summary tab.",
  "run.offlineToast": "Ran in offline mode — no language model was consulted.",

  "progress.evidence": "Extracting evidence items",
  "progress.timeline": "Reconstructing the timeline",
  "progress.hypotheses": "Generating competing hypotheses",
  "progress.verify": "Checking claims against the evidence",
  "progress.risks": "Scanning for reasoning risks",

  /* --- shared ------------------------------------------------------------ */
  "empty.notRun": "No analysis yet",
  "empty.noEvidence": "no evidence cited",
  "evref.broken.title":
    "{id} does not exist in the input. The model invented this citation.",
  "evref.show": "Show this evidence",

  "band.wellSupported": "well supported",
  "band.plausible": "plausible",
  "band.weak": "weak",
  "band.speculative": "speculative",
  "band.unrated": "unrated",

  "source.description": "Incident description",
  "source.logs": "Application logs",
  "source.errors": "Error traces",
  "source.alerts": "Monitoring alerts",
  "source.deploy_notes": "Deployment notes",
  "source.user_reports": "User reports",

  /* --- summary view ------------------------------------------------------ */
  "summary.empty":
    "Load one of the example incidents from the sidebar, or paste your own logs, " +
    "then press Analyse incident.",
  "summary.failed": "Analysis failed",
  "summary.offline.title": "Offline mode",
  "summary.offline.body":
    "No language model was consulted. Everything below was produced by the " +
    "deterministic engine: pattern-matched evidence, a timestamp-ordered timeline, " +
    "and rule-based hypotheses. Add an API key in .env for the model-assisted analysis.",
  "summary.verified.title": "Every claim traced to evidence (grounding {value})",
  "summary.verified.body":
    "Each statement below cites at least one input item that exists. " +
    "Traceable is not the same as correct — the cited evidence may itself be misleading.",
  "summary.failedChecks.title": "{count} claim(s) failed verification (grounding {value})",
  "summary.invented": "Invented citations: ",
  "summary.invented.body": "the model cited {list}, which do not exist in the input.",
  "summary.unsupported": "Unsupported statements: ",
  "summary.unsupported.body": "{count} claim(s) cite no evidence at all.",
  "summary.what": "What happened",
  "summary.what.hint": "professional summary, no unsupported claims",
  "summary.noSummary": "No summary produced.",
  "summary.basedOn": "based on",
  "summary.factsVsAssumptions": "Facts vs assumptions",
  "summary.factsVsAssumptions.hint":
    "the two are kept apart on purpose — mixing them is how investigations go wrong",
  "summary.facts": "facts",
  "summary.facts.title": "Directly supported by the input",
  "summary.facts.none": "No statement in the analysis was fully grounded.",
  "summary.assumptions": "assumptions",
  "summary.assumptions.title": "Believed but not proven",
  "summary.assumptions.none": "No assumptions were flagged.",
  "summary.assumption.why": "Why we think so: {why}",
  "summary.assumption.verify": "To confirm: ",
  "summary.audiences": "Same facts, three audiences",
  "summary.audiences.hint": "the wording changes, the claims do not",
  "summary.audience.engineer": "For the on-call engineer",
  "summary.audience.manager": "For the engineering manager",
  "summary.audience.support": "For the support team",
  "summary.openQuestions": "Still unknown",
  "summary.openQuestions.hint":
    "questions that must be answered before closing this incident",

  /* --- evidence view ----------------------------------------------------- */
  "evidence.empty": "Once an analysis runs, every input line appears here with a stable ID.",
  "evidence.none.title": "No evidence extracted",
  "evidence.none.body":
    "Nothing in the input could be turned into an evidence item. " +
    "Check that the logs are plain text rather than a screenshot or binary file.",
  "evidence.count.title": "{count} evidence items",
  "evidence.count.body":
    "Every claim the tool makes cites these IDs. A claim with no ID next to it " +
    "is a claim nobody has checked.",
  "evidence.redacted.title": "{count} value(s) redacted before leaving this machine",
  "evidence.redacted.body":
    "Emails, IP addresses, bearer tokens and card-shaped numbers were replaced " +
    "with placeholders. The originals never reached the model provider.",
  "evidence.section": "Evidence",
  "evidence.section.hint": "grouped by source, filterable",
  "evidence.filter": "Filter evidence…",
  "evidence.shown": "{count} shown",
  "evidence.allSources": "all sources",
  "evidence.line": "line {line}",

  /* --- timeline view ----------------------------------------------------- */
  "timeline.empty": "The timeline is built from timestamps found in the logs and alerts.",
  "timeline.none.title": "No timeline could be built",
  "timeline.none.body":
    "No parseable timestamps were found. Include raw log lines with their " +
    "original time prefixes rather than a summary.",
  "timeline.inferred.title": "{count} of {total} events are inferred, not observed",
  "timeline.inferred.body":
    "Dashed markers were deduced rather than read from a log line. Treat them " +
    "as assumptions until a source is found.",
  "timeline.allObserved.title": "Every event is backed by a timestamped input line",
  "timeline.allObserved.body": "Nothing in this timeline was invented to fill a gap.",
  "timeline.section": "Timeline",
  "timeline.section.hint": "earliest first",
  "timeline.unknownTime": "time unknown",
  "timeline.inferred": "inferred",
  "timeline.inferred.tip": "No input line states this directly — it was deduced.",
  "timeline.observed": "observed",
  "timeline.observed.tip": "Taken straight from a timestamped input line.",

  /* --- hypotheses view --------------------------------------------------- */
  "hyp.empty":
    "Root-cause hypotheses appear here, ranked by how well the evidence supports them.",
  "hyp.none.title": "No hypotheses generated",
  "hyp.none.body":
    "The evidence may be too thin to support any explanation. Add logs from " +
    "around the failure window and run again.",
  "hyp.count.title": "{count} competing explanations",
  "hyp.count.body":
    "IncidentIQ ranks these; it does not choose between them. The ranking " +
    "reflects how much of the input each explanation accounts for, not how likely " +
    "it is to be true.",
  "hyp.tie.title": "The top two hypotheses are effectively tied",
  "hyp.tie.body":
    "The current evidence cannot tell them apart. Run the test on the leading " +
    "hypothesis before spending effort on a fix.",
  "hyp.section": "Ranked hypotheses",
  "hyp.section.hint": "highest evidential support first",
  "hyp.for": "Evidence for",
  "hyp.against": "Evidence against",
  "hyp.noneFound": "none found",
  "hyp.noneLooked": "none found — did anyone look?",
  "hyp.oneSided.title": "Only supporting evidence was found",
  "hyp.oneSided.body":
    "Before trusting this, go looking for something that would prove it wrong. " +
    "A hypothesis nothing can contradict is not a strong hypothesis — it is an untested one.",
  "hyp.test": "Test that would settle it",
  "hyp.rebuttal": "Counter-argument (second pass)",

  /* --- risks view -------------------------------------------------------- */
  "risks.empty":
    "Cognitive biases and logical fallacies found in this investigation appear here.",
  "risks.flagged.title": "{count} reasoning risk(s) flagged",
  "risks.flagged.body":
    "These describe how the investigation may be going wrong, not what broke in " +
    "production. Read them before acting on the hypotheses.",
  "risks.clean.title": "No reasoning risks flagged",
  "risks.clean.body":
    "The checks below all ran and found nothing. That is weaker evidence than it " +
    "sounds: the detectors only see the reasoning that was written down.",
  "risks.section": "Flagged risks",
  "risks.section.hint": "sorted by severity",
  "risks.where": "Where it showed up: ",
  "risks.impact": "Effect on the investigation: ",
  "risks.mitigation": "How to reduce it: ",
  "risks.triggeredBy": "triggered by",
  "risks.catalog": "What was checked",
  "risks.catalog.hint": "the eight biases and fallacies named in the project brief",
  "risks.catalog.bias": "Bias or fallacy",
  "risks.catalog.appears": "How it can appear in this project",
  "risks.catalog.status": "Status",
  "risks.detected": "detected",
  "risks.notFound": "checked, not found",
  "risks.detector.heuristic": "rule-based",
  "risks.detector.heuristic.title":
    "Flagged by a deterministic rule in the backend, independent of any model.",
  "risks.detector.model": "model",
  "risks.detector.model.title":
    "Flagged by the language model reviewing its own reasoning.",
  "risks.detector.both": "rule + model",
  "risks.detector.both.title":
    "Flagged independently by both the deterministic rule and the model.",
  "risks.why.title": "Why this pane exists",
  "risks.why.body":
    "AI output reads as confident and professional whether or not it is correct. " +
    "Automation bias is the risk that a fluent answer gets accepted because it is " +
    "fluent. The tool cannot remove that risk — it can only keep pointing at it.",

  /* --- actions view ------------------------------------------------------ */
  "actions.empty": "Recommended debugging steps appear here once an analysis has run.",
  "actions.none.title": "No next actions produced",
  "actions.none.body": "Nothing actionable could be derived from the current evidence.",
  "actions.generic.title": "{count} of {total} steps are generic",
  "actions.generic.body":
    "They are not wrong, but nothing in this incident specifically points to them. " +
    "Do the evidence-backed steps first.",
  "actions.grounded.title": "Every step is tied to specific evidence",
  "actions.grounded.body": "Each row cites the input that motivates it.",
  "actions.section": "Next debugging steps",
  "actions.section.hint": "highest priority first",
  "actions.col.priority": "Pri",
  "actions.col.action": "Action",
  "actions.col.owner": "Owner",
  "actions.col.because": "Because of",
  "actions.ungrounded": "ungrounded",
  "actions.genericNote": "generic advice — no evidence in this incident motivates it",
  "actions.warn.title": "Before you run anything destructive",
  "actions.warn.body":
    "A restart or a rollback both fixes and destroys evidence. If the incident is " +
    "not actively hurting users, capture the current state first — the next hour of " +
    "investigation depends on it.",
  "owner.engineer": "on-call engineer",
  "owner.sre": "SRE / platform",
  "owner.manager": "engineering manager",
  "owner.support": "support team",
  "owner.security": "security",

  /* --- report view ------------------------------------------------------- */
  "report.empty":
    "A draft postmortem is generated from the analysis and can be exported as Markdown.",
  "report.none.title": "No postmortem generated",
  "report.none.body": "The analysis completed but produced no report body.",
  "report.draft.title": "This is a draft, not a published postmortem",
  "report.draft.body":
    "It is assembled from hypotheses that have not been tested yet. Confirm the " +
    "root cause with a real test, delete the hypotheses that fail, and put your " +
    "own name on it before circulating.",
  "report.section": "Draft postmortem",
  "report.section.hint": "Markdown, ready to paste into a wiki or a PR",
  "report.copy": "Copy Markdown",
  "report.download": "Download .md",
  "report.chars": "{count} characters",
  "report.copied": "Postmortem copied to the clipboard",
  "report.copyFailed": "The browser blocked clipboard access — use Download instead.",
  "report.downloaded": "Saved to your downloads folder",
};

const HE = {
  /* --- chrome ------------------------------------------------------------ */
  "app.tagline": "ניתוח תקלות מבוסס ראיות",
  "app.skipLink": "דלג לתוצאות הניתוח",
  "app.inputPanel": "פאנל קלט",
  "app.inputPanel.title": "הצג או הסתר את פאנל הקלט",
  "app.theme.toLight": "עבור למצב בהיר",
  "app.theme.toDark": "עבור למצב כהה",
  "app.lang.title": "החלף שפת ממשק",
  "app.sidebar.aria": "קלט התקלה",

  "step.1": "טעינת תקלה",
  "step.2": "ראיות",
  "step.3": "ניתוח",

  /* --- tabs -------------------------------------------------------------- */
  "tab.summary": "סיכום",
  "tab.evidence": "ראיות",
  "tab.timeline": "ציר זמן",
  "tab.hypotheses": "היפותזות",
  "tab.risks": "סיכוני חשיבה",
  "tab.actions": "צעדים הבאים",
  "tab.report": "דוח תחקיר",
  "tabs.aria": "חלקי הניתוח",

  /* --- status bar -------------------------------------------------------- */
  "status.idle": "מוכן — טען דוגמה או הדבק ראיות",
  "status.running": "מנתח…",
  "status.done": "הניתוח הושלם",
  "status.error": "נכשל: {error}",
  "status.grounding": "עיגון {value}",
  "status.grounding.title":
    "שיעור הטענות של המודל שמצטטות ראיה שקיימת בפועל בקלט",
  "status.model": "מודל {model}",

  "provider.notRun": "טרם הורץ",
  "provider.offline": "מנוע לא־מקוון",
  "provider.offline.title":
    "לא נעשה שימוש במודל שפה. הניתוח הזה הופק כולו על ידי המנוע הדטרמיניסטי.",
  "provider.online.title": "ניתוח בסיוע מודל, מאומת מול ראיות הקלט",

  /* --- input panel ------------------------------------------------------- */
  "input.title.label": "כותרת התקלה",
  "input.title.placeholder": "כשלים בתשלום אחרי v2.4.1",
  "input.chars": "{count} תווים",
  "input.file": "קובץ",
  "input.file.title": 'טען קובץ לשדה "{label}"',

  "field.description.label": "תיאור התקלה",
  "field.description.placeholder": "מה נכשל, ממתי, ומי שם לב?",
  "field.description.help": "משפט או שניים. זה הקשר, לא ראיה.",
  "field.logs.label": "לוגים של האפליקציה",
  "field.logs.placeholder": "2026-05-02T10:14:03Z ERROR checkout ...",
  "field.logs.help": "הדבק שורות גולמיות. חותמות הזמן משמשות לבניית ציר הזמן.",
  "field.errors.label": "עקבות שגיאה",
  "field.errors.placeholder": "Traceback (most recent call last): ...",
  "field.alerts.label": "התראות ניטור",
  "field.alerts.placeholder": "[FIRING] CheckoutErrorRate > 5% for 10m",
  "field.deployNotes.label": "הערות פריסה אחרונות",
  "field.deployNotes.placeholder": "v2.4.1 - מעבר ל-connection pooling בלקוח התשלומים",
  "field.deployNotes.help": "פריסה שקדמה לתקלה היא כיוון חקירה, לא סיבה.",
  "field.userReports.label": "תלונות משתמשים / פניות תמיכה",
  "field.userReports.placeholder": '"הכרטיס נדחה בתשלום" ×14 מאז 10:20',

  /* --- samples ----------------------------------------------------------- */
  "samples.loading": "טוען דוגמאות…",
  "samples.none": "לא נמצאו תקלות לדוגמה בתיקייה data/samples/.",
  "samples.loaded": 'נטען "{title}"',

  /* --- run panel --------------------------------------------------------- */
  "run.devilsAdvocate": "טען נגד ההיפותזה המובילה",
  "run.devilsAdvocate.help": "מריץ מעבר שני שמנסה להפריך את התשובה המובילה.",
  "run.redact": "הסתר כתובות מייל, IP וטוקנים לפני השליחה",
  "run.redact.help": "שום דבר שנראה כמו סוד לא יוצא מהמחשב הזה.",
  "run.analyse": "נתח תקלה",
  "run.analysing": "מנתח…",
  "run.cancel": "ביטול",
  "run.clear": "נקה הכל",
  "run.shortcut": "מכל מקום",
  "run.disclaimer":
    "IncidentIQ מציע היפותזות. הוא אינו קובע את סיבת השורש — הרץ את הבדיקה " +
    "המוצעת לפני שאתה מאמין לאחת מהן.",
  "run.needInput": "הוסף קודם ראיות — תיאור, או כמה שורות לוג.",
  "run.unsupportedToast":
    "{count} טענות של המודל לא ניתנות למעקב אל הקלט. ראה את טאב הסיכום.",
  "run.offlineToast": "רץ במצב לא־מקוון — לא נעשה שימוש במודל שפה.",

  "progress.evidence": "מחלץ פריטי ראיה",
  "progress.timeline": "משחזר את ציר הזמן",
  "progress.hypotheses": "מייצר היפותזות מתחרות",
  "progress.verify": "בודק טענות מול הראיות",
  "progress.risks": "סורק סיכוני חשיבה",

  /* --- shared ------------------------------------------------------------ */
  "empty.notRun": "אין ניתוח עדיין",
  "empty.noEvidence": "ללא ציטוט ראיה",
  "evref.broken.title": "{id} לא קיים בקלט. המודל המציא את הציטוט הזה.",
  "evref.show": "הצג את הראיה",

  "band.wellSupported": "מבוסס היטב",
  "band.plausible": "סביר",
  "band.weak": "חלש",
  "band.speculative": "ספקולטיבי",
  "band.unrated": "ללא דירוג",

  "source.description": "תיאור התקלה",
  "source.logs": "לוגים של האפליקציה",
  "source.errors": "עקבות שגיאה",
  "source.alerts": "התראות ניטור",
  "source.deploy_notes": "הערות פריסה",
  "source.user_reports": "דיווחי משתמשים",

  /* --- summary view ------------------------------------------------------ */
  "summary.empty":
    "טען אחת מהתקלות לדוגמה מהסרגל הצדדי, או הדבק לוגים משלך, ואז לחץ על נתח תקלה.",
  "summary.failed": "הניתוח נכשל",
  "summary.offline.title": "מצב לא־מקוון",
  "summary.offline.body":
    "לא נעשה שימוש במודל שפה. כל מה שמופיע להלן הופק על ידי המנוע הדטרמיניסטי: " +
    "ראיות שזוהו בהתאמת תבניות, ציר זמן ממוין לפי חותמות זמן, והיפותזות מבוססות כללים. " +
    "הוסף מפתח API בקובץ ‎.env‎ לניתוח בסיוע מודל.",
  "summary.verified.title": "כל טענה עוגנה בראיה (עיגון {value})",
  "summary.verified.body":
    "כל היגד להלן מצטט לפחות פריט קלט אחד שקיים בפועל. " +
    "ניתן למעקב אינו זהה לנכון — הראיה המצוטטת עשויה בעצמה להטעות.",
  "summary.failedChecks.title": "{count} טענות נכשלו באימות (עיגון {value})",
  "summary.invented": "ציטוטים שהומצאו: ",
  "summary.invented.body": "המודל ציטט את {list}, שאינם קיימים בקלט.",
  "summary.unsupported": "היגדים ללא ביסוס: ",
  "summary.unsupported.body": "{count} טענות אינן מצטטות ראיה כלל.",
  "summary.what": "מה קרה",
  "summary.what.hint": "סיכום מקצועי, ללא טענות בלתי מבוססות",
  "summary.noSummary": "לא הופק סיכום.",
  "summary.basedOn": "מבוסס על",
  "summary.factsVsAssumptions": "עובדות מול הנחות",
  "summary.factsVsAssumptions.hint":
    "השניים מופרדים בכוונה — ערבוב ביניהם הוא הדרך שבה חקירות משתבשות",
  "summary.facts": "עובדות",
  "summary.facts.title": "נתמך ישירות על ידי הקלט",
  "summary.facts.none": "אף היגד בניתוח לא עוגן במלואו.",
  "summary.assumptions": "הנחות",
  "summary.assumptions.title": "מאמינים אך לא הוכח",
  "summary.assumptions.none": "לא סומנו הנחות.",
  "summary.assumption.why": "למה אנחנו חושבים כך: {why}",
  "summary.assumption.verify": "כדי לאמת: ",
  "summary.audiences": "אותן עובדות, שלושה קהלים",
  "summary.audiences.hint": "הניסוח משתנה, הטענות לא",
  "summary.audience.engineer": "למהנדס התורן",
  "summary.audience.manager": "למנהל הפיתוח",
  "summary.audience.support": "לצוות התמיכה",
  "summary.openQuestions": "עדיין לא ידוע",
  "summary.openQuestions.hint": "שאלות שחייבות מענה לפני סגירת התקלה",

  /* --- evidence view ----------------------------------------------------- */
  "evidence.empty": "לאחר הרצת ניתוח, כל שורת קלט תופיע כאן עם מזהה קבוע.",
  "evidence.none.title": "לא חולצו ראיות",
  "evidence.none.body":
    "שום דבר בקלט לא ניתן היה להפוך לפריט ראיה. " +
    "ודא שהלוגים הם טקסט רגיל ולא צילום מסך או קובץ בינארי.",
  "evidence.count.title": "{count} פריטי ראיה",
  "evidence.count.body":
    "כל טענה שהכלי מייצר מצטטת את המזהים האלה. טענה בלי מזהה לצידה " +
    "היא טענה שאיש לא בדק.",
  "evidence.redacted.title": "{count} ערכים הוסתרו לפני יציאה מהמחשב",
  "evidence.redacted.body":
    "כתובות מייל, כתובות IP, טוקני הרשאה ומספרים בצורת כרטיס אשראי הוחלפו " +
    "במחזיקי מקום. המקוריים מעולם לא הגיעו לספק המודל.",
  "evidence.section": "ראיות",
  "evidence.section.hint": "מקובצות לפי מקור, ניתנות לסינון",
  "evidence.filter": "סנן ראיות…",
  "evidence.shown": "{count} מוצגות",
  "evidence.allSources": "כל המקורות",
  "evidence.line": "שורה {line}",

  /* --- timeline view ----------------------------------------------------- */
  "timeline.empty": "ציר הזמן נבנה מחותמות הזמן שנמצאו בלוגים ובהתראות.",
  "timeline.none.title": "לא ניתן היה לבנות ציר זמן",
  "timeline.none.body":
    "לא נמצאו חותמות זמן שניתן לפענח. כלול שורות לוג גולמיות עם קידומות הזמן " +
    "המקוריות שלהן ולא סיכום.",
  "timeline.inferred.title": "{count} מתוך {total} אירועים הוסקו, לא נצפו",
  "timeline.inferred.body":
    "סמנים מקווקווים הוסקו ולא נקראו משורת לוג. התייחס אליהם כאל הנחות " +
    "עד שיימצא מקור.",
  "timeline.allObserved.title": "כל אירוע נתמך בשורת קלט עם חותמת זמן",
  "timeline.allObserved.body": "שום דבר בציר הזמן הזה לא הומצא כדי לסתום פער.",
  "timeline.section": "ציר זמן",
  "timeline.section.hint": "המוקדם ביותר תחילה",
  "timeline.unknownTime": "זמן לא ידוע",
  "timeline.inferred": "מוסק",
  "timeline.inferred.tip": "אף שורת קלט אינה קובעת זאת ישירות — זה הוסק.",
  "timeline.observed": "נצפה",
  "timeline.observed.tip": "נלקח ישירות משורת קלט עם חותמת זמן.",

  /* --- hypotheses view --------------------------------------------------- */
  "hyp.empty": "היפותזות לסיבת השורש יופיעו כאן, מדורגות לפי מידת התמיכה של הראיות.",
  "hyp.none.title": "לא נוצרו היפותזות",
  "hyp.none.body":
    "ייתכן שהראיות דלות מכדי לתמוך בהסבר כלשהו. הוסף לוגים מסביב לחלון " +
    "הכשל והרץ שוב.",
  "hyp.count.title": "{count} הסברים מתחרים",
  "hyp.count.body":
    "IncidentIQ מדרג אותם; הוא אינו בוחר ביניהם. הדירוג משקף כמה מהקלט כל הסבר " +
    "מסביר, לא כמה סביר שהוא נכון.",
  "hyp.tie.title": "שתי ההיפותזות המובילות שקולות למעשה",
  "hyp.tie.body":
    "הראיות הנוכחיות אינן מבדילות ביניהן. הרץ את הבדיקה על ההיפותזה המובילה " +
    "לפני שתשקיע מאמץ בתיקון.",
  "hyp.section": "היפותזות מדורגות",
  "hyp.section.hint": "התמיכה הראייתית הגבוהה ביותר תחילה",
  "hyp.for": "ראיות בעד",
  "hyp.against": "ראיות נגד",
  "hyp.noneFound": "לא נמצאו",
  "hyp.noneLooked": "לא נמצאו — האם מישהו בדק?",
  "hyp.oneSided.title": "נמצאו רק ראיות תומכות",
  "hyp.oneSided.body":
    "לפני שתסמוך על זה, חפש משהו שיוכיח שזה שגוי. " +
    "היפותזה ששום דבר לא יכול לסתור אינה היפותזה חזקה — היא היפותזה שלא נבדקה.",
  "hyp.test": "בדיקה שתכריע",
  "hyp.rebuttal": "טיעון נגדי (מעבר שני)",

  /* --- risks view -------------------------------------------------------- */
  "risks.empty": "הטיות קוגניטיביות וכשלים לוגיים שנמצאו בחקירה הזו יופיעו כאן.",
  "risks.flagged.title": "{count} סיכוני חשיבה סומנו",
  "risks.flagged.body":
    "אלה מתארים כיצד החקירה עלולה להשתבש, לא מה נשבר בייצור. " +
    "קרא אותם לפני שתפעל לפי ההיפותזות.",
  "risks.clean.title": "לא סומנו סיכוני חשיבה",
  "risks.clean.body":
    "כל הבדיקות להלן רצו ולא מצאו דבר. זו ראיה חלשה יותר ממה שזה נשמע: " +
    "הגלאים רואים רק את החשיבה שנכתבה.",
  "risks.section": "סיכונים שסומנו",
  "risks.section.hint": "ממוינים לפי חומרה",
  "risks.where": "היכן הופיע: ",
  "risks.impact": "השפעה על החקירה: ",
  "risks.mitigation": "כיצד להפחית: ",
  "risks.triggeredBy": "הופעל על ידי",
  "risks.catalog": "מה נבדק",
  "risks.catalog.hint": "שמונה ההטיות והכשלים המפורטים במסמך העבודה",
  "risks.catalog.bias": "הטיה או כשל",
  "risks.catalog.appears": "כיצד זה יכול להופיע בפרויקט הזה",
  "risks.catalog.status": "סטטוס",
  "risks.detected": "זוהה",
  "risks.notFound": "נבדק, לא נמצא",
  "risks.detector.heuristic": "מבוסס כללים",
  "risks.detector.heuristic.title":
    "סומן על ידי כלל דטרמיניסטי בצד השרת, ללא תלות במודל כלשהו.",
  "risks.detector.model": "מודל",
  "risks.detector.model.title": "סומן על ידי מודל השפה שבחן את החשיבה של עצמו.",
  "risks.detector.both": "כלל + מודל",
  "risks.detector.both.title":
    "סומן באופן עצמאי גם על ידי הכלל הדטרמיניסטי וגם על ידי המודל.",
  "risks.why.title": "למה החלון הזה קיים",
  "risks.why.body":
    "פלט של AI נקרא בטוח ומקצועי בין אם הוא נכון ובין אם לא. " +
    "הטיית אוטומציה היא הסיכון שתשובה רהוטה תתקבל משום שהיא רהוטה. " +
    "הכלי אינו יכול להסיר את הסיכון — הוא יכול רק להמשיך להצביע עליו.",

  /* --- actions view ------------------------------------------------------ */
  "actions.empty": "צעדי הדיבוג המומלצים יופיעו כאן לאחר הרצת ניתוח.",
  "actions.none.title": "לא הופקו צעדים הבאים",
  "actions.none.body": "לא ניתן היה להסיק פעולה מהראיות הנוכחיות.",
  "actions.generic.title": "{count} מתוך {total} צעדים הם כלליים",
  "actions.generic.body":
    "הם אינם שגויים, אבל שום דבר בתקלה הזו אינו מצביע עליהם ספציפית. " +
    "בצע קודם את הצעדים הנתמכים בראיות.",
  "actions.grounded.title": "כל צעד קשור לראיה ספציפית",
  "actions.grounded.body": "כל שורה מצטטת את הקלט שמניע אותה.",
  "actions.section": "צעדי דיבוג הבאים",
  "actions.section.hint": "העדיפות הגבוהה ביותר תחילה",
  "actions.col.priority": "עדיפות",
  "actions.col.action": "פעולה",
  "actions.col.owner": "אחראי",
  "actions.col.because": "בגלל",
  "actions.ungrounded": "ללא עיגון",
  "actions.genericNote": "עצה כללית — שום ראיה בתקלה הזו אינה מניעה אותה",
  "actions.warn.title": "לפני שאתה מריץ משהו הרסני",
  "actions.warn.body":
    "אתחול או גלגול לאחור גם מתקנים וגם משמידים ראיות. אם התקלה אינה פוגעת " +
    "במשתמשים באופן פעיל, תעד קודם את המצב הנוכחי — השעה הבאה של החקירה תלויה בזה.",
  "owner.engineer": "מהנדס תורן",
  "owner.sre": "SRE / פלטפורמה",
  "owner.manager": "מנהל פיתוח",
  "owner.support": "צוות תמיכה",
  "owner.security": "אבטחה",

  /* --- report view ------------------------------------------------------- */
  "report.empty": "טיוטת דוח תחקיר נוצרת מהניתוח וניתנת לייצוא כ-Markdown.",
  "report.none.title": "לא נוצר דוח תחקיר",
  "report.none.body": "הניתוח הושלם אך לא הפיק גוף דוח.",
  "report.draft.title": "זו טיוטה, לא דוח תחקיר מפורסם",
  "report.draft.body":
    "הוא מורכב מהיפותזות שטרם נבדקו. אמת את סיבת השורש בבדיקה אמיתית, " +
    "מחק את ההיפותזות שנכשלו, וחתום בשמך לפני הפצה.",
  "report.section": "טיוטת דוח תחקיר",
  "report.section.hint": "Markdown, מוכן להדבקה בוויקי או ב-PR",
  "report.copy": "העתק Markdown",
  "report.download": "הורד ‎.md",
  "report.chars": "{count} תווים",
  "report.copied": "דוח התחקיר הועתק ללוח",
  "report.copyFailed": "הדפדפן חסם גישה ללוח — השתמש בהורדה במקום.",
  "report.downloaded": "נשמר לתיקיית ההורדות",
};

const DICTS = { en: EN, he: HE };
export const LANGUAGES = [
  { code: "en", label: "EN", name: "English", dir: "ltr" },
  { code: "he", label: "עב", name: "עברית", dir: "rtl" },
];

const STORAGE_KEY = "iq.lang";
let current = "en";

/** Read the saved language, falling back to the browser's preference. */
export function detectLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && DICTS[saved]) return saved;
  } catch { /* private mode */ }
  return (navigator.language || "en").toLowerCase().startsWith("he") ? "he" : "en";
}

export function getLanguage() {
  return current;
}

export function dirFor(lang = current) {
  return lang === "he" ? "rtl" : "ltr";
}

/**
 * Apply a language to the document. Does not re-render anything - the caller
 * puts the language into the store, and the views redraw from state.
 */
export function applyLanguage(lang) {
  current = DICTS[lang] ? lang : "en";
  document.documentElement.lang = current;
  document.documentElement.dir = dirFor(current);
  try { localStorage.setItem(STORAGE_KEY, current); } catch { /* private mode */ }
  translateStatic();
  return current;
}

/**
 * Translate a key.
 * `{name}` placeholders are replaced from `vars`.
 * Missing keys fall back to English, then to the key - never to blank.
 */
export function t(key, vars) {
  const dict = DICTS[current] || EN;
  let value = dict[key];
  if (value === undefined) value = EN[key];
  if (value === undefined) return key;
  if (!vars) return value;
  return value.replace(/\{(\w+)\}/g, (match, name) =>
    Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : match
  );
}

/**
 * Fill in the static markup in index.html.
 *
 * Elements carry `data-i18n` (text content), `data-i18n-title` or
 * `data-i18n-aria`. Keeping the keys in the HTML means the shell markup stays
 * readable, instead of being assembled in JavaScript purely to be translatable.
 */
export function translateStatic(root = document) {
  for (const node of root.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n);
  }
  for (const node of root.querySelectorAll("[data-i18n-title]")) {
    node.title = t(node.dataset.i18nTitle);
  }
  for (const node of root.querySelectorAll("[data-i18n-aria]")) {
    node.setAttribute("aria-label", t(node.dataset.i18nAria));
  }
}
