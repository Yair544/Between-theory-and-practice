"""
Wording for the offline engine, per language.

The offline engine is not a corner case. It runs whenever there is no API key,
*and* whenever a model call fails - and on a free-tier key a rate limit is
reached easily. So a Hebrew interface falling back to an English analysis is a
thing users actually see, not a theoretical gap.

Only the deterministic engine's own prose lives here. Model output is translated
by the model (see prompts.LANGUAGE_INSTRUCTION), and evidence text is never
translated at all.

`get(language)` always returns a usable table: an unknown language falls back to
English rather than raising, because a missing translation must degrade to
readable, never to a crash in the fallback path itself.
"""

from __future__ import annotations

EN = {
    "summary.errors":
        "{errors} error-level items were found across {sources} source(s), "
        "falling into {patterns} distinct message pattern(s). The most frequent "
        "pattern occurred {top} time(s). ",
    "summary.earliest": "The earliest error is timestamped {ts}. ",
    "summary.nomodel":
        "No causal analysis was performed: this summary was produced by pattern "
        "matching, with no language model involved.",
    "summary.noerrors":
        "{total} evidence items were indexed. None matched an error or warning "
        "pattern, so nothing can be said about what failed without a language "
        "model or a human reading the input.",

    "fact.pattern": 'The pattern "{shape}" appears {count} time(s) in the input.',
    "fact.deploy": "Deployment notes were supplied alongside the failure evidence.",

    "hyp.cluster.title": "The failure is centred on: {shape}",
    "hyp.cluster.body":
        "This message pattern accounts for {share} of the error-level evidence "
        "({count} of {errors} items). The offline engine ranks clusters by "
        "frequency; it does not know what this message means or what could "
        "produce it.",
    "hyp.cluster.test":
        "Read these lines in full and identify the component that emits them, "
        "then check whether the same message appears before the incident window.",
    "hyp.deploy.title": "A recent deployment changed behaviour",
    "hyp.deploy.body":
        "Deployment notes were supplied. This hypothesis is listed because it is "
        "the standard suspect, NOT because any evidence connects the deployment "
        "to the failures - the offline engine cannot make that connection.",
    "hyp.deploy.test":
        "Check whether these errors exist in logs from before the deployment.",

    "assume.clusters":
        "The clusters above correspond to distinct failures rather than one "
        "failure reported repeatedly.",
    "assume.clusters.why":
        "Messages were grouped by text shape only, with no knowledge of the "
        "systems involved.",
    "assume.clusters.verify":
        "Check whether the grouped lines share a request id or a trace id.",

    "action.readfirst": "Read the {count} earliest error lines in full context.",
    "action.readfirst.why":
        "The first failure usually carries more information than the retries "
        "after it.",
    "action.compare": "Compare error rates from before and after the deployment window.",
    "action.compare.why":
        "Establishes whether the deployment is correlated at all, before assuming "
        "it is causal.",
    "action.addkey": "Configure an API key in .env and re-run the analysis.",
    "action.addkey.why":
        "Causal reasoning, disconfirming evidence and the reasoning-risk audit "
        "require a language model. This run produced none of them.",

    "q.meaning": "What does the dominant error message actually mean in this system?",
    "q.meaning.why":
        "Frequency ranking is not explanation. Without this, the ranking above is "
        "just counting.",
    "q.change":
        "Was there a change - deploy, config, traffic, dependency - in the hour "
        "before the first error?",
    "q.change.why": "The offline engine cannot correlate across sources.",
}

HE = {
    "summary.errors":
        "נמצאו {errors} פריטים ברמת שגיאה ב-{sources} מקורות, המתחלקים ל-{patterns} "
        "תבניות הודעה נבדלות. התבנית השכיחה ביותר הופיעה {top} פעמים. ",
    "summary.earliest": "השגיאה המוקדמת ביותר נושאת חותמת זמן {ts}. ",
    "summary.nomodel":
        "לא בוצע ניתוח סיבתי: הסיכום הזה הופק בהתאמת תבניות, ללא מעורבות של "
        "מודל שפה.",
    "summary.noerrors":
        "{total} פריטי ראיה נסרקו. אף אחד מהם לא תאם תבנית של שגיאה או אזהרה, "
        "ולכן לא ניתן לומר דבר על מה שנכשל ללא מודל שפה או אדם שיקרא את הקלט.",

    "fact.pattern": 'התבנית "{shape}" מופיעה {count} פעמים בקלט.',
    "fact.deploy": "הערות פריסה סופקו לצד ראיות הכשל.",

    "hyp.cluster.title": "הכשל מרוכז סביב: {shape}",
    "hyp.cluster.body":
        "תבנית ההודעה הזו מהווה {share} מהראיות ברמת שגיאה ({count} מתוך {errors} "
        "פריטים). המנוע הלא־מקוון מדרג אשכולות לפי תדירות; הוא אינו יודע מה "
        "ההודעה הזו אומרת או מה עלול לגרום לה.",
    "hyp.cluster.test":
        "קרא את השורות האלה במלואן וזהה את הרכיב שפולט אותן, ואז בדוק אם אותה "
        "הודעה מופיעה גם לפני חלון התקלה.",
    "hyp.deploy.title": "פריסה אחרונה שינתה התנהגות",
    "hyp.deploy.body":
        "סופקו הערות פריסה. ההיפותזה הזו מופיעה משום שהיא החשוד המקובל, ולא "
        "משום שראיה כלשהי מקשרת בין הפריסה לכשלים — המנוע הלא־מקוון אינו יכול "
        "ליצור את הקישור הזה.",
    "hyp.deploy.test": "בדוק אם השגיאות האלה קיימות בלוגים מלפני הפריסה.",

    "assume.clusters":
        "האשכולות שלמעלה מייצגים כשלים נבדלים ולא כשל אחד שדווח שוב ושוב.",
    "assume.clusters.why":
        "ההודעות קובצו לפי צורת הטקסט בלבד, ללא ידע על המערכות המעורבות.",
    "assume.clusters.verify":
        "בדוק אם לשורות המקובצות יש מזהה בקשה או מזהה מעקב משותף.",

    "action.readfirst": "קרא את {count} שורות השגיאה המוקדמות ביותר בהקשר מלא.",
    "action.readfirst.why":
        "הכשל הראשון נושא בדרך כלל יותר מידע מהניסיונות החוזרים שאחריו.",
    "action.compare": "השווה שיעורי שגיאה מלפני ואחרי חלון הפריסה.",
    "action.compare.why":
        "מבסס אם קיים בכלל מתאם עם הפריסה, לפני שמניחים שהיא סיבתית.",
    "action.addkey": "הגדר מפתח API בקובץ ‎.env‎ והרץ את הניתוח מחדש.",
    "action.addkey.why":
        "חשיבה סיבתית, ראיות סותרות וביקורת סיכוני החשיבה מחייבות מודל שפה. "
        "ההרצה הזו לא הפיקה אף אחת מהן.",

    "q.meaning": "מה הודעת השגיאה הדומיננטית באמת אומרת במערכת הזו?",
    "q.meaning.why":
        "דירוג לפי תדירות אינו הסבר. בלי זה, הדירוג שלמעלה הוא ספירה בלבד.",
    "q.change":
        "האם היה שינוי — פריסה, קונפיגורציה, תעבורה, תלות — בשעה שלפני השגיאה הראשונה?",
    "q.change.why": "המנוע הלא־מקוון אינו יכול לבצע מתאם בין מקורות.",
}

_TABLES = {"en": EN, "he": HE}


def get(language: str) -> dict[str, str]:
    """The string table for a language, falling back to English."""
    return _TABLES.get(language, EN)
