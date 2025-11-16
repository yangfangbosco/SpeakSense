"""
Example Workflow for SpeakSense
Demonstrates the complete pipeline from FAQ upload to query
"""
import requests
import json
import time
from pathlib import Path


# Service URLs
ASR_URL = "http://localhost:8001"
RETRIEVAL_URL = "http://localhost:8002"
ADMIN_URL = "http://localhost:8003"


def check_services():
    """Check if all services are running"""
    print("Checking services...")
    services = {
        "ASR Service": ASR_URL,
        "Retrieval Service": RETRIEVAL_URL,
        "Admin Service": ADMIN_URL
    }

    for name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ {name} is running")
            else:
                print(f"✗ {name} returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ {name} is not reachable: {e}")
            return False

    return True


def load_sample_faqs():
    """Load sample FAQ data"""
    faq_file = Path(__file__).parent / "sample_faqs.json"

    with open(faq_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def upload_faqs(faqs):
    """Upload FAQs to admin service"""
    print(f"\nUploading {len(faqs)} FAQs...")

    created_count = 0
    for idx, faq in enumerate(faqs, 1):
        try:
            response = requests.post(
                f"{ADMIN_URL}/admin/faq",
                json=faq,
                timeout=60  # TTS generation can take time
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  [{idx}/{len(faqs)}] Created FAQ: {faq['question'][:50]}...")
                print(f"      Answer ID: {result['answer_id']}")
                print(f"      Audio: {result['audio_path']}")
                created_count += 1
            else:
                print(f"  [{idx}/{len(faqs)}] Failed: {response.text}")

        except Exception as e:
            print(f"  [{idx}/{len(faqs)}] Error: {e}")

        # Small delay to avoid overwhelming the service
        time.sleep(0.5)

    print(f"\nSuccessfully uploaded {created_count}/{len(faqs)} FAQs")
    return created_count


def rebuild_indices():
    """Rebuild search indices"""
    print("\nRebuilding search indices...")

    try:
        response = requests.post(
            f"{RETRIEVAL_URL}/retrieval/rebuild_indices",
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Indices rebuilt successfully")
            print(f"  BM25 documents: {result.get('bm25_documents', 0)}")
            print(f"  Vector documents: {result.get('vector_documents', 0)}")
            return True
        else:
            print(f"✗ Failed to rebuild indices: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error rebuilding indices: {e}")
        return False


def test_retrieval(queries):
    """Test retrieval with sample queries"""
    print("\n" + "="*60)
    print("Testing Retrieval")
    print("="*60)

    for query_text, language in queries:
        print(f"\nQuery: {query_text}")
        print(f"Language: {language}")

        try:
            response = requests.post(
                f"{RETRIEVAL_URL}/retrieval/best_answer",
                json={
                    "query": query_text,
                    "language": language
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Match found:")
                print(f"  Question: {result['question']}")
                print(f"  Answer: {result['answer']}")
                print(f"  Audio: {result['audio_path']}")
                print(f"  Confidence: {result['confidence']:.3f}")
                print(f"  Matched by: {result['matched_by']}")
            elif response.status_code == 404:
                print(f"✗ No matching FAQ found")
            else:
                print(f"✗ Error: {response.text}")

        except Exception as e:
            print(f"✗ Error: {e}")

        time.sleep(0.5)


def test_asr():
    """Test ASR service (requires audio file)"""
    print("\n" + "="*60)
    print("Testing ASR (requires audio file)")
    print("="*60)

    # This is just an example - you would need an actual audio file
    print("\nTo test ASR, send an audio file:")
    print("  curl -X POST 'http://localhost:8001/asr/transcribe' \\")
    print("    -F 'file=@your_audio.mp3' \\")
    print("    -F 'language=auto'")


def get_stats():
    """Get statistics from all services"""
    print("\n" + "="*60)
    print("System Statistics")
    print("="*60)

    # Admin stats
    try:
        response = requests.get(f"{ADMIN_URL}/admin/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\nAdmin Service:")
            print(f"  Total FAQs: {stats['total_faqs']}")
            print(f"  Categories: {', '.join(stats['categories'])}")
            print(f"  Languages: {', '.join(stats['languages'])}")
    except Exception as e:
        print(f"Failed to get admin stats: {e}")

    # Retrieval stats
    try:
        response = requests.get(f"{RETRIEVAL_URL}/retrieval/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\nRetrieval Service:")
            print(f"  BM25 documents: {stats['bm25_documents']}")
            print(f"  Vector documents: {stats['vector_documents']}")
            print(f"  BM25 weight: {stats['bm25_weight']}")
            print(f"  Vector weight: {stats['vector_weight']}")
    except Exception as e:
        print(f"Failed to get retrieval stats: {e}")

    # ASR info
    try:
        response = requests.get(f"{ASR_URL}/asr/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"\nASR Service:")
            print(f"  Model: {info['model_type']} - {info['model_name']}")
            print(f"  Device: {info['device']}")
    except Exception as e:
        print(f"Failed to get ASR info: {e}")


def main():
    """Main workflow"""
    print("="*60)
    print("SpeakSense Example Workflow")
    print("="*60)

    # 1. Check services
    if not check_services():
        print("\n✗ Please start all services before running this script")
        print("  Terminal 1: cd services/asr_service && python main.py")
        print("  Terminal 2: cd services/retrieval_service && python main.py")
        print("  Terminal 3: cd services/admin_service && python main.py")
        return

    # 2. Load and upload FAQs
    faqs = load_sample_faqs()
    uploaded = upload_faqs(faqs)

    if uploaded == 0:
        print("\n✗ No FAQs were uploaded. Exiting.")
        return

    # 3. Rebuild indices
    if not rebuild_indices():
        print("\n✗ Failed to rebuild indices. Retrieval may not work.")
        return

    # 4. Test retrieval with sample queries
    test_queries = [
        ("图书馆几点关门？", "zh"),
        ("What time does the library close?", "en"),
        ("如何借书？", "zh"),
        ("How to borrow books?", "en"),
        ("有WiFi吗？", "zh"),
        ("Is there WiFi?", "en"),
    ]

    test_retrieval(test_queries)

    # 5. Show ASR testing info
    test_asr()

    # 6. Display statistics
    get_stats()

    print("\n" + "="*60)
    print("Workflow Complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Test ASR by sending audio files to http://localhost:8001/asr/transcribe")
    print("  2. Check API docs at:")
    print("     - http://localhost:8001/docs (ASR)")
    print("     - http://localhost:8002/docs (Retrieval)")
    print("     - http://localhost:8003/docs (Admin)")
    print("  3. View generated audio files in: data/audio_files/")


if __name__ == "__main__":
    main()
