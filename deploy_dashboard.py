"""
Deploy ZeroCarb Dashboard to AWS S3

This script:
1. Creates an S3 bucket for static website hosting
2. Uploads all dashboard files
3. Configures bucket for public website access
4. Outputs the website URL

Usage:
    python deploy_dashboard.py

Requirements:
    - AWS credentials configured (via environment variables or .env)
    - boto3 installed
"""

import os
import sys
import boto3
import mimetypes
from pathlib import Path

# Configuration
BUCKET_NAME = 'zerocarb-dashboard-prod'
REGION = 'eu-west-2'
DASHBOARD_PATH = Path(__file__).parent / 'dashboard' / 'public'

def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / 'config' / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value

def get_content_type(filename):
    """Get the correct content type for a file."""
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
    }
    ext = Path(filename).suffix.lower()
    return content_types.get(ext, 'application/octet-stream')

def create_bucket(s3_client, bucket_name, region):
    """Create S3 bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket {bucket_name} already exists")
        return True
    except:
        pass
    
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✅ Created bucket: {bucket_name}")
        return True
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        return False

def configure_website(s3_client, bucket_name):
    """Configure bucket for static website hosting."""
    try:
        # Enable static website hosting
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
        )
        print("✅ Configured static website hosting")
        
        # Set bucket policy for public read access
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        import json
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("✅ Set public read policy")
        
        # Disable block public access
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        print("✅ Disabled public access block")
        
        return True
    except Exception as e:
        print(f"❌ Error configuring website: {e}")
        return False

def upload_files(s3_client, bucket_name, source_path):
    """Upload all files from source path to S3."""
    uploaded = 0
    errors = 0
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            # Skip test files and markdown
            if file_path.suffix in ['.md', '.test.html']:
                continue
            
            relative_path = file_path.relative_to(source_path)
            key = str(relative_path).replace('\\', '/')
            content_type = get_content_type(file_path.name)
            
            try:
                with open(file_path, 'rb') as f:
                    s3_client.put_object(
                        Bucket=bucket_name,
                        Key=key,
                        Body=f.read(),
                        ContentType=content_type,
                        CacheControl='max-age=3600'
                    )
                print(f"   ✓ {key}")
                uploaded += 1
            except Exception as e:
                print(f"   ✗ {key}: {e}")
                errors += 1
    
    return uploaded, errors

def main():
    print("=" * 60)
    print("ZeroCarb Dashboard Deployment")
    print("=" * 60)
    
    # Load environment
    load_env()
    
    # Check dashboard path
    if not DASHBOARD_PATH.exists():
        print(f"❌ Dashboard path not found: {DASHBOARD_PATH}")
        return 1
    
    print(f"\n📁 Source: {DASHBOARD_PATH}")
    print(f"🪣 Bucket: {BUCKET_NAME}")
    print(f"🌍 Region: {REGION}")
    
    # Create S3 client
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        
        # Verify credentials
        sts = boto3.client('sts', region_name=REGION)
        identity = sts.get_caller_identity()
        print(f"\n✅ AWS Account: {identity['Account']}")
    except Exception as e:
        print(f"\n❌ AWS credentials error: {e}")
        print("   Make sure AWS credentials are configured")
        return 1
    
    # Create bucket
    print("\n📦 Creating S3 bucket...")
    if not create_bucket(s3_client, BUCKET_NAME, REGION):
        return 1
    
    # Configure website
    print("\n🌐 Configuring website hosting...")
    if not configure_website(s3_client, BUCKET_NAME):
        return 1
    
    # Upload files
    print("\n📤 Uploading files...")
    uploaded, errors = upload_files(s3_client, BUCKET_NAME, DASHBOARD_PATH)
    
    print(f"\n✅ Uploaded: {uploaded} files")
    if errors > 0:
        print(f"❌ Errors: {errors} files")
    
    # Output website URL
    website_url = f"http://{BUCKET_NAME}.s3-website.{REGION}.amazonaws.com"
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\n🌐 Website URL: {website_url}")
    print("\nNote: It may take a few minutes for the website to be accessible.")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
