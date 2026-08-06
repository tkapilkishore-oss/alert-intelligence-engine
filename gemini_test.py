# pyrefly: ignore [missing-import]
from dotenv import load_dotenv, find_dotenv
import os
import traceback
# pyrefly: ignore [missing-import]
import google.genai as genai
import importlib.metadata

print("=" * 80)
print("GEMINI SDK DIAGNOSTIC")
print("=" * 80)

# ------------------------------------------------------------------
# Load .env
# ------------------------------------------------------------------

dotenv_path = find_dotenv()

print(f".env found      : {dotenv_path}")

loaded = load_dotenv(dotenv_path, override=True)

print(f".env loaded     : {loaded}")

api_key = os.getenv("GEMINI_API_KEY")

print(f"Key exists      : {api_key is not None}")

if api_key:
    print(f"Key prefix      : {api_key[:5]}...")
    print(f"Key length      : {len(api_key)}")

print()

# ------------------------------------------------------------------
# SDK Version
# ------------------------------------------------------------------

try:
    version = importlib.metadata.version("google-genai")
    print(f"google-genai    : {version}")
except Exception:
    print("google-genai    : UNKNOWN")

print()

# ------------------------------------------------------------------
# Client Creation
# ------------------------------------------------------------------

print("=" * 80)
print("CLIENT CREATION")
print("=" * 80)

try:
    client = genai.Client(api_key=api_key)
    print("✅ Client created successfully")
except Exception as e:
    print("❌ Client creation failed")
    traceback.print_exc()
    raise SystemExit()

print()

# ------------------------------------------------------------------
# List Models
# ------------------------------------------------------------------

print("=" * 80)
print("AVAILABLE MODELS")
print("=" * 80)

try:
    models = list(client.models.list())

    print(f"Total Models: {len(models)}")
    print()

    for model in models:
        print(model.name)

except Exception:
    print("❌ Failed while listing models")
    traceback.print_exc()

print()

# ------------------------------------------------------------------
# Test Generation
# ------------------------------------------------------------------

print("=" * 80)
print("GENERATION TEST")
print("=" * 80)

TEST_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
]

for model_name in TEST_MODELS:

    print(f"\nTesting: {model_name}")

    try:

        response = client.models.generate_content(
            model=model_name,
            contents="Reply with exactly SUCCESS"
        )

        print("✅ SUCCESS")
        print(response.text)

    except Exception as e:

        print("❌ FAILED")
        print(type(e).__name__)
        print(str(e))

print()

print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)