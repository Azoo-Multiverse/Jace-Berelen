#!/usr/bin/env python3
"""
Jace Berelen POC - Setup Test Script
Quick test to verify everything is ready to run
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all core components can be imported"""
    print("Testing imports...")
    
    try:
        from src import (
            settings, 
            validate_environment, 
            ai_client, 
            slack_handler,
            command_executor,
            ask_ai,
            run_command
        )
        print("All core imports successful")
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("Testing environment...")
    
    try:
        from src import validate_environment
        is_valid, missing = validate_environment()
        
        if is_valid:
            print("Environment validation passed")
            return True
        else:
            print(f"Environment validation failed. Missing: {', '.join(missing)}")
            print("Please set these in your .env file:")
            for var in missing:
                print(f"   - {var}")
            return False
    except Exception as e:
        print(f"Environment test failed: {e}")
        return False

def test_ai_client():
    """Test OpenRouter/AI client configuration"""
    print("Testing AI client configuration...")
    
    try:
        from src import ai_client
        config = ai_client.config
        
        if config["api_key"] and config["api_key"].startswith("sk-or-"):
            print("OpenRouter API key configured")
            print(f"Primary model: {config['model']}")
            print(f"Fallback model: {config['fallback_model']}")
            return True
        else:
            print("OpenRouter API key not properly configured")
            return False
    except Exception as e:
        print(f"AI client test failed: {e}")
        return False

def test_command_executor():
    """Test command executor setup"""
    print("Testing command executor...")
    
    try:
        from src import command_executor
        
        # Test workspace creation
        workspace = command_executor.set_workspace("test_task", "test_user")
        print(f"Command executor workspace created: {workspace}")
        
        # Test allowed commands
        allowed = command_executor.get_allowed_commands()
        print(f"{len(allowed)} command types whitelisted (aws, git, npm, etc.)")
        
        return True
    except Exception as e:
        print(f"Command executor test failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("Testing database setup...")
    
    try:
        from src import init_database, db_manager
        
        # Initialize database
        init_database()
        print("Database initialization successful")
        
        return True
    except Exception as e:
        print(f"Database test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for setup"""
    print("\n" + "="*60)
    print("NEXT STEPS TO START JACE BERELEN POC")
    print("="*60)
    
    print("\n1. Set up your .env file:")
    print("   cp environment.txt .env")
    print("   # Edit .env with your actual keys")
    
    print("\n2. Required keys:")
    print("   - OPENROUTER_API_KEY=sk-or-your-key-here")
    print("   - SLACK_BOT_TOKEN=xoxb-your-bot-token")
    print("   - SLACK_SIGNING_SECRET=your-signing-secret")
    print("   - SECRET_KEY=your-random-secret-key")
    
    print("\n3. Install dependencies:")
    print("   pip install -r requirements.txt")
    
    print("\n4. Run the application:")
    print("   python run.py")
    
    print("\n5. Access points:")
    print("   - API: http://localhost:8000")
    print("   - Docs: http://localhost:8000/docs")
    print("   - Health: http://localhost:8000/health")
    
    print("\n6. Slack commands:")
    print("   - /jace help")
    print("   - /tasks")
    print("   - /ai [question]")
    print("   - DM the bot directly")
    
    print("\n7. Command execution:")
    print("   - AWS CLI: 'aws s3 ls' (in task workspace)")
    print("   - Git: 'git status' (in task workspace)")
    print("   - Safe, isolated execution per task")

def main():
    """Run all tests"""
    print("JACE BERELEN POC - SETUP TEST\n")
    
    tests = [
        ("Imports", test_imports),
        ("Environment", test_environment),
        ("AI Client", test_ai_client),
        ("Command Executor", test_command_executor),
        ("Database", test_database)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("ALL TESTS PASSED! Ready to run Jace Berelen POC")
        show_next_steps()
    else:
        print("Some tests failed. Please fix issues before running.")
        print("\nCommon fixes:")
        print("- Create .env file with your API keys")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Check file permissions")

if __name__ == "__main__":
    main() 