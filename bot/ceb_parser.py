"""CEB power outage website parser.

Fetches and parses power outage data directly from the CEB website,
matching the TypeScript implementation in mauritius-dataset-electricity.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# CEB website URL
CEB_URL = "https://ceb.mu/customer-corner/power-outage-information"

# Mauritius timezone (UTC+4)
MAURITIUS_TZ = ZoneInfo("Indian/Mauritius")
UTC_TZ = ZoneInfo("UTC")

# French month names for date parsing
FRENCH_MONTHS = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

# Regex pattern for parsing French date strings
# Format: "Le dimanche 13 mars 2022 de 09:30:00 à 13:00:00"
DATE_PATTERN = re.compile(
    r"Le\s+\w+\s+(\d{1,2})\s+(\w+)\s+(\d{4})\s+de\s+(\d{2}:\d{2}:\d{2})\s+[àa]\s+(\d{2}:\d{2}:\d{2})",
    re.IGNORECASE
)


async def fetch_ceb_page(url: str = CEB_URL) -> str:
    """Fetch HTML content from CEB website.

    Args:
        url: The CEB URL to fetch from.

    Returns:
        The HTML content as a string.

    Raises:
        httpx.HTTPError: If the request fails.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def extract_district_data(html: str) -> Dict[str, str]:
    """Extract district HTML data from JavaScript variable in page.

    The CEB page contains a JavaScript variable `arDistrictLocations` that maps
    district names to HTML table strings.

    Args:
        html: The full HTML page content.

    Returns:
        Dictionary mapping district names to their HTML table strings.
    """
    # Match the JavaScript variable that contains all district data
    # Pattern: var arDistrictLocations = {"district": "html", ...};
    match = re.search(r'var arDistrictLocations = ({.+});', html)
    if not match:
        logger.error("Could not find arDistrictLocations in page HTML")
        return {}

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse district data JSON: {e}")
        return {}


def parse_french_date(date_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse a French-format date string into UTC datetime objects.

    Format: "Le dimanche 13 mars 2022 de 09:30:00 à 13:00:00"

    Args:
        date_str: The French date string to parse.

    Returns:
        Tuple of (from_time, to_time) as UTC datetime objects,
        or (None, None) if parsing fails.
    """
    if not date_str or not date_str.strip():
        return None, None

    # Normalize whitespace
    date_str = re.sub(r'\s+', ' ', date_str).strip()

    match = DATE_PATTERN.match(date_str)
    if not match:
        logger.warning(f"Could not parse date string: {date_str}")
        return None, None

    day_str, month_str, year_str, from_time_str, to_time_str = match.groups()

    # Parse month name (French)
    month = FRENCH_MONTHS.get(month_str.lower())
    if not month:
        logger.warning(f"Unknown French month: {month_str}")
        return None, None

    try:
        day = int(day_str)
        year = int(year_str)

        # Parse times
        from_parts = from_time_str.split(':')
        to_parts = to_time_str.split(':')

        from_hour, from_min, from_sec = int(from_parts[0]), int(from_parts[1]), int(from_parts[2])
        to_hour, to_min, to_sec = int(to_parts[0]), int(to_parts[1]), int(to_parts[2])

        # Create datetime in Mauritius timezone
        from_time = datetime(year, month, day, from_hour, from_min, from_sec, tzinfo=MAURITIUS_TZ)
        to_time = datetime(year, month, day, to_hour, to_min, to_sec, tzinfo=MAURITIUS_TZ)

        # Handle case where end time is past midnight (next day)
        if to_time < from_time:
            to_time += timedelta(days=1)

        # Convert to UTC
        from_time_utc = from_time.astimezone(UTC_TZ)
        to_time_utc = to_time.astimezone(UTC_TZ)

        return from_time_utc, to_time_utc

    except (ValueError, IndexError) as e:
        logger.warning(f"Error parsing date components from '{date_str}': {e}")
        return None, None


def parse_table_html(html: str, district: str) -> List[Dict[str, Any]]:
    """Parse HTML table for a district and extract outage data.

    Args:
        html: HTML string containing the table for this district.
        district: The district name.

    Returns:
        List of outage dictionaries with date, locality, streets, district fields.
    """
    soup = BeautifulSoup(html, 'lxml')
    outages = []

    # Find all tables with IDs starting with "table-mauritius"
    # CSS selector: [id^=table-mauritius] tbody tr
    tables = soup.find_all('table', id=lambda x: x and x.startswith('table-mauritius'))

    for table in tables:
        tbody = table.find('tbody')
        if not tbody:
            continue

        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                date_text = cells[0].get_text(strip=True)
                locality = cells[1].get_text(strip=True)
                streets = cells[2].get_text(strip=True)

                # Skip rows with empty dates
                if not date_text:
                    continue

                outages.append({
                    'date': date_text,
                    'locality': locality,
                    'streets': streets,
                    'district': district,
                })

    return outages


def generate_outage_id(outage: Dict[str, Any]) -> str:
    """Generate MD5 hash ID for an outage.

    IMPORTANT: This must match the TypeScript implementation exactly.
    The hash is computed BEFORE adding the from/to fields, using only:
    - date
    - locality
    - streets
    - district

    Args:
        outage: Outage dictionary with date, locality, streets, district fields.

    Returns:
        MD5 hash as hexadecimal string.
    """
    # Create the object that will be hashed - must match TypeScript JSON.stringify order
    data = {
        'date': outage['date'],
        'locality': outage['locality'],
        'streets': outage['streets'],
        'district': outage['district'],
    }

    # JSON stringify with no spaces (matching JavaScript's JSON.stringify default)
    json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    return hashlib.md5(json_str.encode('utf-8')).hexdigest()


def categorize_outages(outages_by_district: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Categorize outages into 'today' and 'future' lists.

    'today' includes all outages where from_time is before end of today.
    'future' includes all outages where from_time is after end of today.

    Args:
        outages_by_district: Dictionary mapping district names to lists of outages.

    Returns:
        Dictionary with 'today' and 'future' keys containing lists of outages.
    """
    # Get end of today in local timezone
    now = datetime.now(MAURITIUS_TZ)
    end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    today_outages = []
    future_outages = []

    for outages in outages_by_district.values():
        for outage in outages:
            # Skip outages without valid from time
            if not outage.get('from'):
                continue

            # Parse the from time if it's a string
            from_time = outage['from']
            if isinstance(from_time, str):
                from_time = datetime.fromisoformat(from_time.replace('Z', '+00:00'))

            # Convert to local time for comparison
            from_time_local = from_time.astimezone(MAURITIUS_TZ)

            if from_time_local <= end_of_today:
                today_outages.append(outage)
            else:
                future_outages.append(outage)

    return {
        'today': today_outages,
        'future': future_outages,
    }


def remove_duplicates(outages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate outages based on ID, also filtering out empty dates.

    Args:
        outages: List of outage dictionaries.

    Returns:
        List of unique outages.
    """
    seen = {}
    for outage in outages:
        # Skip entries with empty dates
        if not outage.get('date'):
            continue
        outage_id = outage.get('id')
        if outage_id and outage_id not in seen:
            seen[outage_id] = outage
    return list(seen.values())


async def fetch_and_parse_outages() -> Dict[str, List[Dict[str, Any]]]:
    """Main entry point - fetch CEB page and parse all outages.

    Returns:
        Dictionary with 'today' and 'future' keys containing lists of outages.
        Each outage has: id, date, locality, streets, district, from, to
    """
    logger.info("Fetching power outage data from CEB website...")

    # Fetch the page
    html = await fetch_ceb_page()

    # Extract district data from JavaScript variable
    district_data = extract_district_data(html)
    if not district_data:
        raise ValueError("No district data found in CEB page")

    logger.info(f"Found {len(district_data)} districts in CEB data")

    # Parse each district's HTML table
    outages_by_district = {}

    for district, district_html in district_data.items():
        raw_outages = parse_table_html(district_html, district)

        # Process each outage: generate ID, parse dates
        processed_outages = []
        for outage in raw_outages:
            # Generate ID before adding from/to (matches TypeScript)
            outage_id = generate_outage_id(outage)

            # Parse the French date string
            from_time, to_time = parse_french_date(outage['date'])

            if from_time and to_time:
                processed_outage = {
                    'id': outage_id,
                    'date': outage['date'],
                    'locality': outage['locality'],
                    'streets': outage['streets'],
                    'district': outage['district'],
                    'from': from_time.isoformat(),
                    'to': to_time.isoformat(),
                }
                processed_outages.append(processed_outage)
            else:
                logger.warning(f"Skipping outage with unparseable date: {outage['date']}")

        # Remove duplicates within this district
        outages_by_district[district] = remove_duplicates(processed_outages)
        logger.debug(f"District {district}: {len(outages_by_district[district])} outages")

    # Categorize into today/future
    result = categorize_outages(outages_by_district)

    logger.info(f"Parsed {len(result['today'])} today outages, {len(result['future'])} future outages")

    return result
