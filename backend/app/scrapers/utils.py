from datetime import date, datetime

MONTHS_TO_MAP: dict[str, str] = {
    "januar": "01",
    "februar": "02",
    "mart": "03",
    "april": "04",
    "maj": "05",
    "jun": "06",
    "jul": "07",
    "avgust": "08",
    "septembar": "09",
    "oktobar": "10",
    "novembar": "11",
    "decembar": "12",
}


def convert_date(date_str: str) -> date:
    """Function that convert str date to datetime.date object

    Args:
        date_str(str): date in str format

    Returns:
        datetime.date object
    """
    date_str = date_str.strip().lower().rstrip(".")

    if "/" in date_str:
        return datetime.strptime(date_str, "%d/%m/%Y").date()

    elif "." in date_str:
        parts = [p.strip() for p in date_str.split(".") if p.strip()]
        # Check if it's numeric format (DD.MM.YYYY) - all parts should be digits
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            day = parts[0].zfill(2)
            month = parts[1].zfill(2)
            year = parts[2]
            numeric_date = f"{day}.{month}.{year}"
            return datetime.strptime(numeric_date, "%d.%m.%Y").date()
        # Otherwise, treat as Serbian month name format: "23. januar 2026"
        else:
            clean_str = date_str.replace(".", "").strip()
            parts = clean_str.split()
            if len(parts) != 3:
                raise ValueError(f"Cannot parse date: {date_str}")
            day, month_name, year = parts
            month = MONTHS_TO_MAP.get(month_name)
            if not month:
                raise ValueError(f"Unknown month: {month_name}")
            numeric_date = f"{day.zfill(2)}.{month}.{year}"
            return datetime.strptime(numeric_date, "%d.%m.%Y").date()

    # Serbian month name format without dots: "14 januar 2026"
    else:
        parts = date_str.split()
        if len(parts) != 3:
            raise ValueError(f"Cannot parse date: {date_str}")
        day, month_name, year = parts
        month = MONTHS_TO_MAP.get(month_name)
        if not month:
            raise ValueError(f"Unknown month: {month_name}")
        numeric_date = f"{day.zfill(2)}.{month}.{year}"
        return datetime.strptime(numeric_date, "%d.%m.%Y").date()
