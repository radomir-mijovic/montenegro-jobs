import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)

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

# Genitive case (used with "do" - until): "08. februara"
MONTHS_GENITIVE_TO_MAP: dict[str, str] = {
    "januara": "01",
    "februara": "02",
    "marta": "03",
    "aprila": "04",
    "maja": "05",
    "juna": "06",
    "jula": "07",
    "avgusta": "08",
    "septembra": "09",
    "oktobra": "10",
    "novembra": "11",
    "decembra": "12",
}


def convert_date(
    date_str: str, source: str | None = None, date_source: str | None = None
) -> date | None:
    """Function that convert str date to datetime.date object

    Args:
        date_str(str): date in str format

    Returns:
        datetime.date object
    """
    date_str = date_str.strip().lower().rstrip(".")

    try:
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
            # Otherwise, treat as Serbian month name format: "23. januar 2026" or "13. februara"
            else:
                clean_str = date_str.replace(".", "").strip()
                parts = clean_str.split()

                if len(parts) == 2:
                    # Format: "13. februara" (day and month only, no year)
                    day, month_name = parts
                    # Try both nominative and genitive forms
                    month = MONTHS_TO_MAP.get(month_name) or MONTHS_GENITIVE_TO_MAP.get(month_name)

                    if not month:
                        raise ValueError(f"Unknown month: {month_name}")

                    # Assume current year
                    current_year = datetime.now().year
                    parsed_date = datetime.strptime(f"{day.zfill(2)}.{month}.{current_year}", "%d.%m.%Y").date()

                    # If the date has already passed this year, assume next year
                    if parsed_date < date.today():
                        parsed_date = datetime.strptime(f"{day.zfill(2)}.{month}.{current_year + 1}", "%d.%m.%Y").date()

                    return parsed_date

                elif len(parts) == 3:
                    # Format: "23. januar 2026"
                    day, month_name, year = parts
                    # Try both nominative and genitive forms
                    month = MONTHS_TO_MAP.get(month_name) or MONTHS_GENITIVE_TO_MAP.get(month_name)

                    if not month:
                        raise ValueError(f"Unknown month: {month_name}")
                    numeric_date = f"{day.zfill(2)}.{month}.{year}"
                    return datetime.strptime(numeric_date, "%d.%m.%Y").date()
                else:
                    raise ValueError(f"Cannot parse date: {date_str}")

        # Serbian month name format without dots: "14 januar 2026" or "11 februar" (no year)
        else:
            parts = date_str.split()

            if len(parts) == 2:
                # Format: "11 februar" (no year)
                day, month_name = parts
                # Try both nominative and genitive forms
                month = MONTHS_TO_MAP.get(month_name) or MONTHS_GENITIVE_TO_MAP.get(month_name)

                if not month:
                    raise ValueError(f"Unknown month: {month_name}")

                # Assume current year
                current_year = datetime.now().year
                parsed_date = datetime.strptime(f"{day.zfill(2)}.{month}.{current_year}", "%d.%m.%Y").date()

                # If the date has already passed this year, assume next year
                if parsed_date < date.today():
                    parsed_date = datetime.strptime(f"{day.zfill(2)}.{month}.{current_year + 1}", "%d.%m.%Y").date()

                return parsed_date

            elif len(parts) == 3:
                # Format: "14 januar 2026"
                day, month_name, year = parts
                # Try both nominative and genitive forms
                month = MONTHS_TO_MAP.get(month_name) or MONTHS_GENITIVE_TO_MAP.get(month_name)

                if not month:
                    raise ValueError(f"Unknown month: {month_name}")
                numeric_date = f"{day.zfill(2)}.{month}.{year}"
                return datetime.strptime(numeric_date, "%d.%m.%Y").date()
            else:
                raise ValueError(f"Cannot parse date: {date_str}")

    except Exception as e:
        logger.warning(f"Unable to format date for {source} for {date_source}: {e}")
        return None
