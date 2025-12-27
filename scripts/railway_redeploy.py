#!/usr/bin/env python3
"""
Railway Redeploy Script

Triggers a Railway service redeployment via the GraphQL API.
This script fetches the latest deployment ID and restarts it.

Usage:
    python railway_redeploy.py

Environment Variables Required:
    RAILWAY_TOKEN: Railway API token (from Railway dashboard)
    RAILWAY_PROJECT_ID: The project ID
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
    query deployments($projectId: ID!, $environmentId: ID!, $serviceId: ID!) {
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
        response.raise_for_status()
        
        data = response.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return None
        
        # Extract deployment ID
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


def restart_deployment(token: str, deployment_id: str) -> bool:
    """
    Restart a Railway deployment.
    
    Args:
        token: Railway API token
        deployment_id: The deployment ID to restart
        
    Returns:
        True if restart was successful, False otherwise
    """
    mutation = """
    mutation deploymentRestart($id: ID!) {
        deploymentRestart(id: $id)
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
        logger.info(f"Triggering restart for deployment {deployment_id}...")
        response = requests.post(RAILWAY_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return False
        
        # Check if restart was successful
        result = data.get("data", {}).get("deploymentRestart")
        
        if result:
            logger.info("Deployment restart triggered successfully")
            return True
        else:
            logger.warning("Deployment restart returned false or null")
            return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while restarting deployment: {e}")
        return False


def redeploy() -> bool:
    """
    Main redeploy function that orchestrates the full redeploy process.
    
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
    if not project_id:
        missing.append("RAILWAY_PROJECT_ID")
    if not environment_id:
        missing.append("RAILWAY_ENV_ID or RAILWAY_ENVIRONMENT_ID")
    if not service_id:
        missing.append("RAILWAY_SERVICE_ID")
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    
    # Get latest deployment ID
    deployment_id = get_latest_deployment_id(token, project_id, environment_id, service_id)
    
    if not deployment_id:
        logger.error("Failed to get latest deployment ID")
        return False
    
    # Restart the deployment
    success = restart_deployment(token, deployment_id)
    
    if success:
        logger.info("Railway redeploy completed successfully")
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