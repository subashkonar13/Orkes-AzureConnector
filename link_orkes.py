import json
from conductor.client.http.models import StartWorkflowRequest
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import (
    AuthenticationSettings
)
from conductor.client.workflow.executor.workflow_executor import (
    WorkflowExecutor
)
import logging
import os
import platform
from pathlib import Path
import subprocess

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_workflow_executor(base_url: str, key_id: str,
                          key_secret: str) -> WorkflowExecutor:
    """Create and return a workflow executor with authentication."""
    try:
        logging.info(f"Creating workflow executor for {base_url}")
        conf = Configuration(
            base_url=base_url,
            authentication_settings=AuthenticationSettings(
                key_id=key_id,
                key_secret=key_secret
            ),
            debug=True
        )
        executor = WorkflowExecutor(conf)
        logging.info("Workflow executor created successfully")
        return executor
    except Exception as e:
        logging.error(f"Failed to create workflow executor: {str(e)}")
        raise


def start_workflow(executor: WorkflowExecutor, workflow_name: str,
                   workflow_version: int, input_data: dict) -> str:
    """Start a workflow with the given input data."""
    try:
        logging.info(
            f"Starting workflow: {workflow_name} (version {workflow_version})")
        request = StartWorkflowRequest()
        request.name = workflow_name
        request.version = workflow_version
        request.input = input_data

        workflow_id = executor.start_workflow(request)
        logging.info(f"Successfully started workflow with ID: {workflow_id}")
        return workflow_id
    except Exception as e:
        logging.error(f"Failed to start workflow: {str(e)}")
        raise


def load_local_settings():
    """Load settings from local.settings.json"""
    try:
        with open('local.settings.json') as f:
            settings = json.load(f)
            return settings.get('Values', {})
    except FileNotFoundError:
        logging.error("local.settings.json not found")
        raise
    except json.JSONDecodeError:
        logging.error("Invalid JSON in local.settings.json")
        raise


# For local testing
def main():
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        logging.info("Starting local test")

        # Load settings from local.settings.json
        settings = load_local_settings()

        # Get configuration from settings
        base_url = settings.get('ORKES_BASE_URL')
        key_id = settings.get('ORKES_KEY_ID')
        key_secret = settings.get('ORKES_KEY_SECRET')
        workflow_name = settings.get('WORKFLOW_NAME')
        workflow_version = int(settings.get('WORKFLOW_VERSION', '1'))

        if not all([base_url, key_id, key_secret, workflow_name]):
            raise ValueError(
                "Missing required settings in local.settings.json")

        # Create workflow executor
        executor = get_workflow_executor(
            base_url=base_url,
            key_id=key_id,
            key_secret=key_secret
        )

        # Test data with your specific parameters
        test_input = {
            "blobName": "test.txt",
            "blobSize": 100,
            "blobContent": "This is a test content for local testing"
        }
        
        # Start workflow
        workflow_id = start_workflow(
            executor=executor,
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            input_data=test_input
        )

        logging.info(
            f"Test completed successfully. Workflow ID: {workflow_id}")

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        raise


def setup_certificates():
    """Setup SSL certificates based on the operating system."""
    try:
        system = platform.system().lower()
        home = str(Path.home())

        if system == 'darwin':  # macOS
            ca_roots_path = os.path.join(home, '.mac-ca-roots')
            bashrc_path = os.path.join(home, '.bashrc')
            logging.info("Setting up certificates for macOS")

            try:
                result = subprocess.run(
                    ['security', 'find-certificate', '-a', '-p', 'ls',
                     '/System/Library/Keychains/SystemRootCertificates.keychain'],
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Get certificates from System.keychain
                result2 = subprocess.run(
                    ['security', 'find-certificate', '-a', '-p', 'ls',
                     '/Library/Keychains/System.keychain'],
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Combine the outputs
                combined_output = result.stdout + result2.stdout

                # Write certificates to file
                with open(ca_roots_path, 'w') as f:
                    f.write(combined_output)

                # Update .bashrc
                export_line = f'\nexport REQUESTS_CA_BUNDLE="{ca_roots_path}"'

                # Check if .bashrc exists
                if not os.path.exists(bashrc_path):
                    with open(bashrc_path, 'w') as f:
                        f.write(export_line)
                else:
                    # Read existing content
                    with open(bashrc_path, 'r') as f:
                        content = f.read()

                    # Add export line if it doesn't exist
                    if f'REQUESTS_CA_BUNDLE="{ca_roots_path}"' not in content:
                        with open(bashrc_path, 'a') as f:
                            f.write(export_line)

                # Source .bashrc in current environment
                os.environ['REQUESTS_CA_BUNDLE'] = ca_roots_path

                # Source .bashrc using shell

                # subprocess.run(
                #     f'source {bashrc_path}',
                #     shell=True,
                #     executable='/bin/bash'
                # )

                logging.info(
                    f"Successfully set up certificates at {ca_roots_path}")
                logging.info(f"Updated {bashrc_path} with REQUESTS_CA_BUNDLE")

            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to execute security command: {str(e)}")
                raise

        elif system == 'linux':
            logging.info("Setting up certificates for Linux")
            # Common locations for CA certificates on Linux
            ca_paths = [
                '/etc/ssl/certs/ca-certificates.crt',  # Debian/Ubuntu
                '/etc/pki/tls/certs/ca-bundle.crt',    # RHEL/CentOS
                '/etc/ssl/ca-bundle.pem',              # OpenSUSE
                '/etc/pki/tls/cacert.pem',             # OpenELEC
            ]

            for ca_path in ca_paths:
                if os.path.exists(ca_path):
                    os.environ['REQUESTS_CA_BUNDLE'] = ca_path
                    logging.info(f"Using certificate bundle at {ca_path}")
                    break
            else:
                logging.warning("No system CA certificate bundle found")

        else:
            logging.warning(f"Certificate setup not implemented for {system}")

    except Exception as e:
        logging.error(f"Failed to setup certificates: {str(e)}")
        raise


# For testing purpose
if __name__ == '__main__':
    setup_certificates()
    main()
