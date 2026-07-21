import boto3
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

def read_metadata_files(bucket_name: str, metadata_prefix: str = "metadata/") -> List[Dict[str, Any]]:
    """Read all JSON files from the metadata directory in an S3 bucket."""
    s3_client = boto3.client('s3')
    metadata_objects = []
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=metadata_prefix)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key = obj['Key']
                
                if key == metadata_prefix or not key.endswith('.json'):
                    continue
                
                try:
                    response = s3_client.get_object(Bucket=bucket_name, Key=key)
                    file_content = response['Body'].read().decode('utf-8')
                    file_data = json.loads(file_content)
                    datasets = file_data.get("datasets", [])
                    for dataset in datasets:  
                      metadata_entry = extract_properties(dataset, key)
                      metadata_objects.append(metadata_entry)
                    
                    print(f"✓ Processed: {key}")
                except json.JSONDecodeError as e:
                    print(f"✗ Invalid JSON in {key}: {e}")
                except Exception as e:
                    print(f"✗ Error reading {key}: {e}")
        
        print(f"\nTotal metadata entries processed: {len(metadata_objects)}")
        return metadata_objects
    
    except Exception as e:
        print(f"✗ Error listing bucket contents: {e}")
        return []


def extract_properties(metadata: Dict[str, Any], key) -> Dict[str, Any]:
    """Extract specific properties from a metadata JSON file."""
    entry = {
        "download_url": f"https://grma-data.s3.eu-west-2.amazonaws.com/datasets/{key.removeprefix("metadata/rdls_").removesuffix('.json')}.zip",
        "id": metadata["id"],
        "title": metadata["title"],
        "risk_data_type": metadata["risk_data_type"],
        "description": metadata.get("description"),
        "countries": metadata.get("spatial",{}).get("countries",[]),
        "resources": metadata.get('resources',[])
    }
    
    return {k: v for k, v in entry.items()}


def create_metadata_index(bucket_name: str, metadata_list: List[Dict[str, Any]]) -> None:
    """Upload the combined metadata.json file to the S3 bucket root."""
    s3_client = boto3.client('s3')
    
    combined_metadata = {
        "version": "1.0",
        "count": len(metadata_list),
        "objects": metadata_list
    }
    
    metadata_json = json.dumps(combined_metadata, indent=2, default=str)
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key='metadata.json',
            Body=metadata_json,
            ContentType='application/json'
        )
        print(f"✓ Successfully uploaded metadata.json ({len(metadata_list)} entries)")
    except Exception as e:
        print(f"✗ Error uploading metadata.json: {e}")


def main() -> None:
    """Main function to orchestrate metadata file processing."""
    bucket_name = os.getenv('BUCKET_NAME')
    
    if not bucket_name:
        print("✗ Error: BUCKET_NAME not set in .env file")
        return
    
    print(f"Starting metadata index generation for bucket: {bucket_name}\n")
    
    metadata_objects = read_metadata_files(bucket_name)
    
    if metadata_objects:
        create_metadata_index(bucket_name, metadata_objects)
        print("\n✓ Metadata index generation complete!")
    else:
        print("\n✗ No metadata files found or an error occurred")


if __name__ == "__main__":
    main()
