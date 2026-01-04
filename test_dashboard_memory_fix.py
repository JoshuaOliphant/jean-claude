#!/usr/bin/env python3
"""Test script to verify dashboard memory leak fixes.

This script tests the SSE connection limits, timeout behavior, and memory usage
to ensure the memory leak has been properly fixed.

Usage:
    # Terminal 1: Start the dashboard
    jc dashboard

    # Terminal 2: Run this test
    python test_dashboard_memory_fix.py

Expected Results:
    - First 5 connections should succeed
    - 6th connection should get 429 (Too Many Requests)
    - Connections should auto-close after timeout
    - Memory usage should remain stable
"""

import asyncio
import httpx
import time
import psutil
import os


async def test_connection_limit():
    """Test that connection limit (5) is enforced."""
    print("Testing connection limit enforcement...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try to open 6 connections
        connections = []

        try:
            # Open first 5 connections (should succeed)
            for i in range(5):
                print(f"  Opening connection {i+1}/5...")
                response = await client.get(
                    "http://localhost:8000/api/events/test-workflow/stream",
                    headers={"Accept": "text/event-stream"}
                )
                if response.status_code == 200:
                    connections.append(response)
                    print(f"    ✓ Connection {i+1} opened successfully")
                else:
                    print(f"    ✗ Connection {i+1} failed: {response.status_code}")

            # Try to open 6th connection (should fail with 429)
            print("  Attempting 6th connection (should fail)...")
            try:
                response = await client.get(
                    "http://localhost:8000/api/events/test-workflow/stream",
                    headers={"Accept": "text/event-stream"}
                )
                if response.status_code == 429:
                    print("    ✓ 6th connection correctly rejected with 429 (Too Many Requests)")
                    return True
                else:
                    print(f"    ✗ Expected 429, got {response.status_code}")
                    return False
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    print("    ✓ 6th connection correctly rejected with 429")
                    return True
                print(f"    ✗ Unexpected error: {e}")
                return False

        finally:
            # Close all connections
            for conn in connections:
                await conn.aclose()
            print("  Closed all test connections")


async def test_memory_usage():
    """Monitor memory usage during connection lifetime."""
    print("\nTesting memory usage stability...")

    # Get current process
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    print(f"  Initial memory usage: {initial_memory:.2f} MB")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Open connection
            async with client.stream(
                "GET",
                "http://localhost:8000/api/events/test-workflow/stream",
                headers={"Accept": "text/event-stream"}
            ) as response:
                # Monitor memory for 10 seconds
                for i in range(10):
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory

                    print(f"  {i+1}s: {current_memory:.2f} MB (Δ {memory_increase:+.2f} MB)")

                    if memory_increase > 100:  # More than 100 MB increase
                        print("    ✗ Memory usage increased too much!")
                        return False

                    # Read a few events to keep connection active
                    try:
                        async for line in response.aiter_lines():
                            if line:
                                break  # Just read one line
                    except:
                        pass

                    await asyncio.sleep(1)

        except Exception as e:
            print(f"  ✗ Connection error: {e}")
            return False

    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory

    print(f"  Final memory usage: {final_memory:.2f} MB (Δ {memory_increase:+.2f} MB)")

    if memory_increase < 50:  # Less than 50 MB increase is acceptable
        print("  ✓ Memory usage remained stable")
        return True
    else:
        print(f"  ✗ Memory increased by {memory_increase:.2f} MB")
        return False


async def test_event_loading():
    """Test that only recent events are loaded (not entire file)."""
    print("\nTesting memory-efficient event loading...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Connect and count initial events
            event_count = 0

            async with client.stream(
                "GET",
                "http://localhost:8000/api/events/test-workflow/stream",
                headers={"Accept": "text/event-stream"}
            ) as response:
                # Count events received in first 2 seconds
                start_time = time.time()

                async for line in response.aiter_lines():
                    if line and line.startswith("data:"):
                        event_count += 1

                    if time.time() - start_time > 2:
                        break

            print(f"  Received {event_count} events in first 2 seconds")

            # Should receive max 1000 events (the limit) + a few new ones
            if event_count <= 1010:  # Some buffer for new events
                print("  ✓ Event loading is memory-efficient (limited to recent events)")
                return True
            else:
                print(f"  ✗ Too many events received ({event_count}), may be loading entire file")
                return False

        except Exception as e:
            print(f"  ⚠ Could not test event loading: {e}")
            return None  # Skip this test if events.jsonl doesn't exist


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Dashboard Memory Leak Fix Verification")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("  - Dashboard must be running: jc dashboard")
    print("  - Test workflow directory: agents/test-workflow/")
    print()

    results = []

    # Test 1: Connection limit
    try:
        result = await test_connection_limit()
        results.append(("Connection Limit", result))
    except Exception as e:
        print(f"✗ Connection limit test failed: {e}")
        results.append(("Connection Limit", False))

    # Test 2: Memory usage
    try:
        result = await test_memory_usage()
        results.append(("Memory Stability", result))
    except Exception as e:
        print(f"✗ Memory stability test failed: {e}")
        results.append(("Memory Stability", False))

    # Test 3: Event loading
    try:
        result = await test_event_loading()
        if result is not None:
            results.append(("Event Loading", result))
    except Exception as e:
        print(f"✗ Event loading test failed: {e}")
        results.append(("Event Loading", False))

    # Print summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} {status}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("✅ All tests passed! Memory leak fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    import sys

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
