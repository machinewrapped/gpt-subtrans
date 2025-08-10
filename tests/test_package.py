#!/usr/bin/env python3
"""
Test script to verify gpt-subtrans package installation and basic functionality.
"""

import sys
import tempfile
import os


def test_core_imports():
    """Test that core modules can be imported."""
    try:
        from PySubtitle.Options import Options
        from PySubtitle.SubtitleFile import SubtitleFile
        from PySubtitle.SubtitleProject import SubtitleProject
        from PySubtitle.TranslationProvider import TranslationProvider
        from PySubtitle import version
        print("✓ Core imports successful")
        print(f"✓ Version: {version.__version__}")
        return True
    except ImportError as e:
        print(f"✗ Core import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without requiring API keys."""
    try:
        from PySubtitle.Options import Options
        from PySubtitle.SubtitleFile import SubtitleFile
        
        # Test Options creation
        options = Options()
        options.options['target_language'] = "Spanish"
        assert options.target_language == "Spanish"
        print("✓ Options creation and configuration works")
        
        # Test SRT file loading
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,000
How are you?
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
            f.write(srt_content)
            temp_path = f.name
        
        try:
            subtitle_file = SubtitleFile(temp_path)
            print("✓ Subtitle file loading works")
        finally:
            os.unlink(temp_path)
            
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


def test_providers():
    """Test provider detection."""
    try:
        from PySubtitle.TranslationProvider import TranslationProvider
        providers = TranslationProvider.get_providers()
        print(f"✓ Found {len(providers)} available providers: {list(providers.keys())}")
        return True
    except Exception as e:
        print(f"✗ Provider test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing gpt-subtrans package installation...")
    print()
    
    tests = [
        ("Core Imports", test_core_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Provider Detection", test_providers),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"Running {name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The package is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the installation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())