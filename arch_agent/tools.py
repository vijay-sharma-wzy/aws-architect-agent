"""
Tool definitions exposed to Claude via LangChain tool binding.
Claude calls `render_architecture` with a structured JSON spec; this module
executes the renderer and returns the output path.
"""

import json
from langchain_core.tools import tool
from arch_agent.renderer import render


@tool
def render_architecture(spec: str) -> str:
    """
    Render an AWS architecture diagram from a JSON spec and return the file path.

    Call this tool once you have decided on the full architecture. Pass the spec
    as a JSON string with the following structure:

    {
      "nodes": [
        {"id": "<unique_id>", "service": "<ServiceName>", "label": "<display label>"}
      ],
      "edges": [
        {"from": "<node_id>", "to": "<node_id>", "label": "<optional description>"}
      ],
      "groups": [
        {"label": "<cluster name>", "members": ["<node_id>", ...]}
      ]
    }

    Supported service names:
      Compute:     Lambda, EC2, ECS, EKS, Fargate, Batch
      Database:    RDS, DynamoDB, ElastiCache, Aurora, Redshift
      Network:     APIGateway, CloudFront, Route53, VPC, ELB, ALB, NLB
      Storage:     S3, EFS, Glacier
      Messaging:   SQS, SNS, EventBridge, StepFunctions
      Security:    IAM, Cognito, WAF, KMS
      Management:  CloudWatch, CloudTrail
      Analytics:   Kinesis, Athena, Glue
      ML:          SageMaker, Rekognition

    Returns the absolute path to the rendered PNG file.
    """
    try:
        parsed = json.loads(spec)
    except json.JSONDecodeError as e:
        return f"ERROR: invalid JSON spec — {e}"

    try:
        path = render(parsed)
        return path
    except Exception as e:
        return f"ERROR: rendering failed — {e}"
