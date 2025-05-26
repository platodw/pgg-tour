import requests
from bs4 import BeautifulSoup
import json
import re

# Function to insert spaces between lowercase-uppercase transitions
def add_spaces(name):
    return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)

# URL to scrape
url = "https://pakmanstudios.com/gspro-course-list/"

# Add headers to avoid being blocked
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

courses = set()

# Regex pattern to remove common suffixes like _Pakman, _GSX, etc.
suffix_pattern = re.compile(r'_[A-Z]{2,10}$')

# Find all rows in the course list table
for row in soup.select("table tbody tr"):
    cols = row.find_all("td")
    if cols:
        raw_name = cols[0].get_text(strip=True)
        if raw_name:
            base = suffix_pattern.sub('', raw_name).strip()
            clean_name = add_spaces(base)
            courses.add(clean_name)

# Save to static/course_list.json
sorted_courses = sorted(courses)

print(f"📊 About to save {len(sorted_courses)} courses")
print(f"📝 Sample courses: {sorted_courses[:3] if sorted_courses else 'None'}")

try:
    with open("static/course_list.json", "w") as f:
        json.dump(sorted_courses, f, indent=2)
    print("✅ File write completed")

    # Verify the file was written
    with open("static/course_list.json", "r") as f:
        verification = json.load(f)
    print(f"🔍 Verification: File contains {len(verification)} courses")

except Exception as e:
    print(f"❌ Error writing file: {e}")

print(f"✅ Scraped and formatted {len(sorted_courses)} course names.")