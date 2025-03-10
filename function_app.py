import azure.functions as func
import logging
import os
from link_orkes import get_workflow_executor, start_workflow

app = func.FunctionApp()


@app.blob_trigger(
    arg_name="myblob",
    path="orkesblob/{demo}",  
    connection="AZUREBLOB_STORAGE"
)
def orkes_blob_trigger(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob\n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")
    
    # Get Orkes configuration from environment variables
    ORKES_BASE_URL = os.environ["ORKES_BASE_URL"] #Provide the base url of Orkes cloud
    ORKES_KEY_ID = os.environ["ORKES_KEY_ID"]
    ORKES_KEY_SECRET = os.environ["ORKES_KEY_SECRET"]
    WORKFLOW_NAME = os.environ["WORKFLOW_NAME"]
    WORKFLOW_VERSION = int(os.environ.get("WORKFLOW_VERSION", "1"))
    
    try:
        # Get workflow executor
        executor = get_workflow_executor(
            base_url=ORKES_BASE_URL,
            key_id=ORKES_KEY_ID,
            key_secret=ORKES_KEY_SECRET
        )
        
        # Prepare workflow input
        workflow_input = {
            "blobName": myblob.name,
            "blobSize": myblob.length,
            "blobContent": myblob.read().decode('utf-8')  # If blob contains text
        }
        
        # Start the workflow
        workflow_id = start_workflow(
            executor=executor,
            workflow_name=WORKFLOW_NAME,
            workflow_version=WORKFLOW_VERSION,
            input_data=workflow_input
        )
        
        logging.info(f"Successfully started Orkes workflow with ID: {workflow_id}")
        
    except Exception as e:
        logging.error(f"Failed to start Orkes workflow: {str(e)}")
        raise
