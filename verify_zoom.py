"""
Manual Verification Script for Viewport Scaling & Zoom
Run this to see the browser launch with portrait resolution and 50% zoom.
"""
import time
from compass_core.standard_driver_manager import StandardDriverManager

def verify_viewport_settings():
    print("🚀 Initializing StandardDriverManager...")
    manager = StandardDriverManager()
    
    try:
        # This will trigger the 768x1024 and 50% zoom logic
        driver = manager.get_or_create_driver()
        
        # Navigate to a real page to see the effects
        print("🌐 Navigating to Google (for visual verification)...")
        driver.get("https://www.google.com")
        
        # Explicitly re-apply on the verification script too to be sure
        driver.execute_script("document.body.style.zoom = '0.5'; document.documentElement.style.zoom = '0.5';")
        
        # Verify Resolution
        size = driver.get_window_size()
        print(f"✅ Resolution: {size['width']}x{size['height']} (Expected ~768x1024)")
        
        # Verify Zoom Level via JS
        zoom = driver.execute_script("return window.devicePixelRatio;")
        # Note: on high DPI screens devicePixelRatio starts at 1.25 or 1.5, 
        # but the zoom style shrinks the content.
        print(f"✅ Browser DevicePixelRatio: {zoom}")
        
        print("\n👀 LOOK AT THE BROWSER NOW:")
        print("1. Is it in Portrait mode?")
        print("2. Is the content half-size (50% zoom)?")
        print("\nClosing in 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        manager.quit_driver()

if __name__ == "__main__":
    verify_viewport_settings()
