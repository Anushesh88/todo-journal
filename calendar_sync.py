import urllib.parse
import datetime

def format_date_gcal(date_str: str) -> str:
    """Formats YYYY-MM-DD into YYYYMMDD string for GCal URL."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y%m%d")
    except Exception:
        dt = datetime.date.today()
        return dt.strftime("%Y%m%d")

def generate_gcal_url(title: str, details: str = "", start_date: str = "", end_date: str = "") -> str:
    """
    Creates an instant 1-click Google Calendar Event Creation Web URL.
    """
    if not start_date:
        start_date = datetime.date.today().strftime("%Y-%m-%d")
    if not end_date:
        end_date = start_date

    sd_fmt = format_date_gcal(start_date)
    ed_fmt = format_date_gcal(end_date)
    
    # All day event format or next day for end date
    dates_param = f"{sd_fmt}/{ed_fmt}"

    base_url = "https://calendar.google.com/calendar/render"
    params = {
        "action": "TEMPLATE",
        "text": title,
        "details": details,
        "dates": dates_param
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def generate_ics_content(title: str, details: str = "", start_date: str = "", end_date: str = "") -> str:
    """
    Generates iCalendar (.ics) format string for universal calendar import.
    """
    if not start_date:
        start_date = datetime.date.today().strftime("%Y-%m-%d")
    if not end_date:
        end_date = start_date

    sd_fmt = format_date_gcal(start_date)
    ed_fmt = format_date_gcal(end_date)
    now_fmt = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    ics = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Streamlit ToDo Journal App//EN",
        "BEGIN:VEVENT",
        f"UID:task-{sd_fmt}-{hash(title)}@todojournal.app",
        f"DTSTAMP:{now_fmt}",
        f"DTSTART;VALUE=DATE:{sd_fmt}",
        f"DTEND;VALUE=DATE:{ed_fmt}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:{details.replace('\n', '\\n')}",
        "END:VEVENT",
        "END:VCALENDAR"
    ]
    return "\n".join(ics)
