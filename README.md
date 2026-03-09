# AWS Architecture Agent

An AI agent that designs AWS architectures from plain-English prompts and outputs diagrams.

Give it a prompt like _"serverless e-commerce backend with auth and payments"_ and it returns a PNG architecture diagram with official AWS service icons, a Well-Architected Framework review, and a plain-English explanation.

## How It Works

```
prompt → Claude designs architecture → renders PNG diagram → critic reviews → explanation
```

Built with LangGraph — the agent loops back and revises the architecture if the critic flags issues, up to a maximum of 2 revisions.

## Example Output

```
python main.py "Design a serverless e-commerce backend"
```

```
DIAGRAM: /path/to/outputs/arch_b8742b80.png
CRITIQUE: APPROVED: Well-architected serverless design with proper security and observability layers.
EXPLANATION:
## Architecture Overview
...
```

## Stack

- **Claude claude-opus-4-6** — architecture reasoning via Anthropic API
- **LangGraph** — agent graph orchestration
- **diagrams** (mingrammer) — PNG rendering with official AWS icons

## Setup

**Prerequisites**

```bash
brew install graphviz    # Mac
# apt-get install graphviz  # Linux
```

**Install**

```bash
git clone <repo>
cd llm-project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Configure**

```bash
cp .env.example .env
# add your ANTHROPIC_API_KEY to .env
```

## Usage

```bash
python main.py "Design a 3-tier web app with RDS and CloudFront"
python main.py "Multi-region serverless API with DynamoDB global tables"
python main.py "Data pipeline from Kinesis to Redshift with Glue ETL"
```

Diagrams are saved to `outputs/` in the project root.

## Supported AWS Services

| Category | Services |
|----------|---------|
| Compute | Lambda, EC2, ECS, EKS, Fargate, Batch |
| Database | RDS, DynamoDB, ElastiCache, Aurora, Redshift |
| Network | APIGateway, CloudFront, Route53, VPC, ELB, ALB, NLB |
| Storage | S3, EFS, Glacier |
| Messaging | SQS, SNS, EventBridge, StepFunctions |
| Security | IAM, Cognito, WAF, KMS |
| Management | CloudWatch, CloudTrail |
| Analytics | Kinesis, Athena, Glue |
| ML | SageMaker, Rekognition |
