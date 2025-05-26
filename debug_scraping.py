import requests
from bs4 import BeautifulSoup
import json
import re

def debug_scraping():
    """Debug the course scraping to see what's happening"""

    url = "https://pakmanstudios.com/gspro-course-list/"

    try:
        print(f"🔍 Fetching URL: {url}")

        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        print(f"📊 Response status: {response.status_code}")
        print(f"📏 Response length: {len(response.text)} characters")

        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if there are any tables
        tables = soup.find_all("table")
        print(f"🔢 Found {len(tables)} table(s)")

        if not tables:
            print("❌ No tables found on the page")
            # Let's see what the page actually contains
            print("\n📄 First 500 characters of page content:")
            print(response.text[:500])
            return

        # Check each table for content
        for i, table in enumerate(tables):
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                print(f"📋 Table {i+1}: Found {len(rows)} rows in tbody")

                # Show first few rows for debugging
                for j, row in enumerate(rows[:3]):
                    cols = row.find_all("td")
                    if cols:
                        first_col_text = cols[0].get_text(strip=True)
                        print(f"   Row {j+1}: '{first_col_text}' (cols: {len(cols)})")
            else:
                print(f"📋 Table {i+1}: No tbody found")

        # Try the original scraping logic
        courses = set()
        suffix_pattern = re.compile(r'_[A-Z]{2,10}$')

        for row in soup.select("table tbody tr"):
            cols = row.find_all("td")
            if cols:
                raw_name = cols[0].get_text(strip=True)
                if raw_name:
                    base = suffix_pattern.sub('', raw_name).strip()
                    clean_name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', base)
                    courses.add(clean_name)

        print(f"\n🎯 Original logic found {len(courses)} courses")
        if courses:
            print("📝 Sample courses:")
            for course in sorted(list(courses))[:5]:
                print(f"   - {course}")

    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    debug_scraping()
