import os
import requests
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VAPI_BASE_URL = "https://api.vapi.ai"


class VapiService:
    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY")
        self.assistant_id = os.getenv("VAPI_ASSISTANT_ID")
        self.phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")

        # Validate environment variables
        if not self.api_key:
            logger.warning("VAPI_API_KEY environment variable is not set")

        if not self.assistant_id:
            logger.warning("VAPI_ASSISTANT_ID environment variable is not set")

        if not self.phone_number_id:
            logger.warning("VAPI_PHONE_NUMBER_ID environment variable is not set")

    def make_emergency_call(
        self,
        phone_number: str,
        traveler: Dict[str, Any],
        sos_data: Dict[str, Any],
        trip_data: Dict[str, Any],
        contact_data: Dict[str, Any],
        user_id: Optional[int] = None,
        contact_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Makes an outbound emergency call using Vapi API with dynamic variable injection.

        Args:
            phone_number: Destination phone number
            traveler: Traveler information (name, phone, email, location, etc.)
            sos_data: SOS signal details (status, type, timestamp, location, GPS)
            trip_data: Trip information (destination, date)
            contact_data: Emergency contact information (primary and secondary)
            user_id: ID of the user triggering the emergency
            contact_id: ID of the emergency contact being called

        Returns:
            Dict response from Vapi or None
        """

        # Validate required configuration
        if not all([
            self.api_key,
            self.assistant_id,
            self.phone_number_id
        ]):
            logger.error("Missing Vapi configuration.")
            return {
                "status": "failed",
                "message": "Missing Vapi environment configuration"
            }

        # Vapi endpoint for initiating calls
        url = f"{VAPI_BASE_URL}/call"

        # Headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Prepare metadata with user and contact IDs for webhook handling
        metadata = {
            "user_id": user_id,
            "contact_id": contact_id,
            "contact_phone": phone_number
        }

        # Payload with dynamic variable injection via assistantOverrides
        payload = {
            "assistantId": self.assistant_id,
            "phoneNumberId": self.phone_number_id,
            "customer": {
                "number": phone_number
            },
            "metadata": metadata,
            "assistantOverrides": {
                "variableValues": {
                    "traveler": traveler,
                    "sos": sos_data,
                    "trip": trip_data,
                    "contact": contact_data
                }
            }
        }

        try:
            logger.info("========================================")
            logger.info("INITIATING VAPI EMERGENCY CALL")
            logger.info("========================================")
            logger.info(f"Destination Number: {phone_number}")
            logger.info(f"Assistant ID: {self.assistant_id}")
            logger.info(f"Phone Number ID: {self.phone_number_id}")
            logger.info(f"Traveler: {traveler}")
            logger.info(f"SOS Data: {sos_data}")
            logger.info(f"Trip Data: {trip_data}")
            logger.info(f"Contact Data: {contact_data}")
            logger.info(f"Payload: {payload}")

            # Retry logic - try up to 3 times with increasing timeouts
            max_retries = 3
            last_error = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Attempt {attempt}/{max_retries}...")
                    
                    # Increase timeout with each retry (30s, 45s, 60s)
                    timeout = 30 + (attempt - 1) * 15
                    
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=timeout
                    )

                    logger.info("========================================")
                    logger.info(f"VAPI STATUS CODE: {response.status_code}")
                    logger.info(f"VAPI RESPONSE: {response.text}")
                    logger.info("========================================")

                    # Success
                    if response.status_code in [200, 201]:
                        result = response.json()
                        logger.info(
                            f"Emergency call initiated successfully on attempt {attempt}. "
                            f"Call ID: {result.get('id', 'unknown')}"
                        )
                        return result
                    else:
                        logger.error(
                            f"Failed to initiate emergency call. "
                            f"Status: {response.status_code}, Response: {response.text}"
                        )
                        return None
                        
                except requests.exceptions.Timeout as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt} timed out after {timeout}s: {str(e)}")
                    if attempt < max_retries:
                        logger.info(f"Retrying in 2 seconds...")
                        import time
                        time.sleep(2)  # Wait before retry
                    continue
                    
                except requests.exceptions.ConnectionError as e:
                    last_error = e
                    logger.error(f"Connection error on attempt {attempt}: {str(e)}")
                    logger.error("This could be due to:")
                    logger.error("  - Network connectivity issues")
                    logger.error("  - Firewall/proxy blocking api.vapi.ai")
                    logger.error("  - DNS resolution problems")
                    logger.error("  - Vapi API server temporarily unavailable")
                    return None
                    
                except requests.exceptions.RequestException as e:
                    last_error = e
                    logger.error(f"Request error on attempt {attempt}: {str(e)}")
                    return None
            
            # All retries failed
            logger.error(f"All {max_retries} attempts failed. Last error: {str(last_error)}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error making emergency call: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


# Global singleton instance
try:
    vapi_service = VapiService()

except Exception as e:
    logger.exception(f"Error initializing VapiService: {e}")
    vapi_service = None


def make_emergency_call(
    phone_number: str,
    traveler: Dict[str, Any],
    sos_data: Dict[str, Any],
    trip_data: Dict[str, Any],
    contact_data: Dict[str, Any],
    user_id: Optional[int] = None,
    contact_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Wrapper function for emergency calling with dynamic variables
    """

    if not vapi_service:
        logger.error("VapiService is not initialized")

        return {
            "status": "failed",
            "message": "VapiService not initialized"
        }

    return vapi_service.make_emergency_call(
        phone_number,
        traveler,
        sos_data,
        trip_data,
        contact_data,
        user_id,
        contact_id
    )
