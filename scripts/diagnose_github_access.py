#!/usr/bin/env python3
"""Diagnose GitHub repository_dispatch access issues."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_token(token_name, token_value, owner, repo):
    """Test a GitHub token's access to repository_dispatch."""
    print(f"\n{'='*60}")
    print(f"Testing: {token_name}")
    print(f"{'='*60}")
    
    if not token_value:
        print(f"❌ {token_name} not set in environment")
        return False
    
    print(f"✓ Token found (starts with: {token_value[:7]}...)")
    
    # Test 1: Check repository access
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token_value}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    print(f"\n1. Testing repository access...")
    print(f"   GET {repo_url}")
    
    response = requests.get(repo_url, headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Repository accessible: {data['full_name']}")
        print(f"   Private: {data['private']}")
    elif response.status_code == 404:
        print(f"   ❌ Repository not found or no access")
        return False
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {response.text[:200]}")
        return False
    
    # Test 2: Check token scopes
    print(f"\n2. Checking token scopes...")
    user_url = "https://api.github.com/user"
    response = requests.get(user_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        scopes = response.headers.get("X-OAuth-Scopes", "")
        print(f"   Token scopes: {scopes}")
        
        required_scopes = ["repo", "workflow"]
        has_required = all(scope in scopes for scope in required_scopes)
        
        if has_required:
            print(f"   ✅ Has required scopes: {', '.join(required_scopes)}")
        else:
            print(f"   ⚠️  Missing scopes!")
            print(f"   Required: {', '.join(required_scopes)}")
            print(f"   Found: {scopes}")
            print(f"\n   To fix:")
            print(f"   1. Go to https://github.com/settings/tokens")
            print(f"   2. Create new token with 'repo' and 'workflow' scopes")
            print(f"   3. Save as GITHUB_PAT in .env")
            return False
    else:
        print(f"   ⚠️  Could not check scopes: {response.status_code}")
    
    # Test 3: Try repository_dispatch
    print(f"\n3. Testing repository_dispatch endpoint...")
    dispatch_url = f"https://api.github.com/repos/{owner}/{repo}/dispatches"
    
    test_payload = {
        "event_type": "test-connection",
        "client_payload": {
            "test": True,
            "message": "Testing connection from diagnostic script"
        }
    }
    
    print(f"   POST {dispatch_url}")
    response = requests.post(
        dispatch_url,
        json=test_payload,
        headers=headers,
        timeout=10
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 204:
        print(f"   ✅ Successfully triggered repository_dispatch!")
        print(f"\n   Check GitHub Actions:")
        print(f"   https://github.com/{owner}/{repo}/actions")
        return True
    elif response.status_code == 404:
        print(f"   ❌ 404 Not Found - Token lacks 'workflow' scope")
        print(f"\n   Solution:")
        print(f"   This token cannot trigger workflows.")
        print(f"   You need a Personal Access Token (PAT) with 'workflow' scope.")
        return False
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {response.text}")
        return False

def main():
    """Main diagnostic function."""
    print("\n" + "="*60)
    print("GitHub repository_dispatch Diagnostic Tool")
    print("="*60)
    
    owner = os.getenv("GITHUB_OWNER", "")
    repo = os.getenv("GITHUB_REPO", "")
    
    if not owner or not repo:
        print("\n❌ Error: GITHUB_OWNER and GITHUB_REPO must be set")
        print("\nAdd to .env file:")
        print("  GITHUB_OWNER=Karthi-Knackforge")
        print("  GITHUB_REPO=cms-project")
        return
    
    print(f"\nTarget Repository: {owner}/{repo}")
    
    # Test GITHUB_TOKEN (standard token)
    github_token = os.getenv("GITHUB_TOKEN", "")
    if github_token:
        result1 = test_token("GITHUB_TOKEN", github_token, owner, repo)
    else:
        print(f"\nℹ️  GITHUB_TOKEN not set (this is OK)")
        result1 = False
    
    # Test GITHUB_PAT (personal access token)
    github_pat = os.getenv("GITHUB_PAT", "")
    if github_pat:
        result2 = test_token("GITHUB_PAT", github_pat, owner, repo)
    else:
        print(f"\n⚠️  GITHUB_PAT not set")
        print(f"\nThis is the token you need for repository_dispatch!")
        print(f"\nTo create:")
        print(f"1. Go to https://github.com/settings/tokens")
        print(f"2. Generate new token (classic)")
        print(f"3. Select scopes: 'repo' and 'workflow'")
        print(f"4. Add to .env: GITHUB_PAT=ghp_your_token")
        result2 = False
    
    # Summary
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if result2:
        print("✅ GITHUB_PAT works for repository_dispatch")
        print("\nYou can use this token in Jira automation!")
    elif result1:
        print("⚠️  GITHUB_TOKEN works for repo access but NOT for workflows")
        print("\nYou need a Personal Access Token (PAT) with 'workflow' scope")
    else:
        print("❌ No working token found")
        print("\nAction Required:")
        print("1. Create GitHub Personal Access Token")
        print("2. Add to .env as GITHUB_PAT")
        print("3. Run this script again to verify")
    
    print()

if __name__ == "__main__":
    main()
