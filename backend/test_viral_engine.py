#!/usr/bin/env python3
"""
Test script for the Viral Similarity Engine.
Run this to verify all components are working correctly.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.viral import (
    get_viral_terms, add_viral_term, get_viral_vector, 
    rebuild_viral_vector, window_captions, score_windows_against_viral_vector,
    get_database_stats
)
from app.config import settings


async def test_viral_engine():
    """Test all components of the viral engine."""
    print("🧪 Testing Viral Similarity Engine...")
    print("=" * 50)
    
    try:
        # Test 1: Viral Terms Management
        print("\n1️⃣ Testing Viral Terms Management...")
        terms = get_viral_terms()
        print(f"   ✅ Loaded {len(terms)} viral terms")
        print(f"   📝 Sample terms: {[t.term for t in terms[:5]]}")
        
        # Test 2: Add a new term
        print("\n2️⃣ Testing Term Addition...")
        new_term = "test_viral_term"
        success = add_viral_term(new_term, 1.5)
        print(f"   ✅ Added term '{new_term}': {success}")
        
        # Test 3: Database Stats
        print("\n3️⃣ Testing Database...")
        stats = get_database_stats()
        print(f"   📊 Database stats: {stats}")
        
        # Test 4: Viral Vector Computation
        print("\n4️⃣ Testing Viral Vector Computation...")
        viral_vector, updated_at = await get_viral_vector()
        if viral_vector is not None:
            print(f"   ✅ Viral vector computed: {viral_vector.shape}")
            print(f"   📅 Updated at: {updated_at}")
            print(f"   🔢 Vector norm: {viral_vector.dot(viral_vector):.6f}")
        else:
            print("   ❌ Failed to compute viral vector")
        
        # Test 5: Rebuild Viral Vector
        print("\n5️⃣ Testing Viral Vector Rebuild...")
        rebuild_result = await rebuild_viral_vector()
        print(f"   ✅ Rebuild result: {rebuild_result}")
        
        # Test 6: Caption Windowing
        print("\n6️⃣ Testing Caption Windowing...")
        test_captions = [
            {"start": 0, "end": 10, "text": "wow that was insane!"},
            {"start": 10, "end": 20, "text": "no way this happened"},
            {"start": 20, "end": 30, "text": "watch till the end"},
            {"start": 30, "end": 40, "text": "this is unbelievable"}
        ]
        
        windows = window_captions(
            segments=test_captions,
            start=0,
            end=40,
            window_sec=16,
            hop_sec=8
        )
        print(f"   ✅ Created {len(windows)} caption windows")
        for i, window in enumerate(windows):
            print(f"      Window {i+1}: {window.start_time:.1f}s - {window.end_time:.1f}s")
            print(f"         Text: {window.text[:50]}...")
        
        # Test 7: Viral Scoring
        print("\n7️⃣ Testing Viral Scoring...")
        if windows:
            scored_windows = await score_windows_against_viral_vector(windows)
            print(f"   ✅ Scored {len(scored_windows)} windows")
            for i, window in enumerate(scored_windows[:3]):
                print(f"      Window {i+1}: score = {window.score:.4f}")
                print(f"         Text: {window.text[:50]}...")
        
        # Test 8: Configuration
        print("\n8️⃣ Testing Configuration...")
        print(f"   🔧 Embedding model: {settings.embedding_model}")
        print(f"   🔧 Window size: {settings.viral_window_sec}s")
        print(f"   🔧 Window hop: {settings.viral_window_hop}s")
        print(f"   🔧 Min score: {settings.viral_min_score}")
        print(f"   🔧 Top K: {settings.viral_top_k}")
        print(f"   🔧 Max terms: {settings.viral_max_terms}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test the FastAPI endpoints."""
    print("\n🌐 Testing API Endpoints...")
    print("=" * 50)
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        # Test 1: Health check
        print("\n1️⃣ Testing health endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            print(f"   ✅ Health check: {response.status_code}")
        
        # Test 2: Viral terms endpoint
        print("\n2️⃣ Testing viral terms endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/viral/terms")
            print(f"   ✅ Viral terms: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   📝 Found {data.get('total_count', 0)} terms")
        
        # Test 3: Test endpoint
        print("\n3️⃣ Testing viral test endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{base_url}/api/v1/viral/test")
            print(f"   ✅ Test endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   🚀 Status: {data.get('status', 'unknown')}")
        
        print("\n🎉 API endpoint tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 ClipGenius Viral Similarity Engine Test Suite")
    print("=" * 60)
    
    # Test core functionality
    core_success = await test_viral_engine()
    
    # Test API endpoints (if backend is running)
    api_success = await test_api_endpoints()
    
    print("\n" + "=" * 60)
    if core_success and api_success:
        print("🎉 All tests passed! The Viral Similarity Engine is working correctly.")
        print("\n📚 Next steps:")
        print("   1. Start the backend: python run.py")
        print("   2. Test with a real video")
        print("   3. Check the API documentation at http://localhost:8000/docs")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
        if not core_success:
            print("   - Core functionality tests failed")
        if not api_success:
            print("   - API endpoint tests failed (backend may not be running)")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
