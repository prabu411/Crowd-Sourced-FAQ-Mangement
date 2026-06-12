import sys
import subprocess
import os
import time

def install_dependencies():
    """Installs required packages from requirements.txt."""
    print("=" * 60)
    print("  Crowd FAQs - Automated Setup & Startup Script")
    print("  Developer Module: Mohd Warish (Backend Dev)")
    print("=" * 60)
    print("\n[+] Checking and installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("[+] Dependencies resolved successfully!")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error installing dependencies: {e}")
        print("[!] Trying manual fallback installations...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic"
            ])
            print("[+] Fallback installation succeeded!")
        except Exception as ex:
            print(f"[-] Critical Error: Could not install python packages: {ex}")
            sys.exit(1)

def run_server():
    """Starts the Uvicorn web server."""
    print("\n[+] Initializing FastAPI Uvicorn Server...")
    print("[+] Database loaded: SQLite 'crowd_faqs.db'")
    print("[+] Mock Stage 2 NLP Clustering Engine activated.")
    print("\n" + "=" * 60)
    print("  Crowd FAQs Platform is now running locally!")
    print("  -> Access the Interactive Hub here: http://127.0.0.1:8000")
    print("  -> Access REST API documentation:    http://127.0.0.1:8000/docs")
    print("=" * 60)
    print("\n[!] Press CTRL+C to terminate the server.\n")
    
    # Import uvicorn locally to run
    try:
        import uvicorn
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n[-] Server terminated by user.")
    except Exception as e:
        print(f"[-] Server failed to boot: {e}")

if __name__ == "__main__":
    # Ensure working directory is set to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    install_dependencies()
    # Give DB initialization a small margin
    time.sleep(0.5)
    run_server()
