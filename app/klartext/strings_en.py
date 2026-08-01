"""Englische Texte — die Standardsprache der Seite.

Ein Schluessel je Satz. Platzhalter in geschweiften Klammern werden beim
Uebersetzen gefuellt; Schluessel ohne Platzhalter enthalten keine Klammern.
"""

STRINGS: dict[str, str] = {
    # ---------------------------------------------------------------- Rahmen
    "meta.title": "{product} — documents into clean Markdown",
    "meta.description": "{product} turns documents and images into clean Markdown "
    "and JSON — free, processed entirely on our own server.",
    "og.image_alt": "Klartext — documents become clean Markdown",
    "skip_to_content": "Skip to content",
    "nav.aria.main": "Main navigation",
    "nav.login": "Sign in",
    "nav.logout": "Sign out",
    "nav.create_account": "Create account",
    "nav.create_account_short": "Sign up",
    "nav.convert": "Convert",
    "nav.account": "Account",
    "nav.admin": "Administration",
    "footer.aria.legal": "Legal",
    "footer.imprint": "Imprint",
    "footer.privacy": "Privacy",
    "footer.terms": "Terms of use",
    "footer.licenses": "Open source licences",
    "footer.note": "Processed exclusively on our own server. Nothing is passed to "
    "third-party AI services.",
    "lang.aria": "Language",
    "lang.switch_to_en": "Switch to English",
    "lang.switch_to_de": "Switch to German",
    "lang.to_de": "Deutsch",
    "lang.to_en": "English",

    # --------------------------------------------------------------- Landing
    "landing.title": "{product} — Convert PDF, Scan & Photo to Markdown — Free OCR",
    "landing.description": "Convert PDF, scans, photos, Word or Excel into clean Markdown "
    "and JSON. Free, no tiers — OCR runs on our own server, no AI providers, GDPR-friendly.",
    "landing.schema.description": "Turns PDFs, photos, scans, Word, Excel and PowerPoint "
    "files into clean Markdown and structure-faithful JSON. Processed exclusively on our "
    "own server, never passed to external AI or OCR services.",
    "landing.eyebrow": "Free · Processed locally · No AI vendors",
    "landing.h1": "Documents, in plain text.",
    "landing.lead": "Upload a PDF, photo, scan, Word or Excel file — out comes clean "
    "Markdown you can actually use. No more retyping.",
    "landing.cta.primary": "Create a free account",
    "landing.cta.secondary": "Sign in",
    "landing.hero_note": "Free for good. No tiers, no payment, no locked features.",
    "landing.producthunt.alt": "Klartext — turn documents and scans into clean Markdown "
    "and JSON. Featured on Product Hunt.",
    "landing.bench.h": "Measured, not promised",
    "landing.bench.sub": "Three OCR engines competed for the job. One measurement, "
    "one winner — and that winner is what runs here.",
    "landing.bench.active": "runs here",
    "landing.bench.method": "Measured on 45 required fields — names, item numbers, "
    "amounts, umlauts, degree signs — across four test scans, each checked by hand. "
    "A typical document converts in seconds, not minutes.",
    "landing.showcase.aria": "On the left a scanned document with a table, on the right "
    "the Markdown produced from it with the same table.",
    "landing.showcase.before": "Before — scan or photo",
    "landing.showcase.after": "After — Markdown",
    "landing.showcase.code.heading": "# Price list 2026",
    "landing.showcase.code.body": """| Part number   | Description       | Price  |
|---------------|-------------------|--------|
| A-1001        | Copper pipe 15 mm | €8.40  |
| B-2010        | Pipe lagging 20mm | €4.95  |

All prices exclude VAT.""",
    "landing.formats.aria": "Supported file formats",
    "landing.formats.title": "Reads reliably",
    "landing.stats.aria": "Key facts",
    "landing.stats.formats": "formats",
    "landing.stats.pages": "pages per document",
    "landing.stats.retention": "then deleted",
    "landing.stats.price": "for good",
    "landing.feature.1.h": "Nothing leaves the server",
    "landing.feature.1.p": "Everything runs on this server. No content goes to OpenAI, "
    "Anthropic, Google or any other service. No ad networks, no cross-site tracking.",
    "landing.feature.2.h": "As little loss as possible",
    "landing.feature.2.p": "Numbers, names and tables stay exactly as they appear in the "
    "original. Nothing is summarised or rewritten.",
    "landing.feature.3.h": "Deleted automatically",
    "landing.feature.3.p": "Files and results disappear on their own after {hours} hours "
    "— or right away, if you prefer.",
    "landing.uses.h": "What people use this for",
    "landing.uses.sub": "Everyday cases, no jargon.",
    "landing.uses.1.h": "Photographed an invoice",
    "landing.uses.1.p": "Line items you can copy instead of retype.",
    "landing.uses.2.h": "Scanned a delivery note",
    "landing.uses.2.p": "Quantities and part numbers as a table.",
    "landing.uses.3.h": "Contract as a PDF",
    "landing.uses.3.p": "Find individual clauses with a text search.",
    "landing.uses.4.h": "Photographed a price list",
    "landing.uses.4.p": "A table ready for your spreadsheet.",
    "landing.uses.5.h": "Lecture notes",
    "landing.uses.5.p": "Text for summaries and flashcards.",
    "landing.uses.6.h": "Old letter from the filing cabinet",
    "landing.uses.6.p": "Searchable instead of just an image.",
    "landing.uses.7.h": "Excel spreadsheet",
    "landing.uses.7.p": "As Markdown for tools that can't read XLSX.",
    "landing.conv.h": "The conversions that matter",
    "landing.conv.sub": "What survives the trip, and what doesn't.",
    "landing.conv.1.h": "PDF to Markdown",
    "landing.conv.1.p": "Invoices, contracts, manuals. Headings, paragraphs and tables "
    "carry over. With multi-column layouts the reading order can get scrambled.",
    "landing.conv.2.h": "Photo to text",
    "landing.conv.2.p": "A photographed document becomes text you can copy. A straight, "
    "sharp photo gives the best result.",
    "landing.conv.3.h": "Word to Markdown",
    "landing.conv.3.p": "Headings, paragraphs, lists and tables arrive structured. "
    "Comments, footnotes and text boxes are lost.",
    "landing.conv.4.h": "Excel to Markdown",
    "landing.conv.4.p": "Every sheet becomes a Markdown table with a header row. Cell "
    "formats, formulas and charts are not carried over.",
    "landing.conv.5.h": "Scan to text",
    "landing.conv.5.p": "Even an old, yellowed letter becomes searchable. Poor scan "
    "quality or handwriting lowers recognition.",
    "landing.conv.6.h": "PowerPoint to Markdown",
    "landing.conv.6.p": "Each slide becomes a heading and a bullet list. Graphics, "
    "animations and notes are lost.",
    "landing.io.h": "What goes in, what comes out",
    "landing.io.sub": "{product} accepts these file types:",
    "landing.io.note": "You always get two files: <strong>.md</strong> to read and reuse, "
    "<strong>.json</strong> with the full structure for other programs.",
    "landing.limits.h": "The same limits for everyone",
    "landing.limits.sub": "Technical fair-use limits keep the service stable for everyone. "
    "They exist to prevent overload — not to sell you anything.",
    "landing.limits.filesize": "Size per file",
    "landing.limits.files": "Files per upload",
    "landing.limits.pages": "Pages per document",
    "landing.limits.perday": "Conversions per day",
    "landing.faq.h": "Common questions",
    "landing.faq.1.q": "Is {product} really free?",
    "landing.faq.1.a": "Yes. There are no tiers, no payment and no locked features. All "
    "you need is a free account.",
    "landing.faq.2.q": "What is Markdown, anyway?",
    "landing.faq.2.a": "A simple markup language for text: headings, lists and tables are "
    "marked with ordinary characters like # or |. Readable as plain text and, in note "
    "apps, wikis or on GitHub, nicely formatted.",
    "landing.faq.2.a_html": "A simple markup language for text: headings, lists and "
    "tables are marked with ordinary characters like <code>#</code> or <code>|</code>. "
    "Readable as plain text and, in note apps, wikis or on GitHub, nicely formatted.",
    "landing.faq.3.q": "What is the JSON file for?",
    "landing.faq.3.a": "It holds the same content broken down for machines — pages, "
    "blocks and table cells captured individually. Handy for your own programs, "
    "automations or databases, where Markdown would be too coarse.",
    "landing.faq.4.q": "Are my documents sent to an AI provider?",
    "landing.faq.4.a": "No. The entire conversion runs on our own server. No content is "
    "sent to OpenAI, Anthropic, Google or any other AI or OCR service.",
    "landing.faq.5.q": "Are my documents stored?",
    "landing.faq.5.a": "Only temporarily, for processing. Uploaded files and results are "
    "deleted automatically after {hours} hours, and you can remove any job by hand before "
    "that. {product} is not a storage service.",
    "landing.faq.6.q": "Is the result error-free?",
    "landing.faq.6.a": "No. The conversion is automatic and can contain mistakes with poor "
    "scans, handwriting or nested tables. Markdown also can't represent every layout — the "
    "JSON file is the structure-faithful version. Check results before you rely on them.",
    "landing.faq.7.q": "How well does {product} read handwriting?",
    "landing.faq.7.a": "Honestly: badly. Text recognition is trained on printed text. "
    "Handwritten notes, signatures or hand-filled forms often come out wrong or not at "
    "all — for print and good scans it works reliably.",
    "landing.faq.8.q": "Does it work with phone photos?",
    "landing.faq.8.a": "Yes. Sharpness and resolution decide: a straight, sharp, well-lit "
    "photo gives usable results, a blurry or dark one trips up the text recognition.",
    "landing.faq.9.q": "Which files can I upload?",
    "landing.faq.10.q": "Why do I need an account?",
    "landing.faq.10.a": "Registration is free and makes the fair-use limits apply per "
    "person, instead of all visitors sharing one common limit.",

    # ----------------------------------------------------------------- Login
    "login.title": "Sign in — {product}",
    "login.description": "Sign in to {product} and turn documents into Markdown and JSON.",
    "login.h1": "Sign in",
    "login.email": "Email address",
    "login.password": "Password",
    "login.submit": "Sign in",
    "login.resend": "Resend confirmation email",
    "login.forgot": "Forgotten your password?",
    "login.no_account": "No account yet?",
    "login.create": "Create an account",

    # -------------------------------------------------------------- Register
    "register.title": "Create a free account — {product}",
    "register.description": "Create a free {product} account and turn documents into "
    "Markdown and JSON. No tiers, no payment, no locked features.",
    "register.h1": "Create account",
    "register.intro": "Free, no tiers. We only need the account so the usage limits apply "
    "per person instead of all visitors sharing one common limit.",
    "register.errors_intro": "Please check your entries:",
    "register.email": "Email address",
    "register.password": "Password",
    "register.password_hint": "At least 10 characters. Longer beats complicated.",
    "register.password2": "Repeat password",
    "register.accept": "I have read the {terms} and the {privacy}.",
    "register.accept.terms": "terms of use",
    "register.accept.privacy": "privacy notice",
    "register.submit": "Create account",
    "register.have_account": "Already have an account?",
    "register.sign_in": "Sign in here",

    # --------------------------------------------------------- Register done
    "register_done.title": "Almost there — {product}",
    "register_done.h1": "Almost there",
    "register_done.mail": "If the address was still free, an email with a confirmation "
    "link is on its way. The link is valid for 24 hours.",
    "register_done.spam": "Nothing there? Please check your spam folder. If nothing "
    "arrives after a few minutes, {link}.",
    "register_done.spam_link": "we'll send the email again",
    "register_done.nomail": "The account is set up. You can sign in right away.",
    "register_done.to_login": "Go to sign-in",

    # --------------------------------------------------------- Verify again
    "verify_again.title": "Resend confirmation email — {product}",
    "verify_again.description": "No confirmation email from {product}? Request a new one "
    "here — the link is valid for 24 hours.",
    "verify_again.h1": "Resend confirmation email",
    "verify_again.nomail": "This installation has no email delivery configured. Please "
    "contact the operator.",
    "verify_again.intro": "Enter your address. If it belongs to an account that is still "
    "unconfirmed, we'll send a new link. It is valid for 24 hours; older links stop "
    "working at that point.",
    "verify_again.email": "Email address",
    "verify_again.submit": "Send the email again",
    "verify_again.back": "Back to sign-in",

    # ---------------------------------------------------------------- Forgot
    "forgot.title": "Forgotten password — {product}",
    "forgot.description": "Reset the password for your {product} account. We'll send you "
    "a link that is valid for one hour.",
    "forgot.h1": "Forgotten password",
    "forgot.nomail": "This installation has no email delivery configured, so resetting by "
    "link does not currently work — please contact the operator.",
    "forgot.intro": "Enter your address. If there is an account for it, we'll send a "
    "reset link. The link is valid for one hour and works once.",
    "forgot.email": "Email address",
    "forgot.submit": "Request link",
    "forgot.back": "Back to sign-in",

    # ----------------------------------------------------------------- Reset
    "reset.title": "New password — {product}",
    "reset.description": "Set a new password for your {product} account.",
    "reset.h1": "Set a new password",
    "reset.password": "New password",
    "reset.password_hint": "At least 10 characters.",
    "reset.password2": "Repeat new password",
    "reset.sessions_note": "All existing sign-ins will be ended.",
    "reset.submit": "Save password",
    "reset.broken": "The link is incomplete or has expired.",
    "reset.request_new": "Request a new link",

    # ------------------------------------------------------------- Info/Error
    "info.continue": "Continue",
    "info.to_app": "Go to overview",
    "info.to_login": "Go to sign-in",
    "error.title": "Error {status} — {product}",
    "error.h.401": "Sign-in required",
    "error.h.404": "Not found",
    "error.h.413": "File too large",
    "error.h.429": "One moment, please",
    "error.h.400": "That didn't work",
    "error.h.other": "Something went wrong",
    "error.code": "Error {status}",
    "error.to_home": "Go to home page",
    "error.to_app": "Go to overview",
    "error.to_login": "Go to sign-in",

    # ------------------------------------------------------------- Dashboard
    "dashboard.title": "Convert — {product}",
    "dashboard.h1": "New conversion",
    "dashboard.explainer": "Upload a file, {product} reads the content out of it.",
    "dashboard.drop": "Drag files here",
    "dashboard.or": "or",
    "dashboard.choose": "Choose files",
    "dashboard.limits": "max. {mb} MB · {files} files · {pages} pages",
    "dashboard.submit": "Start conversion",
    "dashboard.clear": "Clear selection",
    "dashboard.fineprint": "Deleted after {hours} hours. Processed on this server only.",
    "dashboard.jobs": "Jobs",
    "dashboard.zip": "Everything as ZIP",
    "dashboard.usage": "Today {jobs}/{jobs_max} conversions · {pages}/{pages_max} pages",
    "dashboard.usage_active": "{active} running, {queued} waiting",
    "dashboard.empty": "Nothing converted yet. Upload a file above — the result appears here.",
    "dashboard.empty.1": "Choose a file or drag it into the box above.",
    "dashboard.empty.2": "Tap “Start conversion”.",
    "dashboard.empty.3": "Finished jobs appear here with Markdown and JSON downloads.",

    # ------------------------------------------------------------------ Job
    "job.back": "← Back to overview",
    "job.status.done": "Done",
    "job.status.processing": "Processing",
    "job.status.queued": "Queued",
    "job.status.error": "Error",
    "job.pages": "{count} page",
    "job.pages_plural": "{count} pages",
    "job.seconds": "{value} s",
    "job.expires": "deleted on {when}",
    "job.note.title": "Note on the original.",
    "job.note.page": "Page",
    "job.note.row": "Row",
    "job.note.column": "Column",
    "job.note.read_as": "Read as",
    "job.pending": "The document is still being processed. This page does not refresh "
    "itself — {link} shows live progress.",
    "job.pending.link": "the overview",
    "job.download_all": "Download everything (ZIP)",
    "job.download_all_images": "Download everything — ZIP with {count} images",
    "job.copy": "Copy",
    "job.formats_note": "<strong>.md</strong> for notes and text, <strong>.json</strong> "
    "for your own programs. The Markdown file is usually enough.",
    "job.images.h": "Images from the document",
    "job.images.count": "{count} image extracted. The Markdown links to it, the ZIP "
    "contains it as a file.",
    "job.images.count_plural": "{count} images extracted. The Markdown links to them, the "
    "ZIP contains them as files.",
    "job.image.alt": "Image {seq} from the document",
    "job.image.alt_page": "Image {seq} from the document, page {page}",
    "job.preview.h": "Preview",
    "job.preview.raw": "Raw text with Markdown characters like <code>#</code> and "
    "<code>|</code>.",
    "job.preview.gone": "The result is no longer available. It was most likely deleted "
    "automatically.",
    "job.delete": "Delete this job now",

    # --------------------------------------------------------------- Account
    "account.title": "Account — {product}",
    "account.h1": "Account",
    "account.changed": "The password was changed.",
    "account.signed_in_as": "Signed in as",
    "account.unverified": "The email address is not confirmed yet.",
    "account.usage.h": "Usage",
    "account.usage.sub": "Purely to protect the server. The same for every account.",
    "account.usage.quota": "Quota",
    "account.usage.used": "Used",
    "account.usage.limit": "Limit",
    "account.usage.jobs_hour": "Conversions (hour)",
    "account.usage.jobs_day": "Conversions (day)",
    "account.usage.pages_day": "Pages (day)",
    "account.usage.bytes_day": "Data volume (day)",
    "account.usage.active": "Running at once",
    "account.password.h": "Change password",
    "account.password.current": "Current password",
    "account.password.new": "New password",
    "account.password.hint": "At least 10 characters.",
    "account.password.repeat": "Repeat new password",
    "account.password.note": "All other sign-ins will be ended.",
    "account.password.submit": "Save password",
    "account.delete.h": "Delete account",
    "account.delete.p": "Account, jobs and all files are deleted immediately and for good.",
    "account.delete.confirm": "Type {word} to confirm",
    "account.delete.word": "DELETE",
    "account.delete.submit": "Delete account permanently",

    # ----------------------------------------------------------------- Admin
    "admin.title": "Administration — {product}",
    "admin.h1": "Administration",
    "admin.saved": "The limits were saved.",
    "admin.load.h": "Load",
    "admin.load.queued": "waiting",
    "admin.load.processing": "running",
    "admin.load.users": "accounts",
    "admin.load.done": "done (24 h)",
    "admin.load.errors": "errors (24 h)",
    "admin.load.avg": "average (24 h)",
    "admin.limits.h": "Technical limits",
    "admin.limits.sub": "Take effect immediately for every account. Server protection "
    "only — no tiers, nothing for sale.",
    "admin.limits.default": "Default from the configuration: {value}",
    "admin.limits.submit": "Save limits",
    "admin.users.h": "Accounts",
    "admin.users.email": "Email",
    "admin.users.status": "Status",
    "admin.users.jobs": "Jobs",
    "admin.users.last_seen": "Last active",
    "admin.users.action": "Action",
    "admin.users.admin_badge": "Administration",
    "admin.users.active": "active",
    "admin.users.inactive": "deactivated",
    "admin.users.unconfirmed": "unconfirmed",
    "admin.users.never": "never",
    "admin.users.deactivate": "Deactivate",
    "admin.users.activate": "Activate",
    "admin.users.own": "your own account",
    "admin.users.note": "Passwords are stored as Argon2id hashes and deliberately cannot "
    "be viewed here.",
    "admin.failed.h": "Recently failed",
    "admin.failed.time": "Time",
    "admin.failed.reason": "Reason",
    "admin.failed.account": "Account",
    "admin.failed.note": "File names and content are deliberately not logged.",
    "admin.failed.none": "No failed jobs.",

    # ---------------------------------------------------------------- Rechtes
    "imprint.title": "Imprint — {product}",
    "imprint.description": "Imprint and provider identification for {product}.",
    "imprint.h1": "Imprint",
    "imprint.legal_note": "German law requires this page (§ 5 DDG). The German version is "
    "the legally binding one: {link}.",
    "imprint.unconfigured": "Not configured yet.",
    "imprint.unconfigured.p": "The mandatory details under § 5 DDG are still missing. They "
    "are set through the environment variables {vars}. Nothing is invented here.",
    "imprint.none": "— not configured —",
    "imprint.provider.h": "Details under § 5 DDG",
    "imprint.contact.h": "Contact",
    "imprint.contact.email": "Email",
    "imprint.contact.phone": "Phone",
    "imprint.vat.h": "VAT identification number",
    "imprint.responsible.h": "Responsible for the content",
    "imprint.dispute.h": "Consumer dispute resolution",
    "imprint.dispute.p": "We are neither willing nor obliged to take part in dispute "
    "resolution proceedings before a consumer arbitration board.",
    "imprint.oss.h": "Open source software in use",
    "imprint.oss.p": "The conversion uses free software. The full list with licences and "
    "copyright notices is available under {link}. {product} is an independent service and "
    "is not affiliated with the authors of the libraries it uses.",

    "privacy.title": "Privacy — {product}",
    "privacy.description": "Privacy notice for {product}: what happens to uploaded "
    "documents, how long they are kept and what rights you have.",
    "privacy.h1": "Privacy notice",
    "privacy.legal_note": "This is a translation for convenience. The German version is "
    "the legally binding one: {link}.",
    "privacy.unconfigured": "Controller not configured yet.",
    "privacy.unconfigured.p": "Without that detail this text is incomplete. See {link}.",
    "privacy.controller.h": "Controller",
    "privacy.uploads.h": "What happens to uploaded documents",
    "privacy.uploads.p1": "Uploaded files are processed exclusively on this service's own "
    "server. The conversion runs locally, using free software on that same server.",
    "privacy.uploads.p2": "<strong>No document content is transmitted to third "
    "parties.</strong> In particular not to:",
    "privacy.uploads.l1": "OpenAI, Anthropic, Google or other providers of language models",
    "privacy.uploads.l2": "external OCR or text recognition services",
    "privacy.uploads.l3": "external image analysis services",
    "privacy.uploads.l4": "external analytics, statistics or tracking providers",
    "privacy.uploads.l5": "error reporting services",
    "privacy.uploads.p3": "Document content, recognised text and file names are never "
    "written to application logs. Only technical events are logged, such as error types, "
    "duration and page count.",
    "privacy.retention.h": "Retention",
    "privacy.retention.p": "Uploaded files and generated results are deleted automatically "
    "after <strong>{hours} hours</strong>. The original file is removed shortly after "
    "processing finishes. Every job can also be deleted immediately by hand at any time.",
    "privacy.account.h": "Account and purposes of processing",
    "privacy.account.p": "Stored are: email address, an Argon2id hash of the password "
    "(never the password itself), the time of registration and of the last sign-in, plus "
    "job data (file name, file type, size, page count, status, timestamps). The legal "
    "basis is Art. 6(1)(b) GDPR (performance of the usage relationship) and Art. 6(1)(f) "
    "GDPR for protecting the service against abuse.",
    "privacy.mail.h": "Email delivery",
    "privacy.mail.p1": "Confirmation and password links are sent via Google's email "
    "service (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Ireland). "
    "Only the email address and the link are transmitted — <strong>never document content "
    "or file names</strong>.",
    "privacy.mail.p2": "These emails are plain text, contain no tracking pixels and no "
    "redirected links. Whether or when a message was opened is not recorded.",
    "privacy.cookies.h": "Cookies",
    "privacy.cookies.p": "Only technically necessary cookies are set: a session cookie for "
    "signing in, a cookie protecting forms against cross-site submission (CSRF), and a "
    "cookie storing your chosen language. All are required for operation and therefore do "
    "not require consent under § 25(2) TDDDG. There are no tracking, advertising or "
    "analytics cookies, and deliberately no cookie banner.",
    "privacy.analytics.h": "Audience measurement",
    "privacy.analytics.p1": "To see how often the public pages are viewed, a self-hosted "
    "instance of <strong>Plausible Analytics</strong> runs on this same server. No external "
    "service is involved; the data does not leave the server. The counting script is served "
    "from our own domain, so the page opens no connection to any third-party host.",
    "privacy.analytics.p2": "Recorded per view:",
    "privacy.analytics.l1": "the page viewed and the referring address",
    "privacy.analytics.l2": "browser, operating system and device type, broadly categorised",
    "privacy.analytics.l3": "the country, derived from the IP address",
    "privacy.analytics.p3": "<strong>The IP address is not stored.</strong> Together with a "
    "daily rotating random value it is turned into a checksum, used solely to count repeat "
    "views within a single day and attributable to no one afterwards. No cookies are set "
    "and nothing is stored on or read from the device — so neither consent under § 25 TDDDG "
    "nor a cookie banner is required. The legal basis is the legitimate interest in "
    "data-minimising audience measurement, Art. 6(1)(f) GDPR.",
    "privacy.analytics.p4": "<strong>The signed-in area is not measured.</strong> Job "
    "identifiers appear in the address bar there, and those have no business in a "
    "statistic. Only the publicly accessible pages are measured.",
    "privacy.logs.h": "Server logs",
    "privacy.logs.p": "To protect against abuse, IP addresses are used briefly for counters "
    "(requests per minute, sign-in attempts). Those counters are deleted after two days at "
    "the latest. The service runs behind a content delivery network, which forwards the "
    "request technically and processes connection data in doing so.",
    "privacy.rights.h": "Your rights",
    "privacy.rights.p": "Access, rectification, erasure, restriction, data portability and "
    "objection under Art. 15–21 GDPR. The account can be deleted in full at any time under "
    "{link}; all associated data and files are removed immediately. You also have the right "
    "to lodge a complaint with a data protection supervisory authority.",

    "terms.title": "Terms of use — {product}",
    "terms.description": "Terms of use for {product}: free use, fair-use limits and result "
    "quality.",
    "terms.h1": "Terms of use",
    "terms.legal_note": "This is a translation for convenience. The German version is the "
    "legally binding one: {link}.",
    "terms.unconfigured": "Operator not configured yet.",
    "terms.unconfigured.p": "See {link}.",
    "terms.1.h": "1. Subject matter",
    "terms.1.p": "{product} converts uploaded documents and images into Markdown and a "
    "structured JSON representation. The service is free. There are no paid features, no "
    "tiers and no subscription.",
    "terms.2.h": "2. Account",
    "terms.2.p": "An account is required. Credentials must be kept secret. An account may "
    "not be passed on to third parties. The account can be deleted at any time by its owner.",
    "terms.3.h": "3. Fair use",
    "terms.3.p": "Technical limits protect the server: currently {mb} MB per file, {files} "
    "files per upload, {pages} pages per document, {per_hour} conversions per hour and "
    "{per_day} per day. These values may be adjusted to keep the service running. "
    "Automated bulk use, attempts to circumvent the limits and operating across multiple "
    "accounts are not permitted.",
    "terms.4.h": "4. Content",
    "terms.4.p": "Only files you hold the necessary rights to may be uploaded. Unlawful "
    "content is prohibited. The uploading person alone is responsible for the content "
    "uploaded.",
    "terms.5.h": "5. Availability and data loss",
    "terms.5.p": "The service is provided without any availability guarantee. Files and "
    "results are deleted automatically after {hours} hours — the service is <strong>not a "
    "storage location and not an archive</strong>. Keep your own copies of the results.",
    "terms.6.h": "6. Result quality",
    "terms.6.p": "The conversion is automatic. The goal is to lose as little information as "
    "technically possible: nothing is summarised, rewritten or corrected. Even so, "
    "error-free recognition cannot be guaranteed — particularly with scanned originals, "
    "handwriting or complex tables. Markdown cannot represent certain layout features; the "
    "JSON output is more structure-faithful. Check results before relying on them.",
    "terms.7.h": "7. Suspension",
    "terms.7.p": "Accounts that endanger operation or breach these terms may be deactivated "
    "without prior notice.",
    "terms.8.h": "8. Liability",
    "terms.8.p": "Liability follows statutory provisions. For a service provided free of "
    "charge, liability is — as far as legally permissible — limited to intent and gross "
    "negligence. Liability for damages arising from injury to life, body or health remains "
    "unaffected.",

    "licenses.title": "Open source licences — {product}",
    "licenses.description": "List of the open source components used by {product}, with "
    "version, licence and copyright notice.",
    "licenses.h1": "Open source licences",
    "licenses.intro": "{product} uses free software. Below are the components in use, with "
    "version, licence and copyright notice. {product} is an independent service and is not "
    "affiliated with the authors of these components.",
    "licenses.missing": "The licence overview could not be loaded.",

    # ---------------------------------------------------------- Fehlermeldungen
    "error.unsupported_type": "This file format is not supported. Possible formats: {list}.",
    "error.type_mismatch": "The file content does not match its extension. Please upload "
    "the original file.",
    "error.empty_file": "The file is empty.",
    "error.file_too_large": "The file is larger than allowed.",
    "error.too_many_files": "You selected too many files at once.",
    "error.too_many_pages": "The document has more pages than allowed.",
    "error.queue_full": "Your queue is full. Wait until the running conversions finish.",
    "error.hourly_limit": "You have reached the hourly quota. Please try again later.",
    "error.daily_limit": "You have reached the daily quota. It resets tomorrow.",
    "error.pages_limit": "You have reached today's page quota.",
    "error.volume_limit": "You have reached today's data volume.",
    "error.server_busy": "A lot of conversions are running right now. Please try again in "
    "a few minutes.",
    "error.timeout": "Processing took too long and was cancelled.",
    "error.conversion_failed": "The document could not be read. It may be damaged or "
    "password protected.",
    "error.engine_unreachable": "Processing is currently unavailable. The job stays in the "
    "queue.",
    "error.engine_error": "Something went wrong during processing.",
    "error.unsupported": "This document could not be processed.",
    "error.no_files": "No file was selected.",
    "error.encrypted_pdf": "This PDF is password protected and cannot be read.",
    "error.generic": "Something went wrong. Please try again.",
    "error.rate_limited": "Too many requests. Please wait a moment.",
    "error.upload_too_large": "The upload is too large.",
    "error.form_expired": "The form has expired. Please reload the page.",
    "error.not_found": "This page does not exist.",
    "error.unexpected": "An unexpected error occurred. Please try again.",
    "error.login_required": "Please sign in.",
    "error.file_missing": "This file does not exist.",
    "error.address_missing": "This address does not exist.",
    "error.request_too_large": "The request is too large.",
    "error.register_flood": "Too many registrations from this connection. Please try later.",
    "error.email_invalid": "Please enter a valid email address.",
    "error.password_mismatch": "The two passwords do not match.",
    "error.password_short": "The password needs at least {min} characters.",
    "error.password_long": "The password is too long.",
    "error.password_blank": "The password cannot consist of spaces only.",
    "error.accept_required": "Please accept the terms of use and the privacy notice.",
    "error.verify_flood_ip": "Too many requests from this connection. Please try later.",
    "error.verify_flood_mail": "This address has already received several emails. Please "
    "wait an hour.",
    "error.login_wrong": "Email address or password is not correct.",
    "error.account_disabled": "This account is deactivated.",
    "error.email_unverified": "Please confirm your email address first, using the link we "
    "sent you. No email? Under “Resend confirmation email” we'll send it again.",
    "error.login_flood": "Too many sign-in attempts. Please wait 15 minutes and try again.",
    "error.forgot_flood": "Too many requests. Please try again later.",
    "error.reset_link_dead": "This link has expired or has already been used.",
    "error.job_missing": "This job does not exist.",
    "error.format_missing": "This format does not exist.",
    "error.result_gone": "The result is no longer available.",
    "error.image_missing": "This image does not exist.",
    "error.image_gone": "The image is no longer available.",
    "error.zip_empty": "No results were selected.",
    "error.zip_nothing": "There are no finished results to download.",
    "error.password_current_wrong": "The current password is not correct.",
    "error.password_new_mismatch": "The two new passwords do not match.",
    "error.delete_confirm": "Type DELETE to confirm.",
    "error.admin_self": "You cannot deactivate your own account here.",
    "error.max_size_hint": "The limit is {mb} MB.",
    "error.pages_hint": "This one has {count}, the limit is {max}.",
    "error.rejected_file": "“{name}”: {reason}",
    # Bereits fertig zusammengesetzter Text — die Ausnahme traegt nur Schluessel.
    "error.passthrough": "{text}",

    # -------------------------------------------------------------- Hinweise
    "info.verify_sent.h": "Email on its way",
    "info.verify_sent.p": "If the address belongs to an account that is still unconfirmed, "
    "we've sent a new confirmation link. It is valid for 24 hours. Nothing there? Please "
    "check your spam folder too.",
    "info.verify_dead.h": "Link not valid",
    "info.verify_dead.p": "This confirmation link has expired or has already been used.",
    "info.verified.h": "Email confirmed",
    "info.verified.p": "Your address is confirmed. You can sign in now.",
    "info.to_login": "Go to sign-in",
    "info.forgot_sent.h": "Email on its way",
    "info.forgot_sent.p": "If there is an account for this address, an email with a reset "
    "link is on its way. The link is valid for one hour.",
    "info.password_changed.h": "Password changed",
    "info.password_changed.p": "You can now sign in with the new password.",

    # ---------------------------------------------------------------- E-Mails
    "mail.verify.subject": "{product}: confirm your email address",
    "mail.verify.body": """Hello,

please confirm your email address for {product}:

{link}

The link is valid for 24 hours. If you did not sign up, simply ignore this
message — nothing further will happen.
""",
    "mail.reset.subject": "{product}: reset your password",
    "mail.reset.body": """Hello,

you can set a new password using this link:

{link}

The link is valid for 1 hour and works only once.
If you did not request it, ignore this message — your existing password
stays valid and unchanged.
""",

    # ------------------------------------------------------- Texte im Ergebnis
    "result.links.h": "Links in the document",
    "result.links.intro": "These links exist in the PDF as clickable annotations and do "
    "not appear in the body text.",
    "result.links.page": "Page {page}",
    "result.repeated.h": "Repeating page elements",
    "result.repeated.intro": "This text appears on nearly every page of the original "
    "(header, footer or watermark). It is listed here once instead of repeated on every "
    "page. The JSON output still contains it unchanged at every occurrence.",
    "note.image_lowres": "The text on this original is only about {height} pixels "
    "high{size}. For reliable text recognition it should be at least {min}. Individual "
    "characters may therefore be read incorrectly. Best to retake the original closer up "
    "and at full camera resolution.",
    "note.image_lowres.size": " ({width} × {height} pixels)",
    "note.pdf_lowres": "This PDF contains scanned pages at {width} × {height} pixels — "
    "about {dpi} dots per inch, where {min} is recommended. Individual characters may "
    "therefore be read incorrectly. Best to rescan at at least 300 dots per inch.",
    "note.units.one": "One cell in a unit column does not resolve to a known unit",
    "note.units.many": "{count} cells in unit columns do not resolve to known units",
    "note.units.tail": "{lead} — the text recognition probably misread them. The values "
    "appear unchanged in the result and are listed individually below; nothing is "
    "corrected, because that would be guesswork.",
    "note.file.h": "Note on the original",
    "note.file.cells": "Flagged cells (kept unchanged):",
    "note.file.line": "- {place}, row \"{row}\", column \"{column}\": read as \"{value}\"",
    "note.file.page": "Page {page}",
    "note.file.table": "Table",
    "note.file.unnamed": "unnamed",

    # ---------------------------------------------------------- Browser-Texte
    "js.new": "new",
    "js.since": "for {value}",
    "js.pages.one": "{count} page",
    "js.pages.many": "{count} pages",
    "js.minutes": "{min} min {sec} s",
    "js.seconds": "{value} s",
    "js.usage_active": "{active} running, {queued} waiting",
    "js.rejected.one": "One file was not accepted:",
    "js.rejected.many": "Some files were not accepted:",
    "js.uploading": "Uploading …",
    "js.checking": "Uploaded — checking …",
    "js.submit": "Start conversion",
    "js.uploaded.one": "1 file uploaded. The conversion is running — the job is in the "
    "list below.",
    "js.uploaded.many": "{count} files uploaded. The conversion is running — the jobs are "
    "in the list below.",
    "js.upload_rejected": "The upload was rejected.",
    "js.connection_lost": "The connection was interrupted. Please try again.",
    "js.progress_aria": "Upload progress",
    "js.ahead.one": "1 job ahead",
    "js.ahead.many": "{count} jobs ahead",
    "js.ahead.next": "next in line",
    "js.usage": "Today {jobs}/{jobs_max} conversions · {pages}/{pages_max} pages",
    "js.status.queued": "Queued",
    "js.status.processing": "Processing",
    "js.status.done": "Done",
    "js.status.error": "Error",
    "js.note.lowres": "Original is coarse — individual characters may be read incorrectly.",
    "js.view": "View",
    "js.download_md": "Download Markdown: {name}",
    "js.download_json": "Download JSON: {name}",
    "js.delete_aria": "Delete job: {name}",
    "js.delete_title": "Delete job",
    "js.delete_confirm": "Delete this job and all its results for good?",
    "js.empty": "Nothing converted yet. Upload a file above — the result appears here.",
    "js.empty.1": "Choose a file or drag it into the box above.",
    "js.empty.2": "Tap “Start conversion”.",
    "js.empty.3": "Finished jobs appear here with Markdown and JSON downloads.",
    "js.copied": "Markdown copied to the clipboard.",
    "js.copy_failed": "Copying didn't work. Please select the text and copy it manually.",
}
