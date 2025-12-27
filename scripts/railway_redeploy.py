#!/usr/bin/env python3
"""
Railway Redeploy Script

Triggers a Railway service redeployment via the GraphQL API.

Usage:
    python railway_redeploy.py

Environment Variables Required:
    RAILWAY_TOKEN: Railway API token (from Railway dashboard)
    RAILWAY_PROJECT_ID: The project ID (optional, for logging)
    RAILWAY_ENV_ID or RAILWAY_ENVIRONMENT_ID: The environment ID
    RAILWAY_SERVICE_ID: The service ID
"""

import os
import sys
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

# Set up logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'railway_redeploy.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Railway GraphQL API endpoint
RAILWAY_API_URL = "https://backboard.railway.com/graphql/v2"


def service_instance_redeploy(token: str, environment_id: str, service_id: str) -> bool:
    """
    Redeploy a Railway service instance using serviceInstanceRedeploy mutation.

    Args:
        token: Railway API token
        environment_id: Railway environment ID
        service_id: Railway service ID

    Returns:
        True if redeploy was successful, False otherwise
    """
    mutation = """
    mutation serviceInstanceRedeploy($environmentId: String!, $serviceId: String!) {
        serviceInstanceRedeploy(environmentId: $environmentId, serviceId: $serviceId)
    }
    """

    variables = {
        "environmentId": environment_id,
        "serviceId": service_id
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": mutation,
        "variables": variables
    }

    try:
        logger.info(f"Triggering redeploy for service {service_id} in environment {environment_id}...")
        response = requests.post(RAILWAY_API_URL, json=payload, headers=headers, timeout=30)

        # Log response for debugging
        if response.status_code != 200:
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response body: {response.text}")

        response.raise_for_status()

        data = response.json()

        # Check for GraphQL errors
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            # Try fallback method
            return False

        # Check if redeploy was successful
        result = data.get("data", {}).get("serviceInstanceRedeploy")

        if result:
            logger.info("Service redeploy triggered successfully")
            return True
        else:
            logger.warning("Service redeploy returned false or null")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while redeploying service: {e}")
        return False


def deployment_redeploy(token: str, deployment_id: str) -> bool:
    """
    Redeploy using deploymentRedeploy mutation (fallback method).

    Args:
        token: Railway API token
        deployment_id: The deployment ID to redeploy

    Returns:
        True if redeploy was successful, False otherwise
    """
    mutation = """
    mutation deploymentRedeploy($id: String!) {
        deploymentRedeploy(id: $id) {
            status
        }
    }
    """

    variables = {
        "id": deployment_id
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": mutation,
        "variables": variables
    }

    try:
        logger.info(f"Triggering redeploy for deployment {deployment_id}...")
        response = requests.post(RAILWAY_API_URL, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response body: {response.text}")

        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return False

        result = data.get("data", {}).get("deploymentRedeploy")

        if result:
            logger.info(f"Deployment redeploy triggered successfully, status: {result.get('status', 'unknown')}")
            return True
        else:
            logger.warning("Deployment redeploy returned false or null")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while redeploying: {e}")
        return False


def get_latest_deployment_id(token: str, project_id: str, environment_id: str, service_id: str) -> str | None:
    """
    Fetch the latest deployment ID from Railway.

    Args:
        token: Railway API token
        project_id: Railway project ID
        environment_id: Railway environment ID
        service_id: Railway service ID

    Returns:
        The deployment ID string, or None if not found
    """
    query = """
    query deployments($projectId: String!, $environmentId: String!, $serviceId: String!) {
        deployments(first: 1, input: {
            projectId: $projectId
            environmentId: $environmentId
            serviceId: $serviceId
        }) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    variables = {
        "projectId": project_id,
        "environmentId": environment_id,
        "serviceId": service_id
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "variables": variables
    }

    try:
        logger.info("Fetching latest deployment ID from Railway...")
        response = requests.post(RAILWAY_API_URL, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response body: {response.text}")

        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return None

        edges = data.get("data", {}).get("deployments", {}).get("edges", [])

        if not edges:
            logger.error("No deployments found")
            return None

        deployment_id = edges[0].get("node", {}).get("id")

        if not deployment_id:
            logger.error("Deployment ID not found in response")
            return None

        logger.info(f"Found latest deployment ID: {deployment_id}")
        return deployment_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching deployment: {e}")
        return None
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing response: {e}")
        return None


def redeploy() -> bool:
    """
    Main redeploy function that orchestrates the full redeploy process.
    Tries serviceInstanceRedeploy first, then falls back to deploymentRedeploy.

    Returns:
        True if redeploy was successful, False otherwise
    """
    # Load environment variables from .env file if it exists
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

    # Get required environment variables
    token = os.getenv("RAILWAY_TOKEN")
    project_id = os.getenv("RAILWAY_PROJECT_ID")
    # Support both RAILWAY_ENV_ID and RAILWAY_ENVIRONMENT_ID
    environment_id = os.getenv("RAILWAY_ENV_ID") or os.getenv("RAILWAY_ENVIRONMENT_ID")
    service_id = os.getenv("RAILWAY_SERVICE_ID")

    # Validate required environment variables
    missing = []
    if not token:
        missing.append("RAILWAY_TOKEN")
    if not environment_id:
        missing.append("RAILWAY_ENV_ID or RAILWAY_ENVIRONMENT_ID")
    if not service_id:
        missing.append("RAILWAY_SERVICE_ID")

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False

    # Try serviceInstanceRedeploy first (simpler, doesn't need deployment ID)
    logger.info("Attempting serviceInstanceRedeploy...")
    success = service_instance_redeploy(token, environment_id, service_id)

    if success:
        logger.info("Railway redeploy completed successfully")
        return True

    # Fallback to deploymentRedeploy if serviceInstanceRedeploy fails
    logger.info("serviceInstanceRedeploy failed, trying deploymentRedeploy fallback...")

    if not project_id:
        logger.error("RAILWAY_PROJECT_ID required for fallback method")
        return False

    deployment_id = get_latest_deployment_id(token, project_id, environment_id, service_id)

    if not deployment_id:
        logger.error("Failed to get latest deployment ID")
        return False

    success = deployment_redeploy(token, deployment_id)

    if success:
        logger.info("Railway redeploy completed successfully (via fallback)")
    else:
        logger.error("Railway redeploy failed")

    return success


def main():
    """Main entry point for the script."""
    logger.info("=" * 50)
    logger.info("Starting Railway redeploy process")
    logger.info("=" * 50)

    success = redeploy()

    logger.info("=" * 50)
    logger.info(f"Redeploy {'succeeded' if success else 'failed'}")
    logger.info("=" * 50)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
