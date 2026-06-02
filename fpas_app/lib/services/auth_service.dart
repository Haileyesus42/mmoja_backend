import 'package:fpas_app/services/api_service.dart';
import '../models/contact_model.dart';
import 'dart:typed_data';

class AuthService {
  final ApiService _apiService = ApiService();

  // Track current user session
  String? _currentUser;

  Future<bool> login(String username, String password) async {
    try {
      // First, try to authenticate with the backend API to get JWT token
      final result = await _apiService.login(username, password);

      if (result['success'] == true) {
        // Authentication successful with backend, store user session
        _currentUser = username;
        return true;
      } else {
        return false;
      }
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }

  Future<bool> logout() async {
    try {
      // Logout from backend API if possible
      try {
        await _apiService.logout();
      } catch (e) {
        print('Backend logout failed: $e');
      }

      // Clear user session
      _currentUser = null;
      return true;
    } catch (e) {
      print('Logout error: $e');
      return false;
    }
  }

  Future<String?> getCurrentUser() async {
    // Return the user stored in memory
    return _currentUser;
  }

  Future<bool> isLoggedIn() async {
    // Check if there's a user in memory
    return _currentUser != null;
  }

  Future<bool> register(String username, String email, String password) async {
    try {
      // Register user with backend API only
      final result = await _apiService.register(username, email, password);
      
      if (result['success'] == true) {
        return true;
      } else {
        throw Exception(result['error'] ?? 'Registration failed');
      }
    } catch (e) {
      print('Registration error: $e');
      rethrow;
    }
  }

  // Enhanced registration method that creates user and sets up profile
  Future<bool> registerWithProfile({
    required String username,
    required String password,
    required Map<String, dynamic> profileData,
    required List<ContactModel> contacts,
  }) async {
    try {
      // Register user with backend API
      final result = await _apiService.registerWithProfile(
        username: username,
        password: password,
        profileData: profileData,
        contacts: contacts,
      );
      
      if (result['success'] == true) {
        return true;
      } else {
        throw Exception(result['error'] ?? 'Registration with profile failed');
      }
    } catch (e) {
      print('Registration with profile error: $e');
      rethrow;
    }
  }

  // Update user profile with basic data
  Future<bool> updateProfile({
    required String username,
    String? fullName,
    String? email,
    String? phone,
    String? address,
    String? currentCity,
    String? currentCountry,
    String? hotelName,
  }) async {
    try {
      final result = await _apiService.updateUserProfile(
        username: username,
        fullName: fullName,
        email: email,
        phone: phone,
        address: address,
        currentCity: currentCity,
        currentCountry: currentCountry,
        hotelName: hotelName,
      );
      
      return result['success'] == true;
    } catch (e) {
      print('Profile update error: $e');
      return false;
    }
  }

  // Method to set the current user directly (useful after biometric authentication)
  Future<void> setCurrentUser(String username) async {
    _currentUser = username;
  }

  // Method to check if user has face enrollment
  Future<bool> hasFaceEnrollment(String? username) async {
    if (username == null) {
      return false;
    }
    
    try {
      return await _apiService.hasFaceEnrollment(username);
    } catch (e) {
      print('Error checking face enrollment: $e');
      return false;
    }
  }

  // Method to login with face recognition
  Future<bool> loginWithFace(Uint8List imageBytes) async {
    try {
      // Try to authenticate with the backend API using face recognition
      final result = await _apiService.loginWithFace(imageBytes: imageBytes);

      if (result['success'] == true) {
        // Authentication successful with backend, store user session
        final userData = result['data']['user'];
        _currentUser = userData['username'];
        return true;
      } else {
        return false;
      }
    } catch (e) {
      print('Face login error: $e');
      return false;
    }
  }

  // Method to login with palm recognition
  Future<bool> loginWithPalm(String imageBase64) async {
    try {
      // Try to authenticate with the backend API using palm recognition
      final result = await _apiService.loginWithPalm(imageBase64: imageBase64);

      if (result['success'] == true) {
        // Authentication successful with backend, store user session
        final userData = result['data']['user'];
        _currentUser = userData['username'];
        return true;
      } else {
        return false;
      }
    } catch (e) {
      print('Palm login error: $e');
      return false;
    }
  }
}