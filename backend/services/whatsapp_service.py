import os
from dotenv import load_dotenv

# Load environment variables from project root .env file
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️  Twilio library not installed. Run: pip install twilio")


class WhatsAppService:
    def __init__(self):
        # Twilio credentials from environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.messaging_service_sid = os.getenv('TWILIO_MESSAGING_SERVICE_SID', '+14155238886')  # Default to sandbox
        
        # Check if we have real credentials
        self.has_real_credentials = (
            self.account_sid and 
            self.auth_token and 
            self.account_sid != 'your_account_sid_here' and
            self.auth_token != 'your_auth_token_here'
        )
        
        # Initialize Twilio client if credentials are available and Twilio is installed
        if TWILIO_AVAILABLE and self.has_real_credentials:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print("✅ Twilio WhatsApp service initialized with REAL credentials")
                print(f"   Account SID: {self.account_sid[:8]}...")
                print(f"   Messaging Service: {self.messaging_service_sid}")
            except Exception as e:
                print(f"❌ Failed to initialize Twilio client: {e}")
                self.client = None
        else:
            self.client = None
            if not self.has_real_credentials:
                print("⚠️  Running in SIMULATION MODE - Configure real Twilio credentials in .env file")
                print("   To enable real WhatsApp messages:")
                print("   1. Sign up at https://www.twilio.com/")
                print("   2. Get your Account SID and Auth Token from Console")
                print("   3. Update backend/.env file with your credentials")
                print("   4. Recipient must join your WhatsApp sandbox first")
    
    def send_whatsapp_message(self, to_number: str, message_body: str) -> dict:
        """
        Send a WhatsApp message to the specified number
        
        Args:
            to_number: Recipient's phone number (with country code, e.g., +251949867668)
            message_body: The message content
            
        Returns:
            dict with status and message SID
        """
        try:
            # Format the recipient number for WhatsApp (add 'whatsapp:' prefix)
            whatsapp_to = f"whatsapp:{to_number}"
            
            if self.client and self.has_real_credentials:
                # Send REAL WhatsApp message via Twilio
                print(f"\n📱 SENDING REAL WHATSAPP MESSAGE VIA TWILIO")
                print(f"=" * 60)
                
                message = self.client.messages.create(
                    body=message_body,
                    from_=f"whatsapp:{self.messaging_service_sid}",
                    to=whatsapp_to
                )
                
                print(f"✅ WhatsApp message SENT SUCCESSFULLY!")
                print(f"   To: {to_number}")
                print(f"   Message SID: {message.sid}")
                print(f"   Status: {message.status}")
                print(f"=" * 60)
                
                return {
                    'success': True,
                    'message_sid': message.sid,
                    'status': message.status,
                    'real_message': True
                }
            else:
                # Simulation mode - just log the message
                print(f"\n📱 WHATSAPP MESSAGE (SIMULATION MODE)")
                print(f"=" * 60)
                print(f"To: {to_number}")
                print(f"Message:\n{message_body}")
                print(f"=" * 60)
                print(f"\n⚠️  This is a SIMULATED message.")
                print(f"   To send REAL messages, configure Twilio credentials in backend/.env")
                
                return {
                    'success': True,
                    'message_sid': 'SIMULATED_' + str(hash(message_body))[:10],
                    'status': 'simulated',
                    'real_message': False
                }
                
        except Exception as e:
            print(f"❌ Failed to send WhatsApp message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_emergency_whatsapp(self, contact_name: str, relationship: str, 
                                phone: str, traveler_name: str, 
                                location: str, gps: str, 
                                hotel: str, signal_type: str = "SOS_BUTTON") -> dict:
        """
        Send an emergency notification via WhatsApp
        
        Args:
            contact_name: Name of the emergency contact
            relationship: Relationship to traveler
            phone: Contact's phone number
            traveler_name: Name of the traveler in emergency
            location: Current location of traveler
            gps: GPS coordinates
            hotel: Hotel/accommodation name
            signal_type: Type of emergency signal
            
        Returns:
            dict with success status and message details
        """
        # Build emergency message
        message = f"""🚨 EMERGENCY ALERT 🚨

Dear {contact_name} ({relationship}),

This is an automated emergency notification from Umojee Emergency System.

   TRAVELER: {traveler_name}
   LOCATION: {location}
   GPS: {gps}
   HOTEL: {hotel}

⚠️ An emergency SOS signal was triggered but we couldn't reach you by phone.

Please contact {traveler_name} immediately or reach out to local emergency services.

If you receive this message, please respond to confirm you've been notified.

- Umojee Emergency System"""

        print(f"\n📱 SENDING EMERGENCY WHATSAPP TO: {contact_name}")
        print(f"   Phone: {phone}")
        print(f"   Relationship: {relationship}")
        
        return self.send_whatsapp_message(phone, message)


# Convenience function for easy import
def send_emergency_whatsapp(contact_name: str, relationship: str, 
                           phone: str, traveler_name: str, 
                           location: str, gps: str, 
                           hotel: str, signal_type: str = "SOS_BUTTON") -> dict:
    """
    Send an emergency WhatsApp notification
    
    Args:
        Same as WhatsAppService.send_emergency_whatsapp
        
    Returns:
        dict with success status
    """
    service = WhatsAppService()
    return service.send_emergency_whatsapp(
        contact_name=contact_name,
        relationship=relationship,
        phone=phone,
        traveler_name=traveler_name,
        location=location,
        gps=gps,
        hotel=hotel,
        signal_type=signal_type
    )
