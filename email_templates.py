"""
Premium Email Templates for MyLibrary
Color theme: teal #00d4aa, navy #0a1628, blue #3b82f6
"""

APP_NAME = "MyLibrary"
MAX_BOOKS = 3
FINE_PER_DAY = 5

def _wrap(body, preheader=''):
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<!--[if mso]><style>table,td{{font-family:Arial,sans-serif}}</style><![endif]-->
</head><body style="margin:0;padding:0;background:#050a15;font-family:'Segoe UI',Roboto,Arial,sans-serif;-webkit-font-smoothing:antialiased">
<span style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#050a15">{preheader}</span>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#050a15"><tr><td align="center" style="padding:40px 16px">

<!-- Outer glow wrapper -->
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">

<!-- Top glow effect -->
<tr><td align="center" style="padding-bottom:2px">
<table width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:90%">
<tr><td style="height:2px;background:linear-gradient(90deg,transparent,#00d4aa,#3b82f6,#8b5cf6,transparent);border-radius:2px"></td></tr>
</table>
</td></tr>

<!-- Main card -->
<tr><td style="background:#0b1527;border-radius:20px;overflow:hidden;border:1px solid rgba(0,212,170,0.1);box-shadow:0 0 80px rgba(0,212,170,0.06),0 25px 60px rgba(0,0,0,0.5)">

<!-- Header -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="height:4px;background:linear-gradient(90deg,#00d4aa,#00b894 25%,#3b82f6 50%,#8b5cf6 75%,#a78bfa)"></td></tr>
<tr><td style="padding:30px 44px 22px;text-align:center">
<table cellpadding="0" cellspacing="0" style="margin:0 auto"><tr>
<td style="width:42px;height:42px;background:linear-gradient(135deg,#00d4aa,#3b82f6);border-radius:10px;text-align:center;vertical-align:middle;font-size:22px;line-height:42px">&#128218;</td>
<td style="padding-left:12px">
<p style="margin:0;font-size:24px;font-weight:800;color:#00d4aa;letter-spacing:-0.5px">{APP_NAME}</p>
<p style="margin:2px 0 0;font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:3px;font-weight:600">DIGITAL LIBRARY</p>
</td>
</tr></table>
</td></tr>
<tr><td style="padding:0 44px"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,212,170,0.15),transparent)"></td></tr></table></td></tr>
</table>

<!-- Body -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:28px 44px 32px">{body}</td></tr>
</table>

<!-- Footer -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:0 44px"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,212,170,0.1),transparent)"></td></tr></table></td></tr>
<tr><td style="padding:22px 44px 18px;text-align:center">
<p style="margin:0 0 4px;color:#334155;font-size:11px">Automated message from {APP_NAME} &bull; Do not reply</p>
<p style="margin:0;color:#1e293b;font-size:10px">&copy; 2026 {APP_NAME} &mdash; Digital Library Management</p>
</td></tr>
<tr><td style="height:3px;background:linear-gradient(90deg,#00d4aa,#00b894 25%,#3b82f6 50%,#8b5cf6 75%,#a78bfa);border-radius:0 0 20px 20px"></td></tr>
</table>

</td></tr>

<!-- Bottom glow -->
<tr><td align="center" style="padding-top:2px">
<table width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:90%">
<tr><td style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,212,170,0.2),transparent)"></td></tr>
</table>
</td></tr>

</table>
</td></tr></table>
</body></html>'''


def _badge(emoji, size='48'):
    return f'<table cellpadding="0" cellspacing="0" style="margin:0 auto 14px"><tr><td style="width:{size}px;height:{size}px;background:linear-gradient(135deg,rgba(0,212,170,0.15),rgba(59,130,246,0.1));border:1px solid rgba(0,212,170,0.2);border-radius:14px;text-align:center;vertical-align:middle;font-size:{int(int(size)*0.5)}px;line-height:{size}px">{emoji}</td></tr></table>'


def _section(content, color='0,212,170', gradient=True):
    bg = f'linear-gradient(135deg,rgba({color},0.07),rgba(59,130,246,0.04))' if gradient else f'rgba({color},0.06)'
    return f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px"><tr><td style="background:{bg};border:1px solid rgba({color},0.18);border-radius:14px;padding:22px 24px">{content}</td></tr></table>'


def _info_row(label, value, color='#e2e8f0', mono=False):
    font = "font-family:'Courier New',monospace;" if mono else ""
    return f'<p style="margin:0 0 3px;color:#4a5568;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700">{label}</p><p style="margin:0 0 14px;color:{color};font-size:16px;font-weight:700;{font}">{value}</p>'


def _alert(text, color='245,158,11', icon='&#9888;&#65039;'):
    return f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:4px"><tr><td style="background:rgba({color},0.07);border-left:3px solid rgba({color},0.6);border-radius:0 10px 10px 0;padding:13px 18px"><p style="margin:0;color:rgba({color},1);font-size:12px;font-weight:600;line-height:1.5">{icon} {text}</p></td></tr></table>'


def _divider():
    return '<table width="100%" cellpadding="0" cellspacing="0" style="margin:6px 0"><tr><td style="height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.04),transparent)"></td></tr></table>'


def email_otp(otp, purpose='register'):
    is_reg = purpose == 'register'
    title = 'Verify Your Identity' if is_reg else 'Reset Your Password'
    desc = 'Enter this code to complete your registration' if is_reg else 'Enter this code to reset your password'
    emoji = '&#128272;' if is_reg else '&#128273;'

    digits = ''.join(f'<td style="width:44px;height:56px;background:linear-gradient(180deg,rgba(0,212,170,0.12),rgba(0,212,170,0.04));border:1px solid rgba(0,212,170,0.25);border-radius:10px;text-align:center;vertical-align:middle;font-size:28px;font-weight:800;color:#00d4aa;font-family:\'Courier New\',monospace;letter-spacing:0;{("margin-left:6px;" if i>0 else "")}">{d}</td><td width="6"></td>' for i, d in enumerate(str(otp)))

    body = f'''
{_badge(emoji)}
<h2 style="margin:0 0 6px;color:#fff;font-size:22px;font-weight:800;text-align:center;letter-spacing:-0.3px">{title}</h2>
<p style="margin:0 0 26px;color:#64748b;font-size:13px;text-align:center;line-height:1.5">{desc}</p>

{_section(f"""
<p style="margin:0 0 12px;color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:2.5px;font-weight:700;text-align:center">Verification Code</p>
<table cellpadding="0" cellspacing="0" style="margin:0 auto"><tr>{digits}</tr></table>
<p style="margin:14px 0 0;color:#475569;font-size:11px;text-align:center">&#9200; Expires in <strong style="color:#f59e0b">10 minutes</strong></p>
""")}

{_alert("Never share this code. " + APP_NAME + " staff will never ask for your OTP.", "239,68,68", "&#128274;")}
'''
    return _wrap(body, f'Your {APP_NAME} code: {otp}')


def email_borrow_approved(name, title, token, due_date):
    body = f'''
{_badge("&#9989;")}
<h2 style="margin:0 0 6px;color:#fff;font-size:22px;font-weight:800;text-align:center">Borrow Approved!</h2>
<p style="margin:0 0 24px;color:#64748b;font-size:13px;text-align:center">Hello <strong style="color:#cbd5e1">{name}</strong>, your request has been approved.</p>

{_section(f"""
{_info_row("Book", "&#128214; " + title, "#fff")}
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="50%" style="vertical-align:top">{_info_row("Token", token, "#00d4aa", True)}</td>
<td width="50%" style="vertical-align:top">{_info_row("Due Date", "&#128197; " + due_date)}</td>
</tr></table>
""")}

<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.12);border-radius:12px;padding:18px 22px">
<p style="margin:0 0 10px;color:#e2e8f0;font-size:13px;font-weight:700">&#128203; How to collect:</p>
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:4px 0;color:#94a3b8;font-size:12px"><span style="display:inline-block;width:20px;height:20px;background:rgba(0,212,170,0.1);border-radius:50%;text-align:center;line-height:20px;font-size:10px;color:#00d4aa;font-weight:800;margin-right:8px">1</span>Visit the library counter</td></tr>
<tr><td style="padding:4px 0;color:#94a3b8;font-size:12px"><span style="display:inline-block;width:20px;height:20px;background:rgba(0,212,170,0.1);border-radius:50%;text-align:center;line-height:20px;font-size:10px;color:#00d4aa;font-weight:800;margin-right:8px">2</span>Show your QR code or token</td></tr>
<tr><td style="padding:4px 0;color:#94a3b8;font-size:12px"><span style="display:inline-block;width:20px;height:20px;background:rgba(0,212,170,0.1);border-radius:50%;text-align:center;line-height:20px;font-size:10px;color:#00d4aa;font-weight:800;margin-right:8px">3</span>Collect and enjoy! &#128218;</td></tr>
</table>
</td></tr></table>

{_alert(f"Late return fine: &#8377;{FINE_PER_DAY}/day after " + due_date, "239,68,68", "&#9888;&#65039;")}
'''
    return _wrap(body, f'Borrow approved: "{title}"')


def email_return_success(name, title, fine):
    if fine > 0:
        fine_html = _section(f'''
<p style="margin:0 0 4px;color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;text-align:center">Late Return Fine</p>
<p style="margin:0 0 4px;color:#ef4444;font-size:32px;font-weight:800;text-align:center">&#8377;{fine}</p>
<p style="margin:0;color:#94a3b8;font-size:11px;text-align:center">Please pay at the library counter</p>
''', '239,68,68', False)
    else:
        fine_html = _section(f'''
<table cellpadding="0" cellspacing="0" style="margin:0 auto"><tr>
<td style="font-size:20px;vertical-align:middle">&#9989;</td>
<td style="padding-left:8px;color:#00d4aa;font-size:15px;font-weight:700">Returned on time &mdash; No fine!</td>
</tr></table>''', '0,212,170', False)

    body = f'''
{_badge("&#128215;")}
<h2 style="margin:0 0 6px;color:#fff;font-size:22px;font-weight:800;text-align:center">Book Returned</h2>
<p style="margin:0 0 24px;color:#64748b;font-size:13px;text-align:center">Hello <strong style="color:#cbd5e1">{name}</strong>, your return is confirmed.</p>

{_section(_info_row("Returned Book", "&#128214; " + title, "#fff"))}
{fine_html}

<p style="margin:8px 0 0;color:#64748b;font-size:12px;text-align:center;line-height:1.6">Thank you for using <strong style="color:#00d4aa">{APP_NAME}</strong>!<br>Happy reading &#128218;</p>
'''
    return _wrap(body, f'Return confirmed: "{title}"')


def email_admin_approval(name):
    features = [
        ("&#128214;", "Browse & search books"),
        ("&#128218;", f"Borrow up to {MAX_BOOKS} books"),
        ("&#127915;", "Digital library card"),
        ("&#128269;", "Join book waitlists"),
    ]
    feat_html = ''.join(f'<tr><td style="padding:5px 0;color:#94a3b8;font-size:12px"><span style="margin-right:8px">{icon}</span>{text}</td></tr>' for icon, text in features)

    body = f'''
{_badge("&#127881;", "56")}
<h2 style="margin:0 0 6px;color:#fff;font-size:24px;font-weight:800;text-align:center">Welcome Aboard!</h2>
<p style="margin:0 0 24px;color:#64748b;font-size:13px;text-align:center">Hello <strong style="color:#cbd5e1">{name}</strong>, your account is ready!</p>

{_section(f"""
<table cellpadding="0" cellspacing="0" style="margin:0 auto"><tr>
<td style="font-size:36px;vertical-align:middle">&#9989;</td>
<td style="padding-left:12px"><p style="margin:0;color:#00d4aa;font-size:18px;font-weight:800">Account Approved</p><p style="margin:4px 0 0;color:#64748b;font-size:12px">Full access granted by administrator</p></td>
</tr></table>
""", "0,212,170")}

<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.12);border-radius:12px;padding:18px 22px">
<p style="margin:0 0 10px;color:#e2e8f0;font-size:13px;font-weight:700">&#128640; You can now:</p>
<table width="100%" cellpadding="0" cellspacing="0">{feat_html}</table>
</td></tr></table>

<p style="margin:16px 0 0;color:#64748b;font-size:12px;text-align:center">Log in and start exploring! &#128218;</p>
'''
    return _wrap(body, f'Welcome to {APP_NAME}! Your account is approved.')


def email_overdue(name, title, due_fmt, fine):
    body = f'''
{_badge("&#9888;&#65039;", "56")}
<h2 style="margin:0 0 6px;color:#ef4444;font-size:22px;font-weight:800;text-align:center">Overdue Notice</h2>
<p style="margin:0 0 24px;color:#64748b;font-size:13px;text-align:center">Dear <strong style="color:#cbd5e1">{name}</strong>, please return this book.</p>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px"><tr><td style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);border-radius:14px;overflow:hidden">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:3px;background:linear-gradient(90deg,#ef4444,#f59e0b)"></td></tr></table>
<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="padding:22px 24px">
{_info_row("Overdue Book", "&#128214; " + title, "#fff")}
{_divider()}
<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px"><tr>
<td width="50%" style="vertical-align:top">{_info_row("Was Due", "&#128197; " + due_fmt, "#fbbf24")}</td>
<td width="50%" style="vertical-align:top;text-align:right">
<p style="margin:0 0 3px;color:#4a5568;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700">Fine</p>
<p style="margin:0;color:#ef4444;font-size:30px;font-weight:800">&#8377;{fine}</p>
</td>
</tr></table>
</td></tr></table>
</td></tr></table>

{_alert(f"Fine increases by &#8377;{FINE_PER_DAY} every day. Return immediately!", "245,158,11", "&#9200;")}

<p style="margin:12px 0 0;color:#475569;font-size:11px;text-align:center">Library: Mon&ndash;Sat, 9 AM &ndash; 5 PM</p>
'''
    return _wrap(body, f'OVERDUE: "{title}" — Fine: Rs.{fine}')


def email_reservation_ready(name, title, token):
    body = f'''
{_badge("&#127881;", "56")}
<h2 style="margin:0 0 6px;color:#fff;font-size:22px;font-weight:800;text-align:center">Your Book is Ready!</h2>
<p style="margin:0 0 24px;color:#64748b;font-size:13px;text-align:center">Hello <strong style="color:#cbd5e1">{name}</strong>, great news!</p>

{_section(f"""
<p style="margin:0 0 4px;color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;text-align:center">Now Available</p>
<p style="margin:0 0 18px;color:#fff;font-size:18px;font-weight:800;text-align:center">&#128214; {title}</p>
<table cellpadding="0" cellspacing="0" style="margin:0 auto"><tr><td style="background:linear-gradient(135deg,rgba(0,212,170,0.15),rgba(0,212,170,0.05));border:2px solid rgba(0,212,170,0.3);border-radius:10px;padding:14px 28px;text-align:center">
<p style="margin:0 0 2px;color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700">Collection Token</p>
<p style="margin:0;color:#00d4aa;font-size:20px;font-weight:800;font-family:'Courier New',monospace;letter-spacing:3px">{token}</p>
</td></tr></table>
""")}

{_alert("Collect within <strong>3 days</strong> or reservation expires.", "245,158,11", "&#9200;")}

<p style="margin:12px 0 0;color:#475569;font-size:11px;text-align:center">Show QR code or token at the counter</p>
'''
    return _wrap(body, f'"{title}" is ready for pickup!')
