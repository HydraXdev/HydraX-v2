#!/usr/bin/env python3
"""
Test script for /connect command functionality
"""

import sys
import re

def test_parse_connect_credentials(message_text):
    """Test version of credential parsing"""
    try:
        lines = message_text.split('\n')
        login_id = None
        password = None
        server_name = None
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('login:'):
                login_id = line.split(':', 1)[1].strip()
            elif line.lower().startswith('password:'):
                password = line.split(':', 1)[1].strip()
            elif line.lower().startswith('server:'):
                server_name = line.split(':', 1)[1].strip()
        
        if login_id and password and server_name:
            try:
                login_id = int(login_id)
                return (login_id, password, server_name)
            except ValueError:
                return None
        return None
    except Exception as e:
        print(f"Credential parsing error: {e}")
        return None

def test_validation(login_id, password, server_name):
    """Test parameter validation"""
    try:
        # Validate login ID (should be positive integer)
        if not isinstance(login_id, int) or login_id <= 0:
            return False
        
        # Validate password (basic checks)
        if not password or len(password) < 4 or len(password) > 100:
            return False
        
        # Validate server name (should be alphanumeric with allowed special chars)
        if not server_name or len(server_name) > 50:
            return False
        
        # Server name should only contain safe characters
        import string
        allowed_chars = string.ascii_letters + string.digits + '-._'
        if not all(c in allowed_chars for c in server_name):
            return False
        
        # Security: Check for potential injection attempts
        dangerous_patterns = [';', '&&', '||', '`', '$', '(', ')', '|']
        for pattern in dangerous_patterns:
            if pattern in password or pattern in server_name:
                print(f"Potential injection attempt detected in credentials")
                return False
        
        return True
    except Exception as e:
        print(f"Parameter validation error: {e}")
        return False

def main():
    """Test the connect command parsing"""
    
    # Test case 1: Valid format
    print("=== TEST 1: Valid Format ===")
    test_message_1 = """/connect
Login: 843859
Password: MyP@ssw0rd
Server: Coinexx-Demo"""
    
    result = test_parse_connect_credentials(test_message_1)
    if result:
        login_id, password, server_name = result
        print(f"✅ Parsed successfully:")
        print(f"  Login: {login_id}")
        print(f"  Password: [HIDDEN]")
        print(f"  Server: {server_name}")
        
        if test_validation(login_id, password, server_name):
            print("✅ Validation passed")
        else:
            print("❌ Validation failed")
    else:
        print("❌ Parsing failed")
    
    # Test case 2: Invalid format
    print("\n=== TEST 2: Invalid Format ===")
    test_message_2 = """/connect
Login 843859
Password: MyP@ssw0rd
Server: Coinexx-Demo"""
    
    result = test_parse_connect_credentials(test_message_2)
    if result:
        print("❌ Should have failed parsing")
    else:
        print("✅ Correctly rejected invalid format")
    
    # Test case 3: Injection attempt
    print("\n=== TEST 3: Injection Attempt ===")
    test_message_3 = """/connect
Login: 843859
Password: MyPass; rm -rf /
Server: Coinexx-Demo"""
    
    result = test_parse_connect_credentials(test_message_3)
    if result:
        login_id, password, server_name = result
        print(f"Parsed: Login={login_id}, Server={server_name}")
        
        if test_validation(login_id, password, server_name):
            print("❌ Should have failed security validation")
        else:
            print("✅ Security validation correctly blocked injection attempt")
    else:
        print("❌ Parsing failed unexpectedly")
    
    # Test case 4: Mixed case format
    print("\n=== TEST 4: Mixed Case Format ===")
    test_message_4 = """/connect
LOGIN: 843859
Password: MyP@ssw0rd
SERVER: Coinexx-Demo"""
    
    result = test_parse_connect_credentials(test_message_4)
    if result:
        login_id, password, server_name = result
        print(f"✅ Mixed case parsing successful:")
        print(f"  Login: {login_id}")
        print(f"  Server: {server_name}")
    else:
        print("❌ Mixed case parsing failed")
    
    print("\n=== CONNECT COMMAND TESTS COMPLETE ===")

if __name__ == "__main__":
    main()