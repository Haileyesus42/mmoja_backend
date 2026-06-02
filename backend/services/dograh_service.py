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

DOGRAH_BASE_URL = "https://api.dograh.com"

class DograhService:
    def __init__(self):
        self.api_key = os.getenv("DOGRAH_API_KEY")
        self.agent_uuid = os.getenv("DOGRAH_AGENT_UUID")

        # Validate environment variables
        if not self.api_key:
            logger.warning("DOGRAH_API_KEY environment variable is not set")
        else:
            logger.debug(f"DOGRAH_API_KEY loaded, starts with: {self.api_key[:10]}...")

        if not self.agent_uuid:
            logger.warning("DOGRAH_AGENT_UUID environment variable is not set")
        else:
            logger.debug(f"DOGRAH_AGENT_UUID loaded: {self.agent_uuid}")

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
        Makes an outbound emergency call using Dograh API with dynamic variable injection.

        Args:
            phone_number: Destination phone number
            traveler: Traveler information (name, phone, email, location, etc.)
            sos_data: SOS signal details (status, type, timestamp, location, GPS)
            trip_data: Trip information (destination, date)
            contact_data: Emergency contact information (primary and secondary)
            user_id: ID of the user triggering the emergency
            contact_id: ID of the emergency contact being called

        Returns:
            Dict response from Dograh or None
        """

        # Validate required configuration
        if not all([self.api_key, self.agent_uuid]):
            logger.error("Missing Dograh configuration.")
            return {
                "status": "failed",
                "message": "Missing Dograh environment configuration"
            }

        url = f"{DOGRAH_BASE_URL}/api/v1/public/agent/test/{self.agent_uuid}"

        # Headers - use the API key as-is without adding dg_ prefix (as per working test)
        # The API key in environment variable should already include dg_ prefix if required by the API
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        # Prepare initial context with emergency data
        initial_context = {
            "traveler": traveler,
            "sos": sos_data,
            "trip": trip_data,
            "contact": contact_data
        }

        # Payload with phone number and initial context
        payload = {
            "phone_number": phone_number,
            "initial_context": initial_context
        }

        try:
            logger.info("========================================")
            logger.info("INITIATING DOGRAH EMERGENCY CALL")
            logger.info("========================================")
            logger.info(f"Destination Number: {phone_number}")
            logger.info(f"Agent UUID: {self.agent_uuid}")
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
                    logger.info(f"DOGRAH STATUS CODE: {response.status_code}")
                    logger.info(f"DOGRAH RESPONSE: {response.text}")
                    logger.info("========================================")

                    # Success
                    if response.status_code in [200, 201]:
                        result = response.json()
                        logger.info(
                            f"Emergency call initiated successfully on attempt {attempt}. "
                            f"Response: {result}"
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
                    logger.error("  - Firewall/proxy blocking api.dograh.com")
                    logger.error("  - DNS resolution problems")
                    logger.error("  - Dograh API server temporarily unavailable")
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
    dograh_service = DograhService()

except Exception as e:
    logger.exception(f"Error initializing DograhService: {e}")
    dograh_service = None


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

    if not dograh_service:
        logger.error("DograhService is not initialized")

        return {
            "status": "failed",
            "message": "DograhService not initialized"
        }

    return dograh_service.make_emergency_call(
        phone_number,
        traveler,
        sos_data,
        trip_data,
        contact_data,
        user_id,
        contact_id
    )