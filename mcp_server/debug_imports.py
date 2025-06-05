#!/usr/bin/env python3
"""Debug imports for cloud server."""

print("Testing FastAPI imports...")

try:
    import fastapi
    print(f"✓ fastapi version: {fastapi.__version__}")
except ImportError as e:
    print(f"✗ fastapi import failed: {e}")

try:
    from fastapi import FastAPI
    print("✓ FastAPI class imported")
except ImportError as e:
    print(f"✗ FastAPI class import failed: {e}")

try:
    import uvicorn
    print(f"✓ uvicorn version: {uvicorn.__version__}")
except ImportError as e:
    print(f"✗ uvicorn import failed: {e}")

try:
    from fastapi.middleware.cors import CORSMiddleware
    print("✓ CORSMiddleware imported")
except ImportError as e:
    print(f"✗ CORSMiddleware import failed: {e}")

try:
    from fastapi.security import HTTPBearer
    print("✓ HTTPBearer imported")
except ImportError as e:
    print(f"✗ HTTPBearer import failed: {e}")

print("\nTesting all imports together...")
try:
    from fastapi import FastAPI, Request, HTTPException, Depends
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer
    import uvicorn
    print("✅ All FastAPI imports successful!")
except ImportError as e:
    print(f"✗ Combined import failed: {e}")
    import traceback
    traceback.print_exc()