import os
from dotenv import load_dotenv

# Force load the .env file
load_dotenv()

def verify_infrastructure():
    print("\n--- 🔒 Environment & API Verification ---")
    
    # Define the keys we expect
    expected_keys = {
        "Hugging Face": "HF_TOKEN",
        "Google AI Studio": "GOOGLE_API_KEY",
        "Groq": "GROQ_API_KEY",
        "Weights & Biases": "WANDB_API_KEY"
    }
    
    all_clear = True
    
    for provider, env_var in expected_keys.items():
        key_value = os.getenv(env_var)
        if key_value:
            # Mask the key for security in the terminal output
            masked_key = f"{key_value[:4]}...{key_value[-4:]}" if len(key_value) > 8 else "****"
            print(f"✅ {provider:<18} : Loaded ({masked_key})")
        else:
            print(f"❌ {provider:<18} : MISSING (Check your .env file)")
            all_clear = False
            
    print("-" * 40)
    if all_clear:
        print("🚀 System Ready. All APIs are mapped.")
    else:
        print("⚠️ Warning: Missing credentials detected.")

if __name__ == "__main__":
    verify_infrastructure()