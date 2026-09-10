#!/usr/bin/env python3
import sys
import json
import subprocess

sys.path.insert(0, '/Users/antonschwarz/Desktop/Test/backend')

from excel_builder import build_excel

# Load options_meta
with open('/Users/antonschwarz/Desktop/Test/backend/options_meta.json') as f:
    options_meta = json.load(f)

# Test data with 475
vehicle_data = {
    "base_vehicle": {
        "code": "66GR",
        "text": "Basic Vehicle X5",
        "price": 0.0
    },
    "exterior_color": {
        "code": "475",
        "text": "Black Sapphire Metallic",
        "price": 0.0
    },
    "interior_color": None,
    "interior_trim": None,
    "security_package": None,
    "standard": [],
    "optional": [],
    "security": [],
    "total_price": 0.0
}

print("=" * 60)
print("TEST: Building Excel with 475 (should include image)")
print("=" * 60)

result = build_excel(vehicle_data)
print(f"\n✓ Excel created: {result}")

# Check if image is in the Excel
print("\nChecking for images in Excel...")
result = subprocess.run(
    ['unzip', '-l', result],
    capture_output=True,
    text=True
)

if 'media' in result.stdout or 'image' in result.stdout:
    print("✓ Image found in Excel!")
    print(result.stdout)
else:
    print("✗ No image found in Excel")
    print(result.stdout)
