class Constants {
  // Backend configuration
  static String backendHost = '192.168.8.50'; // Update this when IP changes
  static int backendPort = 8000;
  static String backendBaseUrl = 'http://$backendHost:$backendPort/api/v1';
  
  // Common timeout values
  static const Duration connectTimeout = Duration(seconds: 100);
  static const Duration receiveTimeout = Duration(seconds: 300);
  static const Duration sendTimeout = Duration(seconds: 300);
}