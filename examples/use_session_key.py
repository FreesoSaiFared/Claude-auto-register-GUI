#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example script: How to access Claude AI using a saved SessionKey
"""

import requests
import json
import os
import sys

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_session_key(file_path):
    """Read the saved SessionKey"""
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: file {file_path} not found")
        return None


def send_message_to_claude(session_key, message, conversation_id=None):
    """
    Send a message to Claude using SessionKey
    
    Args:
        session_key: Claude的SessionKey
        message: The message content to be sent
        conversation_id: Optional, existing session ID
        
    Returns:
        Response JSON or error message
    """
    # API endpoint
    base_url = "https://claude.ai/api"
    
    # Set request headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"sessionKey={session_key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Create a new session (if no session ID is provided)
    if not conversation_id:
        try:
            # Get Organization ID
            org_response = requests.get(f"{base_url}/organizations", headers=headers)
            org_response.raise_for_status()
            org_data = org_response.json()
            if len(org_data) == 0:
                return {"error": "Unable to retrieve organization ID"}
            
            organization_id = org_data[0]["uuid"]
            
            # Create a new session
            create_data = {
                "name": "",
                "organization_id": organization_id
            }
            create_response = requests.post(
                f"{base_url}/organizations/{organization_id}/chat_conversations",
                headers=headers,
                json=create_data
            )
            create_response.raise_for_status()
            conversation_id = create_response.json()["uuid"]
            
        except requests.RequestException as e:
            return {"error": f"Session creation failed: {str(e)}"}
    
    # Send message
    try:
        message_data = {
            "attachments": [],
            "completion": {
                "prompt": "",
                "timezone": "Asia/Shanghai",
                "model": "claude-3-opus-20240229"
            },
            "organization_id": organization_id,
            "conversation_id": conversation_id,
            "text": message
        }
        
        message_response = requests.post(
            f"{base_url}/append_message",
            headers=headers,
            json=message_data,
            stream=True
        )
        message_response.raise_for_status()
        
        # Read streaming response
        full_response = ""
        for line in message_response.iter_lines():
            if line:
                try:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:] # Remove the "data: " prefix
                        if json_str != "[DONE]":
                            chunk = json.loads(json_str)
                            if "completion" in chunk:
                                full_response += chunk["completion"]
                except Exception as e:
                    print(f"Error parsing response: {e}")
        
        return {
            "conversation_id": conversation_id,
            "response": full_response
        }
        
    except requests.RequestException as e:
        return {"error": f"Message sending failed: {str(e)}"}


def main():
    # Read SessionKey
    session_key_file = "../sessionKey.txt" # Adjust the path according to the actual situation
    session_key = read_session_key(session_key_file)
    
    if not session_key:
        print("Unable to read SessionKey. Please run the registration program to generate SessionKey first.")
        return
    
    print("SessionKey successfully read!")
    
    # Example of sending a message
    message = "Hello, Claude! Please briefly introduce yourself."
    print(f"\nSent message: '{message}'")
    
    result = send_message_to_claude(session_key, message)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nClaude's reply:")
        print("="*50)
        print(result["response"])
        print("="*50)
        print(f"\nSession ID: {result['conversation_id']}")
        print("\nYou can use this session ID to continue the conversation")


if __name__ == "__main__":
    main() 
