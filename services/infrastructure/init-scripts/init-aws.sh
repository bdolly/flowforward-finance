#!/bin/bash
# LocalStack initialization script
# This runs automatically when LocalStack is ready

set -e

echo "=== Initializing LocalStack AWS Resources ==="

# ============================================
# KMS - Create encryption keys
# ============================================
echo "Creating KMS keys..."

# Create a master key for general encryption
KMS_KEY_ID=$(awslocal kms create-key \
    --description "FlowForward master encryption key" \
    --query 'KeyMetadata.KeyId' \
    --output text)

echo "Created KMS key: $KMS_KEY_ID"

# Create an alias for easier reference
awslocal kms create-alias \
    --alias-name alias/flowforward-master-key \
    --target-key-id "$KMS_KEY_ID"

echo "Created alias: alias/flowforward-master-key"

# ============================================
# SQS - Create queues
# ============================================
echo "Creating SQS queues..."

# Dead letter queue for failed messages
awslocal sqs create-queue \
    --queue-name flowforward-events-dlq \
    --attributes '{
        "MessageRetentionPeriod": "1209600",
        "VisibilityTimeout": "30"
    }'

echo "Created DLQ: flowforward-events-dlq"

# Get DLQ ARN for redrive policy
DLQ_ARN=$(awslocal sqs get-queue-attributes \
    --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/flowforward-events-dlq \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)

# Main events queue with DLQ
awslocal sqs create-queue \
    --queue-name flowforward-events \
    --attributes "{
        \"MessageRetentionPeriod\": \"345600\",
        \"VisibilityTimeout\": \"60\",
        \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
    }"

echo "Created queue: flowforward-events"

# Auth events queue
awslocal sqs create-queue \
    --queue-name flowforward-auth-events \
    --attributes "{
        \"MessageRetentionPeriod\": \"345600\",
        \"VisibilityTimeout\": \"60\",
        \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
    }"

echo "Created queue: flowforward-auth-events"

# Account events queue
awslocal sqs create-queue \
    --queue-name flowforward-account-events \
    --attributes "{
        \"MessageRetentionPeriod\": \"345600\",
        \"VisibilityTimeout\": \"60\",
        \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
    }"

echo "Created queue: flowforward-account-events"

# ============================================
# SNS - Create topics
# ============================================
echo "Creating SNS topics..."

# Auth events topic
AUTH_TOPIC_ARN=$(awslocal sns create-topic \
    --name flowforward-auth-events \
    --query 'TopicArn' \
    --output text)

echo "Created SNS topic: $AUTH_TOPIC_ARN"

# Account events topic
ACCOUNT_TOPIC_ARN=$(awslocal sns create-topic \
    --name flowforward-account-events \
    --query 'TopicArn' \
    --output text)

echo "Created SNS topic: $ACCOUNT_TOPIC_ARN"

# General events topic
EVENTS_TOPIC_ARN=$(awslocal sns create-topic \
    --name flowforward-events \
    --query 'TopicArn' \
    --output text)

echo "Created SNS topic: $EVENTS_TOPIC_ARN"

# ============================================
# Verification
# ============================================
echo ""
echo "=== LocalStack Resources Created ==="
echo ""
echo "KMS Keys:"
awslocal kms list-aliases --query 'Aliases[?starts_with(AliasName, `alias/flowforward`)]' --output table

echo ""
echo "SQS Queues:"
awslocal sqs list-queues --query 'QueueUrls' --output table

echo ""
echo "SNS Topics:"
awslocal sns list-topics --query 'Topics[?contains(TopicArn, `flowforward`)]' --output table

echo ""
echo "=== LocalStack initialization complete ==="

