"""
Auto-generated Playwright Test Script
Generated from: RBPLCD-8002
Title: View teststep details and navigate accordions
Generated: 2025-11-24 14:37:04
"""

import pytest
from playwright.sync_api import Page, expect


def test_rbplcd_8002(page: Page):
    """
    Test: View teststep details and navigate accordions
    Module: Teststep
    """

    # Step 0: Login
    print("Step 0: Login")
    page.goto("http://fe0vm03313.de.bosch.com/rbplcd_t/client/login")
    page.wait_for_load_state('networkidle')

    # Enter credentials
    page.fill('input[type="text"]', "mechanic")
    page.fill('input[type="password"]', "avalon")

    # Click login button
    page.click("[data-loginBtn='loginBtn']")
    page.wait_for_load_state('networkidle')

    print("[OK] Login successful")

    # Step 2: Click Runs link in sidebar to navigate to Teststep module
    # Selector discovered by: Agent L1 (confidence: 0.86)
    print("Step 2: Click Runs link in sidebar to navigate to Teststep module")

    # Wait for element to be available
    page.wait_for_selector("[data-test='sidebar-nav-item-nav_item_teststeps']", timeout=10000)

    # Click action
    page.click("[data-test='sidebar-nav-item-nav_item_teststeps']")
    page.wait_for_load_state('networkidle')
    print("[OK] Clicked element")

    # Step 3: Click on table row for Teststep named default_Measurement01
    # Selector discovered by: Agent L1 (confidence: 0.77)
    print("Step 3: Click on table row for Teststep named default_Measurement01")

    # Wait for element to be available
    page.wait_for_selector("[data-attribute='default_Measurement01']", timeout=10000)

    # Click action
    page.click("[data-attribute='default_Measurement01']")
    page.wait_for_load_state('networkidle')
    print("[OK] Clicked element")

    # Step 4: Click to expand Details accordion section
    # Selector discovered by: Agent L1 (confidence: 0.77)
    print("Step 4: Click to expand Details accordion section")

    # Wait for element to be available
    page.wait_for_selector("[data-detailspanel='detailsPanel']", timeout=10000)

    # Click action
    page.click("[data-detailspanel='detailsPanel']")
    page.wait_for_load_state('networkidle')
    print("[OK] Clicked element")

    # Step 5: Click to expand Parts accordion section
    # Selector discovered by: Agent L1 (confidence: 0.78)
    print("Step 5: Click to expand Parts accordion section")

    # Wait for element to be available
    page.wait_for_selector("[data-parttypepanel='partTypePanel']", timeout=10000)

    # Click action
    page.click("[data-parttypepanel='partTypePanel']")
    page.wait_for_load_state('networkidle')
    print("[OK] Clicked element")

    # Step 6: Click to expand Equipments accordion section
    # Selector discovered by: Agent L1 (confidence: 0.77)
    print("Step 6: Click to expand Equipments accordion section")

    # Wait for element to be available
    page.wait_for_selector("[data-expensionpanelheader='aeName.TestEquipment.names']", timeout=10000)

    # Click action
    page.click("[data-expensionpanelheader='aeName.TestEquipment.names']")
    page.wait_for_load_state('networkidle')
    print("[OK] Clicked element")

    # Step 7: Click to expand Sequences accordion section
    # Selector discovered by: Agent L1 (confidence: 0.79)
    print("Step 7: Click to expand Sequences accordion section")

    # Wait for element to be available
    page.wait_for_selector("[data-expensionpanelheader='aeName.TestSequence.names']", timeout=10000)

    # Click action
    page.click("[data-expensionpanelheader='aeName.TestSequence.names']")
    page.wait_for_load_state('networkidle')
    print("[OK] Clicked element")

    print("[OK] Test completed successfully")


if __name__ == "__main__":
    """Run test with pytest and generate HTML report"""
    from datetime import datetime
    from pathlib import Path

    # Create Reports folder if it doesn't exist
    reports_folder = Path("Reports")
    reports_folder.mkdir(parents=True, exist_ok=True)

    # Generate report filename with NEW timestamp (at execution time)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ticket_id = "RBPLCD-8002"
    report_path = reports_folder / f"{ticket_id}_{timestamp}_report.html"

    # Run with HTML report
    pytest.main([__file__, "-v", "-s", f"--html={report_path}", "--self-contained-html"])
    print(f"\n[OK] HTML Report: {report_path}")
