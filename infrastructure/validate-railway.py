#!/usr/bin/env python3
"""
Railway Deployment Validation
Checks if everything is ready for deployment
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - MISSING")
        return False

def check_requirements():
    """Check if requirements.txt has Railway dependencies"""
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "gunicorn",
            "asyncpg",
            "psycopg2-binary",
            "sqlalchemy",
            "slack-sdk",
            "openai"
        ]
        
        missing = []
        for package in required_packages:
            if package not in content:
                missing.append(package)
        
        if not missing:
            print("✅ Requirements.txt has all Railway dependencies")
            return True
        else:
            print(f"❌ Requirements.txt missing: {', '.join(missing)}")
            return False
            
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def check_config_imports():
    """Check if src/config.py has Railway functions"""
    try:
        with open("src/config.py", "r") as f:
            content = f.read()
        
        required_functions = [
            "is_railway",
            "get_port", 
            "get_database_url"
        ]
        
        missing = []
        for func in required_functions:
            if f"def {func}" not in content:
                missing.append(func)
        
        if not missing:
            print("✅ Config.py has all Railway functions")
            return True
        else:
            print(f"❌ Config.py missing functions: {', '.join(missing)}")
            return False
            
    except FileNotFoundError:
        print("❌ src/config.py not found")
        return False

def validate_run_script():
    """Check if run.py is Railway-ready"""
    try:
        with open("run.py", "r") as f:
            content = f.read()
        
        checks = [
            ("is_railway", "Railway detection"),
            ("get_port", "Port detection"),
            ("host = \"0.0.0.0\"", "Host binding"),
            ("workers=1", "Single worker config")
        ]
        
        all_good = True
        for check, description in checks:
            if check in content:
                print(f"✅ Run.py {description}")
            else:
                print(f"❌ Run.py missing {description}")
                all_good = False
                
        return all_good
        
    except FileNotFoundError:
        print("❌ run.py not found")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating Railway deployment readiness...")
    print("="*60)
    
    all_checks = []
    
    # Check required files
    print("\n📁 CHECKING FILES:")
    all_checks.append(check_file_exists("railway.toml", "Railway config"))
    all_checks.append(check_file_exists("Procfile", "Process file"))
    all_checks.append(check_file_exists("requirements.txt", "Python dependencies"))
    all_checks.append(check_file_exists("run.py", "Main entry point"))
    all_checks.append(check_file_exists("src/config.py", "Configuration module"))
    all_checks.append(check_file_exists("src/database.py", "Database module"))
    all_checks.append(check_file_exists("src/main.py", "FastAPI app"))
    all_checks.append(check_file_exists("RAILWAY-DEPLOY.md", "Deploy guide"))
    all_checks.append(check_file_exists("generate-secrets.py", "Secret generator"))
    
    # Check dependencies
    print("\n📦 CHECKING DEPENDENCIES:")
    all_checks.append(check_requirements())
    
    # Check configuration
    print("\n⚙️ CHECKING CONFIGURATION:")
    all_checks.append(check_config_imports())
    all_checks.append(validate_run_script())
    
    # Final verdict
    print("\n" + "="*60)
    if all(all_checks):
        print("🎉 VALIDATION PASSED! Ready for Railway deployment!")
        print("\n🚀 NEXT STEPS:")
        print("1. Run: python generate-secrets.py")
        print("2. Fork this repo to your GitHub")
        print("3. Deploy on Railway following RAILWAY-DEPLOY.md")
        print("4. Configure environment variables")
        print("5. Add PostgreSQL service")
        print("6. Deploy! 🔥")
        return True
    else:
        print("❌ VALIDATION FAILED! Fix the issues above first.")
        failed_count = len([x for x in all_checks if not x])
        print(f"   {failed_count} issues need to be resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 