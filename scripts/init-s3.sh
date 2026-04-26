#!/bin/bash
# Create S3 buckets in LocalStack for local development

awslocal s3 mb s3://resume-normalizer-uploads
awslocal s3 mb s3://resume-normalizer-generated

echo "S3 buckets created successfully"
