"""
Renders an AWS architecture diagram from a structured JSON spec using the
`diagrams` library (mingrammer). Requires Graphviz installed on the system.

Spec format:
{
  "nodes": [
    {"id": "apigw", "service": "APIGateway", "label": "API Gateway"}
  ],
  "edges": [
    {"from": "apigw", "to": "lambda1"}
  ],
  "groups": [
    {"label": "VPC", "members": ["rds", "ec2"]}
  ]
}
"""

import os
import uuid
from diagrams import Diagram, Cluster, Edge
from diagrams.aws import (
    compute, database, network, storage, integration,
    security, management, analytics, ml
)

# Map service name strings → diagrams classes
SERVICE_MAP = {
    # Compute
    "Lambda":           compute.Lambda,
    "EC2":              compute.EC2,
    "ECS":              compute.ECS,
    "EKS":              compute.EKS,
    "Fargate":          compute.Fargate,
    "Batch":            compute.Batch,
    # Database
    "RDS":              database.RDS,
    "DynamoDB":         database.Dynamodb,
    "ElastiCache":      database.Elasticache,
    "Aurora":           database.Aurora,
    "Redshift":         database.Redshift,
    # Network
    "APIGateway":       network.APIGateway,
    "CloudFront":       network.CloudFront,
    "Route53":          network.Route53,
    "VPC":              network.VPC,
    "ELB":              network.ELB,
    "ALB":              network.ELB,
    "NLB":              network.ELB,
    # Storage
    "S3":               storage.S3,
    "EFS":              storage.EFS,
    "Glacier":          storage.S3Glacier,
    # Integration / Messaging
    "SQS":              integration.SQS,
    "SNS":              integration.SNS,
    "EventBridge":      integration.Eventbridge,
    "StepFunctions":    integration.StepFunctions,
    # Security
    "IAM":              security.IAM,
    "Cognito":          security.Cognito,
    "WAF":              security.WAF,
    "KMS":              security.KMS,
    # Management
    "CloudWatch":       management.Cloudwatch,
    "CloudTrail":       management.Cloudtrail,
    # Analytics
    "Kinesis":          analytics.KinesisDataStreams,
    "Athena":           analytics.Athena,
    "Glue":             analytics.Glue,
    # ML
    "SageMaker":        ml.Sagemaker,
    "Rekognition":      ml.Rekognition,
}


def _resolve_service(service_name: str):
    """Return a diagrams class for the given service name string."""
    cls = SERVICE_MAP.get(service_name)
    if cls is None:
        # Fall back to a generic compute node rather than crashing
        cls = compute.EC2
    return cls


def render(spec: dict, output_dir: str | None = None) -> str:
    """
    Render the architecture spec to a PNG and return its absolute file path.

    Args:
        spec: dict with keys `nodes`, `edges`, `groups`
        output_dir: directory to write PNG into. Defaults to system temp dir.

    Returns:
        Absolute path to the output PNG file.
    """
    nodes_spec = spec.get("nodes", [])
    edges_spec = spec.get("edges", [])
    groups_spec = spec.get("groups", [])

    default_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
    out_dir = output_dir or default_out
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(out_dir, f"arch_{uuid.uuid4().hex[:8]}")

    # Build a lookup: node_id → group label (if any)
    node_to_group: dict[str, str] = {}
    for group in groups_spec:
        for member_id in group.get("members", []):
            node_to_group[member_id] = group["label"]

    graph_attr = {
        "rankdir": "TB",        # top-to-bottom flow instead of left-to-right
        "splines": "ortho",     # right-angle edges — eliminates diagonal criss-crossing
        "nodesep": "0.8",       # horizontal spacing between nodes in the same rank
        "ranksep": "1.2",       # vertical spacing between ranks
        "pad": "0.5",           # padding around the whole diagram
        "concentrate": "true",  # merge parallel edges going the same direction
    }

    with Diagram("AWS Architecture", filename=filename, show=False, outformat="png", graph_attr=graph_attr):
        # Track instantiated diagram nodes by id
        node_instances: dict[str, object] = {}

        # Group nodes that belong to a Cluster
        group_labels = {g["label"] for g in groups_spec}
        grouped_node_ids = set(node_to_group.keys())

        # Render ungrouped nodes first
        for n in nodes_spec:
            if n["id"] not in grouped_node_ids:
                cls = _resolve_service(n["service"])
                node_instances[n["id"]] = cls(n.get("label", n["id"]))

        # Render grouped nodes inside Clusters
        for group in groups_spec:
            with Cluster(group["label"]):
                for member_id in group.get("members", []):
                    node_spec = next(
                        (n for n in nodes_spec if n["id"] == member_id), None
                    )
                    if node_spec:
                        cls = _resolve_service(node_spec["service"])
                        node_instances[member_id] = cls(
                            node_spec.get("label", member_id)
                        )

        # Draw edges
        for e in edges_spec:
            src = node_instances.get(e["from"])
            dst = node_instances.get(e["to"])
            if src and dst:
                src >> Edge(label=e.get("label", "")) >> dst

    return f"{filename}.png"
