import boto3
import uuid
import json
import time
from typing import Dict, Any, List

def validate_input(sender_id: str, countries: List[str]) -> bool:
    if not 1 <= len(sender_id) <= 11:
        raise ValueError("Sender ID must be between 1 and 11 characters")
    
    if not sender_id.replace('_', '').replace('-', '').isalnum():
        raise ValueError("Sender ID can only contain alphanumeric characters, underscore, and hyphen")
    
    if not countries:
        raise ValueError("At least one country code must be provided")
    
    return True

def request_sender_id(client, sender_id: str, countries: List[str], message_types: List[str] = None, tags: List[Dict] = None) -> List[Dict]:
    if message_types is None:
        message_types = ["TRANSACTIONAL", "PROMOTIONAL"]
    
    results = []
    
    for i, country in enumerate(countries):
        if i > 0:
            time.sleep(1)  # Rate limiting: 1 request per second
            
        try:
            print(f"Processing country: {country} ({i+1}/{len(countries)})")
            request_params = {
                'ClientToken': str(uuid.uuid4()),
                'SenderId': sender_id,
                'IsoCountryCode': country.upper(),
                'MessageTypes': message_types,
                'DeletionProtectionEnabled': False
            }
            
            if tags:
                request_params['Tags'] = tags
                
            response = client.request_sender_id(**request_params)
            
            results.append({
                'Country': country,
                'Status': 'Success',
                'SenderIdArn': response.get('SenderIdArn'),
                'MonthlyLeasingPrice': response.get('MonthlyLeasingPrice')
            })
            
        except Exception as e:
            results.append({
                'Country': country,
                'Status': 'Failed',
                'Error': str(e)
            })
            
        print(f"Completed {country}: {'Success' if results[-1]['Status'] == 'Success' else 'Failed'}")
    
    return results

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Extract parameters from event
        sender_id = event['sender_id']
        countries = [c.strip().upper() for c in event['countries'] if c.strip()]
        tags = event.get('tags')  # Optional
        message_types = event.get('message_types', ["TRANSACTIONAL", "PROMOTIONAL"])  # Optional
        
        # Validate input
        validate_input(sender_id, countries)
        
        # Initialize the AWS SMS Voice v2 client
        client = boto3.client('pinpoint-sms-voice-v2')
        
        # Process the request
        results = request_sender_id(
            client=client,
            sender_id=sender_id,
            countries=countries,
            message_types=message_types,
            tags=tags
        )
        
        # Calculate summary
        successful = sum(1 for r in results if r['Status'] == 'Success')
        
        return {
            'statusCode': 200,
            'body': {
                'results': results,
                'summary': {
                    'total': len(countries),
                    'successful': successful,
                    'failed': len(countries) - successful
                }
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
