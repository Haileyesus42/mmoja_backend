class ApiConfig {
  // Base URL configuration
  static const String baseUrl = 'http://localhost:8000/api/v1';
  
  // Timeout configurations (in seconds)
  static const int connectTimeout = 10;
  static const int receiveTimeout = 15;
  static const int sendTimeout = 15;
}