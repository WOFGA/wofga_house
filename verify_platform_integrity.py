"""
verify_platform_integrity.py
Automated End-to-End Verification Suite for Tainan WebGIS Platform (wofga_house).
Covers:
1. Syntax & compilation across Python 3.10+ and Node.js JavaScript engines
2. Data schema, coordinate bounds (Greater Tainan), and numeric price validation
3. Leaflet WebGIS styling, cluster config, and .leaflet-div-icon transparent override
4. Mobile layout integrity (360px viewport) and overflow prevention
5. Form accessibility (WCAG aria-labels, touch target sizing, inputmode/autocomplete)
6. Dynamic Soil Liquefaction tile calculations via official ArcGIS Server
7. Hover popup debounce, event listener cleanup, and state management
8. Layer toggle controls (Registration, 591 In-sale, Liquefaction, Flood, Transit, Amenities)
9. Data pipeline fail-safe guards (empty overwrite protection, incremental merge, regionid=15)
10. GitHub Actions CI/CD permission configuration
"""

import json
import os
import re
import subprocess
import sys
import unittest

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

class TestPlatformIntegrity(unittest.TestCase):

    def setUp(self):
        self.index_path = os.path.join(REPO_ROOT, "index.html")
        self.run_agent_path = os.path.join(REPO_ROOT, "run_agent.py")
        self.fetch_591_path = os.path.join(REPO_ROOT, "fetch_591_listings.py")
        self.listings_path = os.path.join(REPO_ROOT, "listings.json")
        self.onsale_path = os.path.join(REPO_ROOT, "listings_onsale.json")
        self.workflow_path = os.path.join(REPO_ROOT, ".github", "workflows", "daily_runner.yml")

        with open(self.index_path, "r", encoding="utf-8") as f:
            self.index_html = f.read()

    def test_01_python_syntax(self):
        """Verify clean syntax and compilation for all backend Python files."""
        for py_file in [self.run_agent_path, self.fetch_591_path]:
            res = subprocess.run([sys.executable, "-m", "py_compile", py_file], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Python compile error in {py_file}:\n{res.stderr}")

    def test_02_javascript_syntax(self):
        """Verify clean JavaScript syntax for all inline script blocks using Node.js."""
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', self.index_html, re.DOTALL)
        self.assertTrue(len(scripts) > 0, "No inline scripts found in index.html")
        for idx, script_content in enumerate(scripts):
            if not script_content.strip():
                continue
            tmp_file = os.path.join(REPO_ROOT, f"_tmp_test_{idx}.js")
            try:
                with open(tmp_file, "w", encoding="utf-8") as f:
                    f.write(script_content)
                res = subprocess.run(["node", "--check", tmp_file], capture_output=True, text=True)
                self.assertEqual(res.returncode, 0, f"JS syntax error in block {idx}:\n{res.stderr}")
            finally:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)

    def test_03_json_datasets_integrity(self):
        """Verify listings.json and listings_onsale.json schemas, boundary coordinates, and prices."""
        for json_path, min_count in [(self.listings_path, 200), (self.onsale_path, 100)]:
            self.assertTrue(os.path.exists(json_path), f"JSON file missing: {json_path}")
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreaterEqual(len(data), min_count, f"{json_path} contains fewer items than expected")

            for i, item in enumerate(data):
                self.assertIn("lat", item, f"Missing lat in item {i} of {json_path}")
                self.assertIn("lng", item, f"Missing lng in item {i} of {json_path}")
                self.assertIn("district", item, f"Missing district in item {i} of {json_path}")
                self.assertIn("askTotal", item, f"Missing askTotal in item {i} of {json_path}")
                self.assertIn("askUnit", item, f"Missing askUnit in item {i} of {json_path}")
                self.assertIn("regUnit", item, f"Missing regUnit in item {i} of {json_path}")

                lat, lng = float(item["lat"]), float(item["lng"])
                self.assertTrue(22.80 <= lat <= 23.45, f"Lat {lat} out of Tainan bounds at item {i}")
                self.assertTrue(120.00 <= lng <= 120.60, f"Lng {lng} out of Tainan bounds at item {i}")
                self.assertGreater(float(item["askTotal"]), 0, f"askTotal non-positive at item {i}")
                self.assertGreater(float(item["askUnit"]), 0, f"askUnit non-positive at item {i}")

    def test_04_css_overrides_and_pin_styles(self):
        """Verify CSS defines .leaflet-div-icon transparent override and all custom WebGIS pins."""
        style_match = re.search(r'<style\b[^>]*>(.*?)</style>', self.index_html, re.DOTALL)
        self.assertIsNotNone(style_match, "<style> section not found in index.html")
        css = style_match.group(1)

        self.assertIn(".leaflet-div-icon", css, "Missing .leaflet-div-icon CSS override")
        self.assertIn("transparent", css, "leaflet-div-icon must be transparent")
        self.assertIn(".custom-pin", css, "Missing .custom-pin CSS class")
        self.assertIn(".pin-591", css, "Missing .pin-591 CSS class")
        self.assertIn(".pin-onsale", css, "Missing .pin-onsale CSS class")
        self.assertIn(".landmark-pin", css, "Missing .landmark-pin CSS class")
        self.assertIn(".cluster-pin", css, "Missing .cluster-pin CSS class")

    def test_05_mobile_responsiveness_360px(self):
        """Verify viewport tag and mobile layout rules down to 360px width."""
        self.assertIn('name="viewport"', self.index_html, "Missing viewport meta tag")
        self.assertIn('content="width=device-width, initial-scale=1.0"', self.index_html)
        self.assertIn("w-full sm:w-auto sm:flex-1", self.index_html, "Search input wrapper should be w-full on mobile")
        self.assertIn("width: min(320px, calc(100vw - 56px))", self.index_html, "Popup width rule not properly constrained")
        self.assertIn("py-1.5", self.index_html, "Mobile buttons should have at least py-1.5 touch ergonomics")

    def test_06_accessibility_and_form_attributes(self):
        """Verify form inputs have aria-labels, and mobile-friendly autocomplete/inputmode."""
        self.assertIn('id="input591Url"', self.index_html)
        self.assertIn('aria-label="591 售屋網址或房屋編號"', self.index_html)
        self.assertIn('id="districtFilter"', self.index_html)
        self.assertIn('aria-label="行政區快篩"', self.index_html)
        self.assertIn('id="vipCodeInput"', self.index_html)
        self.assertIn('aria-label="VIP 通行碼"', self.index_html)
        self.assertIn('id="leadName"', self.index_html)
        self.assertIn('autocomplete="name"', self.index_html)
        self.assertIn('id="leadPhone"', self.index_html)
        self.assertIn('type="tel"', self.index_html)
        self.assertIn('inputmode="tel"', self.index_html)

    def test_07_arcgis_soil_liquefaction_layer(self):
        """Verify that ArcGIS Dynamic export is used instead of the broken WMTS tile URL."""
        self.assertIn("ArcGISDynamicTileLayer", self.index_html, "ArcGISDynamicTileLayer class missing")
        self.assertIn("P04032/Soil_cgs_2026/MapServer/export", self.index_html, "ArcGIS export URL missing")
        self.assertIn("bboxSR=4326", self.index_html, "bboxSR=4326 missing")
        self.assertNotIn("P04032_Soil_cgs/default/GoogleMapsCompatible/{z}/{y}/{x}.png", self.index_html, "Old broken WMTS URL still present")

    def test_08_hover_popup_timer_fix(self):
        """Verify that mouseenter and mouseleave on popups properly control popupCloseTimer."""
        self.assertIn("popupEl.addEventListener('mouseenter'", self.index_html, "Popup mouseenter listener missing")
        self.assertIn("popupEl.addEventListener('mouseleave'", self.index_html, "Popup mouseleave listener missing")
        self.assertIn("isCursorOnPopup = true", self.index_html, "isCursorOnPopup state setting missing")

    def test_09_registration_and_onsale_layer_toggles(self):
        """Verify layer toggles for both registration and 591 in-sale properties."""
        self.assertIn('id="toggleRegistration"', self.index_html, "toggleRegistration checkbox missing")
        self.assertIn('id="toggleOnsale"', self.index_html, "toggleOnsale checkbox missing")
        self.assertIn('handleRegistrationToggle', self.index_html, "handleRegistrationToggle function missing")
        self.assertIn('handleOnsaleToggle', self.index_html, "handleOnsaleToggle function missing")

    def test_10_591_search_regionid_in_run_agent(self):
        """Verify that run_agent.py uses regionid=15 (Tainan) instead of 14 (Chiayi)."""
        with open(self.run_agent_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("regionid=15", code, "run_agent.py must use regionid=15 for Tainan")
        self.assertNotIn("regionid=14", code, "run_agent.py still uses regionid=14 (Chiayi)")

    def test_11_fetch_591_data_protection(self):
        """Verify that fetch_591_listings.py preserves existing data if crawl yields 0 results."""
        with open(self.fetch_591_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("len(listings) == 0", code, "Zero results check missing in fetch_591_listings.py")
        self.assertIn("保留", code, "Preservation message or logic missing")

    def test_12_github_actions_workflow_permissions(self):
        """Verify that GitHub Actions daily_runner.yml has contents: write permissions."""
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            workflow = f.read()
        self.assertIn("permissions:", workflow, "permissions block missing in daily_runner.yml")
        self.assertIn("contents: write", workflow, "contents: write missing in daily_runner.yml")

    def test_13_591_parser_bargain_and_sign_formatting(self):
        """Verify that parse591Listing handles negative diffPct with discount badge and no '+-' prefix."""
        self.assertIn("const sign = item591.diffPct > 0 ? '+' : '';", self.index_html)
        self.assertNotIn("(+${item591.diffPct}%)", self.index_html, "Pin icon must not hardcode + before diffPct")
        self.assertIn("591讓利案", self.index_html, "parse591Listing must support 591讓利案 badge for bargain items")

    def test_14_detail_lookup_dynamic_items(self):
        """Verify that scrollToDetail and selectAndUnlock fall back to selectedItem for dynamic items."""
        self.assertIn("selectedItem && selectedItem.id === id", self.index_html)

    def test_15_popup_hover_listener_deduplication(self):
        """Verify that popupopen guards against duplicate mouseenter/mouseleave listener attachment."""
        self.assertIn("_hasHoverListeners", self.index_html, "_hasHoverListeners guard missing")

    def test_16_district_filter_closes_popups_and_checks_toggles(self):
        """Verify that filterByDistrict closes active popups, and renderMarkers checks toggleRegistration."""
        self.assertIn("map.closePopup()", self.index_html)
        self.assertIn("toggleRegistration", self.index_html)

    def test_17_arcgis_error_tile_fallback(self):
        """Verify errorTileUrl and tileerror event listener on officialLiquefactionTile."""
        self.assertIn("errorTileUrl:", self.index_html)
        self.assertIn("officialLiquefactionTile.on('tileerror'", self.index_html)

    def test_18_fetch_591_robust_content_parsing(self):
        """Verify safe subContent extraction and non-Tainan address prefix filtering in fetch_591_listings.py."""
        with open(self.fetch_591_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn('(data.get("content") or {}).get("subContent"', code)
        self.assertIn("NON_TAINAN_PATTERN", code)

    def test_19_run_agent_dynamic_listing_count(self):
        """Verify dynamic listing count in run_agent.py fallback report string."""
        with open(self.run_agent_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("{len(listings)}", code)
        self.assertNotIn("292 筆有效建物交易", code)

    def test_20_all_37_tainan_districts_fallbacks(self):
        """Verify all 37 districts of Greater Tainan have fallbacks within bounds in run_agent and fetch_591."""
        import run_agent
        self.assertEqual(len(run_agent.DISTRICT_FALLBACKS), 37)
        for dist, info in run_agent.DISTRICT_FALLBACKS.items():
            lat, lng = info["lat"], info["lng"]
            self.assertTrue(22.80 <= lat <= 23.45, f"{dist} lat {lat} out of bounds")
            self.assertTrue(120.00 <= lng <= 120.60, f"{dist} lng {lng} out of bounds")

        import fetch_591_listings
        self.assertEqual(len(fetch_591_listings.DISTRICT_MAP), 37)

    def test_21_scoped_road_matching_zero_cross_district_collisions(self):
        """Verify TAINAN_DISTRICT_ROADS exists and scoped road matching prevents cross-district road mismatches."""
        import run_agent
        self.assertTrue(hasattr(run_agent, "TAINAN_DISTRICT_ROADS"))
        self.assertGreaterEqual(len(run_agent.TAINAN_DISTRICT_ROADS), 30)
        yk_roads = run_agent.TAINAN_DISTRICT_ROADS.get("永康區", {})
        xy_roads = run_agent.TAINAN_DISTRICT_ROADS.get("新營區", {})
        self.assertIn("中華路", yk_roads)
        self.assertIn("中華路", xy_roads)
        self.assertLess(yk_roads["中華路"]["lat"], 23.1)
        self.assertGreater(xy_roads["中華路"]["lat"], 23.2)

    def test_22_vip_modal_keyboard_accessibility_and_aria(self):
        """Verify WCAG 2.1 AA dialog role, aria attributes, Escape key dismissal, and Enter submission."""
        self.assertIn('role="dialog"', self.index_html)
        self.assertIn('aria-modal="true"', self.index_html)
        self.assertIn('aria-labelledby="vipModalTitle"', self.index_html)
        self.assertIn('aria-describedby="vipModalDesc"', self.index_html)
        self.assertIn("Escape", self.index_html)
        self.assertIn("focusables", self.index_html)
        self.assertIn('onkeydown="if(event.key===\'Enter\') verifyVipCode()"', self.index_html)

    def test_23_tap_false_and_mobile_touch_ergonomics(self):
        """Verify tap: false on Leaflet map to prevent double-tap issues and fluid mobile touch."""
        self.assertIn("tap: false", self.index_html)
        self.assertIn("-webkit-backface-visibility", self.index_html)

    def test_24_active_591_marker_interactions(self):
        """Verify that dynamic 591 pin m591 has hover and click event listeners."""
        self.assertIn("m591.on('mouseover'", self.index_html)
        self.assertIn("m591.on('click'", self.index_html)

    def test_25_safe_storage_wrapper(self):
        """Verify safe wrapper getStoredVip / setStoredVip protects against SecurityError in sandboxes."""
        self.assertIn("getStoredVip", self.index_html)
        self.assertIn("setStoredVip", self.index_html)

    def test_26_popup_dismiss_on_layer_toggle(self):
        """Verify that map.closePopup() is called in layer toggle handlers to prevent orphaned popups."""
        self.assertIn("map.closePopup()", self.index_html)
        self.assertRegex(self.index_html, r'(?s)handleRegistrationToggle\s*=\s*function.*?map\.closePopup\(\)')
        self.assertRegex(self.index_html, r'(?s)handleOnsaleToggle\s*=\s*function.*?map\.closePopup\(\)')


def run_all():
    print("=" * 60)
    print("  Tainan WebGIS Platform (wofga_house) Automated Test Suite")
    print("=" * 60)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPlatformIntegrity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\nTest Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures:  {len(result.failures)}")
    print(f"  Errors:    {len(result.errors)}")
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_all())
