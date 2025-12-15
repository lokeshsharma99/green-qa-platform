"""
Deploy ZeroCarb Dashboard to AWS CloudFront

This script:
1. Configures S3 bucket for CloudFront origin
2. Creates CloudFront distribution with OAC (Origin Access Control)
3. Invalidates cache after deployment

Usage:
    python deploy_cloudfront.py

Requirements:
    - AWS credentials configured
    - boto3 installed
    - S3 bucket already exists with dashboard files
"""

import boto3
import json
import time
import sys

# Configuration
BUCKET_NAME = 'zerocarb-dashboard'
REGION = 'eu-west-2'

def get_or_create_oac(cf_client, bucket_name):
    """Get or create Origin Access Control for S3."""
    oac_name = f'{bucket_name}-oac'
    
    # Check if OAC exists
    try:
        response = cf_client.list_origin_access_controls()
        for oac in response.get('OriginAccessControlList', {}).get('Items', []):
            if oac['Name'] == oac_name:
                print(f'✅ Found existing OAC: {oac["Id"]}')
                return oac['Id']
    except Exception as e:
        print(f'⚠️ Error listing OACs: {e}')
    
    # Create new OAC
    try:
        response = cf_client.create_origin_access_control(
            OriginAccessControlConfig={
                'Name': oac_name,
                'Description': f'OAC for {bucket_name}',
                'SigningProtocol': 'sigv4',
                'SigningBehavior': 'always',
                'OriginAccessControlOriginType': 's3'
            }
        )
        oac_id = response['OriginAccessControl']['Id']
        print(f'✅ Created OAC: {oac_id}')
        return oac_id
    except Exception as e:
        print(f'❌ Error creating OAC: {e}')
        return None

def find_existing_distribution(cf_client, bucket_name):
    """Find existing CloudFront distribution for the bucket."""
    try:
        paginator = cf_client.get_paginator('list_distributions')
        for page in paginator.paginate():
            items = page.get('DistributionList', {}).get('Items', [])
            for dist in items:
                for origin in dist.get('Origins', {}).get('Items', []):
                    if bucket_name in origin.get('DomainName', ''):
                        print(f'✅ Found existing distribution: {dist["Id"]}')
                        return dist['Id'], dist['DomainName']
    except Exception as e:
        print(f'⚠️ Error listing distributions: {e}')
    return None, None

def create_distribution(cf_client, bucket_name, oac_id):
    """Create CloudFront distribution."""
    s3_origin = f'{bucket_name}.s3.{REGION}.amazonaws.com'
    caller_ref = f'zerocarb-{int(time.time())}'
    
    config = {
        'CallerReference': caller_ref,
        'Comment': 'ZeroCarb Dashboard',
        'DefaultRootObject': 'index.html',
        'Origins': {
            'Quantity': 1,
            'Items': [{
                'Id': f's3-{bucket_name}',
                'DomainName': s3_origin,
                'S3OriginConfig': {'OriginAccessIdentity': ''},
                'OriginAccessControlId': oac_id
            }]
        },
        'DefaultCacheBehavior': {
            'TargetOriginId': f's3-{bucket_name}',
            'ViewerProtocolPolicy': 'redirect-to-https',
            'AllowedMethods': {
                'Quantity': 2,
                'Items': ['GET', 'HEAD'],
                'CachedMethods': {'Quantity': 2, 'Items': ['GET', 'HEAD']}
            },
            'CachePolicyId': '658327ea-f89d-4fab-a63d-7e88639e58f6',  # CachingOptimized
            'Compress': True
        },
        'CustomErrorResponses': {
            'Quantity': 1,
            'Items': [{
                'ErrorCode': 404,
                'ResponsePagePath': '/index.html',
                'ResponseCode': '200',
                'ErrorCachingMinTTL': 300
            }]
        },
        'PriceClass': 'PriceClass_100',  # US, Canada, Europe
        'Enabled': True,
        'HttpVersion': 'http2'
    }
    
    try:
        response = cf_client.create_distribution(DistributionConfig=config)
        dist_id = response['Distribution']['Id']
        domain = response['Distribution']['DomainName']
        print(f'✅ Created distribution: {dist_id}')
        print(f'🌐 Domain: https://{domain}')
        return dist_id, domain
    except Exception as e:
        print(f'❌ Error creating distribution: {e}')
        return None, None

def update_bucket_policy(s3_client, bucket_name, dist_id):
    """Update S3 bucket policy to allow CloudFront access."""
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCloudFrontServicePrincipal",
                "Effect": "Allow",
                "Principal": {"Service": "cloudfront.amazonaws.com"},
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*",
                "Condition": {
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{account_id}:distribution/{dist_id}"
                    }
                }
            }
        ]
    }
    
    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print('✅ Updated bucket policy for CloudFront access')
        return True
    except Exception as e:
        print(f'❌ Error updating bucket policy: {e}')
        return False

def invalidate_cache(cf_client, dist_id):
    """Invalidate CloudFront cache."""
    try:
        response = cf_client.create_invalidation(
            DistributionId=dist_id,
            InvalidationBatch={
                'Paths': {'Quantity': 1, 'Items': ['/*']},
                'CallerReference': f'invalidate-{int(time.time())}'
            }
        )
        inv_id = response['Invalidation']['Id']
        print(f'✅ Cache invalidation started: {inv_id}')
        return inv_id
    except Exception as e:
        print(f'❌ Error invalidating cache: {e}')
        return None

def main():
    print('=' * 60)
    print('ZeroCarb Dashboard - CloudFront Deployment')
    print('=' * 60)
    
    # Initialize clients
    cf_client = boto3.client('cloudfront')
    s3_client = boto3.client('s3', region_name=REGION)
    
    # Verify credentials
    try:
        identity = boto3.client('sts').get_caller_identity()
        print(f'\n✅ AWS Account: {identity["Account"]}')
    except Exception as e:
        print(f'\n❌ AWS credentials error: {e}')
        return 1
    
    # Check for existing distribution
    print('\n🔍 Checking for existing distribution...')
    dist_id, domain = find_existing_distribution(cf_client, BUCKET_NAME)
    
    if dist_id:
        print(f'\n📦 Using existing distribution: {dist_id}')
        print(f'🌐 URL: https://{domain}')
        
        # Invalidate cache
        print('\n🔄 Invalidating cache...')
        invalidate_cache(cf_client, dist_id)
    else:
        # Create OAC
        print('\n🔐 Setting up Origin Access Control...')
        oac_id = get_or_create_oac(cf_client, BUCKET_NAME)
        if not oac_id:
            return 1
        
        # Create distribution
        print('\n☁️ Creating CloudFront distribution...')
        dist_id, domain = create_distribution(cf_client, BUCKET_NAME, oac_id)
        if not dist_id:
            return 1
        
        # Update bucket policy
        print('\n🔒 Updating bucket policy...')
        update_bucket_policy(s3_client, BUCKET_NAME, dist_id)
    
    print('\n' + '=' * 60)
    print('DEPLOYMENT COMPLETE')
    print('=' * 60)
    print(f'\n🌐 Dashboard URL: https://{domain}')
    print('\n⏳ Note: New distributions take 5-10 minutes to deploy globally.')
    print('   Cache invalidations take 1-2 minutes to complete.')
    print('=' * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
