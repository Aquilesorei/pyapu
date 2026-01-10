from strutex import DocumentProcessor

def test_processor_init():
    print("Verifying Processor Initialization...")
    dp = DocumentProcessor(provider="gemini")
    
    try:
        print("1. Initializing SequentialProcessor...")
        seq = dp.create_sequential(chunk_size_pages=1)
        print("   ✅ SequentialProcessor OK")
        
        print("2. Initializing PrivacyProcessor...")
        priv = dp.create_privacy()
        print("   ✅ PrivacyProcessor OK")
        
        print("3. Initializing ActiveLearningProcessor...")
        active = dp.create_active(num_trials=2)
        print("   ✅ ActiveLearningProcessor OK")
        
        print("\n🎉 All processor initializations passed!")
        
    except AttributeError as e:
        print(f"\n❌ Initialization failed with AttributeError: {e}")
    except Exception as e:
        print(f"\n❌ Initialization failed with unexpected error: {e}")

if __name__ == "__main__":
    test_processor_init()
