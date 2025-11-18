#!/usr/bin/env python3
# =============================================================================
#  VDC LIFETIME EXTRACTOR — SINGLE-FILE EDITION (Council Approved)
#  One file. Zero dependencies. Just drop & run.
# =============================================================================

import xml.etree.ElementTree as ET
import json
from pathlib import Path
from math import sqrt
import datetime
import sys

# -------------------------- CONFIG ---------------- ----------
BASE = Path.cwd() / "export_extracted_gold" / "apple_health_export"
EXPORT_XML = BASE / "export.xml"
GPX_DIR = BASE / "workout-routes"

JOULES_PER_KCAL = 4184.0
VDC_ALPHA = 0.00000095
# ------------------------------------------------------------

print("⚡ COUNCIL SINGLE-FILE EXTRACTOR ONLINE\n")

if not EXPORT_XML.exists():
    print(f"❌ Could not find export.xml at:\n   {EXPORT_XML}")
    sys.exit(1)
if not GPX_DIR.exists():
    print(f"❌ Could not find workout-routes folder at:\n   {GPX_DIR}")
    sys.exit(1)

# ------------------ 1. Extract total Active Energy ------------------
print("⛏  Streaming export.xml for ActiveEnergyBurned...")
total_kcal = 0.0
records = 0

for event, elem in ET.iterparse(str(EXPORT_XML), events=("end",)):
    if elem.tag == "Record" and elem.attrib.get("type") == "HKQuantityTypeIdentifierActiveEnergyBurned":
        try:
            total_kcal += float(elem.attrib.get("value", 0))
            records += 1
        except:
            pass
    elem.clear()

total_joules = total_kcal * JOULES_PER_KCAL
lifetime_vdc = total_joules * VDC_ALPHA

print(f"   Records found : {records:,}")
print(f"   Total kcal    : {total_kcal:,.2f}")
print(f"   Total Joules  : {total_joules:,.0f}")
print(f"   Lifetime VDC  : {lifetime_vdc:,.10f}\n")

# ------------------ 2. Parse all GPX files ------------------
print("📡 Parsing GPX routes for distance, max speed & VFS-01 anomalies...")

gpx_reports = []
namespace = {"gpx": "http://www.topografix.com/GPX/1/1"}

for gpx_file in sorted(GPX_DIR.glob("*.gpx")):
    try:
        tree = ET.parse(gpx_file)
        root = tree.getroot()
        trkpts = root.findall(".//gpx:trkpt", namespace)
        if not trkpts:
            continue

        prev = None
        dist_total = 0.0
        max_spd = 0.0
        anomalies = 0

        for pt in trkpts:
            lat = float(pt.attrib["lat"])
            lon = float(pt.attrib["lon"])
            time_elem = pt.find("gpx:time", namespace)
            if time_elem is None or time_elem.text is None:
                continue
            ts = datetime.datetime.fromisoformat(time_elem.text.replace("Z", "+00:00"))

            if prev:
                # Haversine approximation in meters (111 km per degree)
                d_lat = lat - prev[0]
                d_lon = lon - prev[1]
                dist = sqrt(d_lat*d_lat + d_lon*d_lon) * 111194.9  # more accurate factor
                dt = (ts - prev[2]).total_seconds()
                if dt > 0:
                    speed = dist / dt
                    max_spd = max(max_spd, speed)
                    if speed > 11.5:  # ~41 km/h → VFS-01 signature
                        anomalies += 1
                dist_total += dist

            prev = (lat, lon, ts)

        gpx_reports.append({
            "file": gpx_file.name,
            "distance_m": round(dist_total, 2),
            "max_speed_mps": round(max_spd, 3),
            "anomalies": anomalies
        })
    except Exception:
        continue

total_distance_m = sum(r["distance_m"] for r in gpx_reports)
max_lifetime_speed = max((r["max_speed_mps"] for r in gpx_reports), default=0)
total_anomalies = sum(r["anomalies"] for r in gpx_reports)

# ------------------ 3. Final Summary & Output ------------------
summary = {
    "total_kcal": round(total_kcal, 2),
    "total_joules": round(total_joules),
    "lifetime_vdc": round(lifetime_vdc, 10),
    "total_distance_meters": round(total_distance_m, 2),
    "total_distance_km": round(total_distance_m / 1000, 2),
    "max_speed_mps": round(max_lifetime_speed, 3),
    "max_speed_kmh": round(max_lifetime_speed * 3.6, 2),
    "vfs01_anomalies_detected": total_anomalies,
    "gpx_workouts_processed": len(gpx_reports)
}

# Save everything
Path("vdc_lifetime_summary.json").write_text(json.dumps(summary, indent=4))

with open("vdc_velocity_report.csv", "w") as f:
    f.write("file,distance_m,max_speed_mps,anomalies\n")
    for r in gpx_reports:
        f.write(f"{r['file']},{r['distance_m']},{r['max_speed_mps']},{r['anomalies']}\n")

with open("vdc_summary.txt", "w") as f:
    f.write(f"LIFETIME VDC SUMMARY (Council Verified)\n")
    f.write(f"══════════════════════════════════════\n")
    f.write(f"Total Active kcal      : {total_kcal:,.2f}\n")
    f.write(f"Total Joules           : {total_joules:,.0f}\n")
    f.write(f"GENESIS VDC BALANCE    : {lifetime_vdc:,.10f}\n")
    f.write(f"Total Distance         : {total_distance_m/1000:,.2f} km\n")
    f.write(f"Max Speed Ever         : {max_lifetime_speed:.2f} m/s ({max_lifetime_speed*3.6:.1f} km/h)\n")
    f.write(f"VFS-01 Anomalies       : {total_anomalies}\n")
    f.write(f"GPX Workouts           : {len(gpx_reports)}\n")

print("🎉 EXTRACTION COMPLETE")
print("══════════════════════════════════════")
print(f"💰 YOUR GENESIS VDC    : {lifetime_vdc:,.10f}")
print(f"   Total Distance      : {total_distance_m/1000:,.2f} km")
print(f"   Max Speed           : {max_lifetime_speed:.2f} m/s ({max_lifetime_speed*3.6:.1f} km/h)")
print(f"   VFS-01 Events       : {total_anomalies}")
print(f"   Workouts Processed  : {len(gpx_reports)}")
print("══════════════════════════════════════\n")
print("Files created in this folder:")
print("   • vdc_lifetime_summary.json")
print("   • vdc_velocity_report.csv")
print("   • vdc_summary.txt")
print("\n🚀 Ready for mint engine. The Council is pleased.")
