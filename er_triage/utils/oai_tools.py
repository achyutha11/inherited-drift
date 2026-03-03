"""OpenAI tool definitions for ER simulation."""

put_patient_tool = {
    "type": "function",
    "function": {
        "name": "put_patient",
        "description": "Place a patient at a specific position in the queue. Position 0 is the front of the queue (will be seen first).",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "integer",
                    "description": "The ID of the patient to place in the queue"
                },
                "position": {
                    "type": "integer",
                    "description": "The position in the queue (0 = front, will be seen first)"
                }
            },
            "required": ["patient_id", "position"]
        }
    }
}

finish_timestep_tool = {
    "type": "function",
    "function": {
        "name": "finish_timestep",
        "description": "Complete the current timestep. Any patients not explicitly placed will be added to the end of the queue.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}

view_queue_tool = {
    "type": "function",
    "function": {
        "name": "view_queue",
        "description": "View the current queue with detailed patient information.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}