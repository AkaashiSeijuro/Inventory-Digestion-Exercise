import csv
import io
import json
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime

# Constants for input/output locations and API endpoint
ENTRY_HTML_URL = "https://bitbucket.org/cityhive/jobs/raw/master/integration-eng/integration-entryfile.html"
LOCAL_SOURCE_FILE = "downloaded_inventory.csv"
OUTPUT_FILE = "inventory_output.csv"
API_BASE_URL = "http://localhost:3000"


# Fetching HTML/text content from URL
def fetch_text(url):
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


# Fetching raw bytes (used for CSV download)
def fetch_bytes(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


# Saving downloaded CSV locally for reference/debugging
def save_bytes(content, file_path):
    with open(file_path, "wb") as f:
        f.write(content)


# Helper to extract values between HTML markers
def extract_between(text, start_marker, end_marker):
    start = text.find(start_marker)
    if start == -1:
        return ""
    start += len(start_marker)

    end = text.find(end_marker, start)
    if end == -1:
        return ""

    return text[start:end].strip()


# Parsing HTML entry file to extract S3 bucket info
def parse_entry_html(html):

    # Extracting bucket name
    bucket = extract_between(html, '<div id="bucket-value">', '</div>')

    # Extracting region using regex
    region_match = re.search(
        r'id="region-value"[^>]*data-region="([^"]+)"',
        html
    )
    region = region_match.group(1) if region_match else ""

    # Building object path from spans
    object_block = extract_between(html, '<div id="object-value">', '</div>')
    path_parts = re.findall(r'<span class="path">([^<]+)</span>', object_block)
    object_path = "/".join(part.strip() for part in path_parts if part.strip())

    # Validating parsing success
    if not bucket or not region or not object_path:
        raise ValueError("Failed parsing HTML")

    return bucket, region, object_path


# Constructing S3 download URL
def build_s3_url(bucket, region, object_path):
    return f"https://{bucket}.s3.{region}.amazonaws.com/{object_path}"


# Cleaning values (remove NULL and whitespace)
def clean_value(value):
    value = (value or "").strip()
    if value.upper() == "NULL":
        return ""
    return value


# Ensuring duplicate headers become unique
def make_unique_headers(headers):
    counts = {}
    unique = []

    for h in headers:
        h = h.strip()
        if h not in counts:
            counts[h] = 1
            unique.append(h)
        else:
            counts[h] += 1
            unique.append(f"{h}_{counts[h]}")

    return unique


# Parse pipe-delimited CSV into dictionaries
def parse_inventory_csv(content_bytes):

    # Removing BOM and read CSV
    text = content_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text), delimiter="|")
    rows = list(reader)

    raw_headers = rows[0]

    # Fixing duplicate column names
    headers = make_unique_headers(raw_headers)

    data_rows = rows[1:]

    # Removing separator row if present
    if data_rows and data_rows[0][0] == "-------":
        data_rows = data_rows[1:]

    # Converting rows to dictionaries
    dict_rows = []
    for values in data_rows:
        row_dict = {}
        for i, header in enumerate(headers):
            row_dict[header] = values[i] if i < len(values) else ""
        dict_rows.append(row_dict)

    return headers, dict_rows


# Safe float conversion
def to_float(value, default=0.0):
    value = clean_value(value)
    try:
        return float(value)
    except Exception:
        return default


# Safe integer conversion
def to_int(value, default=0):
    value = clean_value(value)
    try:
        return int(float(value))
    except Exception:
        return default


# Validating UPC (must be numeric and >5 digits)
def valid_upc(value):
    value = clean_value(value)
    return value.isdigit() and len(value) > 5


# Checking if item sold in 2020 (supports multiple date formats)
def sold_in_2020(value):

    value = clean_value(value)

    if not value:
        return False

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S"
    ]

    # Trying structured parsing first
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).year == 2020
        except Exception:
            pass

    # Fallback string check
    return "2020" in value


# Selecting first valid price from possible columns
def pick_price(row):

    candidates = [
        row.get("Price", ""),
        row.get("Retail_Price", ""),
        row.get("WebPrice", ""),
        row.get("Price_2", ""),
        row.get("Price_3", ""),
    ]

    for candidate in candidates:
        val = to_float(candidate, default=0.0)

        # Using first valid price
        if val > 0:
            return val

    return 0.0


# Main transformation logic
def transform_rows(rows):

    # Counting duplicate SKUs
    item_counts = Counter(clean_value(row.get("ItemNum")) for row in rows)
    duplicates = {item for item, count in item_counts.items() if item and count > 1}

    output = []

    for row in rows:

        # Keeping only items sold in 2020
        last_sold = clean_value(row.get("Last_Sold"))
        if not sold_in_2020(last_sold):
            continue

        item_num = clean_value(row.get("ItemNum"))
        item_name = clean_value(row.get("ItemName"))
        item_extra = clean_value(row.get("ItemName_Extra"))

        cost = to_float(row.get("Cost"))
        price = pick_price(row)

        # Skiping if no valid price
        if price <= 0:
            continue

        quantity = to_int(row.get("In_Stock"))
        department = clean_value(row.get("Dept_ID"))
        vendor = clean_value(row.get("Vendor_Number"))

        # Choosing best description
        description = clean_value(row.get("Description"))
        if not description:
            description = clean_value(row.get("Description_2"))

        upc = clean_value(row.get("AltSKU"))
        row_id = clean_value(row.get("RowID"))

        # Combining name fields
        name = f"{item_name} {item_extra}".strip()

        # Calculating margin
        margin = 0.0
        if cost > 0:
            margin = (price - cost) / cost

        # Applying pricing rules
        if margin > 0.30:
            final_price = round(price * 1.07, 2)
        else:
            final_price = round(price * 1.09, 2)

        # Handling UPC vs internal ID rule
        if valid_upc(upc):
            internal_id = ""
        else:
            upc = ""
            internal_id = f"biz_id_{row_id}"

        # Storing extra attributes as JSON
        properties = json.dumps({
            "department": department,
            "vendor": vendor,
            "description": description
        })

        # Assigning tags
        tags = []

        if item_num in duplicates:
            tags.append("duplicate_sku")

        if margin > 0.30:
            tags.append("high_margin")
        elif margin < 0.30:
            tags.append("low_margin")

        # Final transformed record
        output.append({
            "item_num": item_num,
            "name": name,
            "department": department,
            "upc": upc,
            "internal_id": internal_id,
            "price": final_price,
            "cost": round(cost, 2),
            "quantity": quantity,
            "properties": properties,
            "tags": ",".join(tags)
        })

    return output


# Writing transformed data to CSV
def write_output_csv(rows, output_file=OUTPUT_FILE):

    fieldnames = [
        "item_num",
        "name",
        "department",
        "upc",
        "internal_id",
        "price",
        "cost",
        "quantity",
        "properties",
        "tags"
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)


# Full pipeline implementation for download, parse, to transform
def load_and_transform(save_local_copy=True):

    html = fetch_text(ENTRY_HTML_URL)

    bucket, region, object_path = parse_entry_html(html)

    s3_url = build_s3_url(bucket, region, object_path)

    print("Bucket:", bucket)
    print("Region:", region)
    print("Object Path:", object_path)
    print("S3 URL:", s3_url)

    csv_bytes = fetch_bytes(s3_url)

    # Saving raw CSV if desired
    if save_local_copy:
        save_bytes(csv_bytes, LOCAL_SOURCE_FILE)

    headers, rows = parse_inventory_csv(csv_bytes)

    print("Parsed rows:", len(rows))

    transformed = transform_rows(rows)

    print("Transformed rows:", len(transformed))

    return transformed


# Generating CSV output file
def generate_csv():

    transformed = load_and_transform(save_local_copy=True)

    write_output_csv(transformed)

    print(f"CSV generated: {OUTPUT_FILE}")


# Uploading transformed data to API
def upload():

    transformed = load_and_transform(save_local_copy=True)

    payload = json.dumps(transformed).encode("utf-8")

    req = urllib.request.Request(
        f"{API_BASE_URL}/inventory_uploads.json",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            print("Upload success")
            print(response.read().decode("utf-8"))

    except Exception as e:
        print("Upload failed")
        print(e)


# Listing uploaded batches from API
def list_uploads():

    req = urllib.request.Request(
        f"{API_BASE_URL}/inventory_uploads.json",
        method="GET"
    )

    try:
        with urllib.request.urlopen(req) as response:
            print("Upload batches:")
            print(response.read().decode("utf-8"))

    except Exception as e:
        print("Request failed")
        print(e)


# CLI entry point
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python integration-exercise.py generate_csv")
        print("  python integration-exercise.py upload")
        print("  python integration-exercise.py list_uploads")

    elif sys.argv[1] == "generate_csv":
        generate_csv()

    elif sys.argv[1] == "upload":
        upload()

    elif sys.argv[1] == "list_uploads":
        list_uploads()

    else:
        print("Unknown command")
