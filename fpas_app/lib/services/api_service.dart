import 'dart:io';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:image_picker/image_picker.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../utils/constants.dart';
import '../models/contact_model.dart';
import '../models/user_model.dart';

class ApiService {
  static String get baseUrl {
    if (kIsWeb) {
      // When running on web, the server is on localhost (the machine hosting the web app)
      return 'http://localhost:${Constants.backendPort}/api/v1';
    } else {
      // Use the configured backend IP for physical devices
      return Constants.backendBaseUrl;
    }
  }

  final Dio _dio = Dio();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiService() {
    _dio.options.connectTimeout = Constants.connectTimeout;
    _dio.options.receiveTimeout = Constants.receiveTimeout;
    _dio.options.sendTimeout = Constants.sendTimeout;

    _dio.interceptors.add(
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        requestHeader: true,
        responseHeader: true,
      ),
    );
  }

  // Get auth token with error handling for missing plugins
  Future<String?> getToken() async {
    try {
      return await _storage.read(key: 'auth_token');
    } catch (e) {
      print('Error reading token: $e');
      // Return null if secure storage is not available
      return null;
    }
  }

  // Save token with error handling for missing plugins
  Future<void> saveToken(String token) async {
    try {
      await _storage.write(key: 'auth_token', value: token);
    } catch (e) {
      print('Error saving token: $e');
      // Silently fail if secure storage is not available
    }
  }

  // Remove token with error handling for missing plugins
  Future<void> removeToken() async {
    try {
      await _storage.delete(key: 'auth_token');
    } catch (e) {
      print('Error removing token: $e');
      // Silently fail if secure storage is not available
    }
  }

  // Check if logged in
  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  /// Pick an image from gallery (web) or return existing file bytes (mobile).
  Future<Uint8List?> _pickImageBytes(String? imagePath) async {
    if (kIsWeb) {
      final picker = ImagePicker();
      final XFile? image = await picker.pickImage(source: ImageSource.gallery);
      if (image == null) return null;
      return await image.readAsBytes();
    } else {
      if (imagePath == null) return null;
      final file = File(imagePath);
      return await file.readAsBytes();
    }
  }

  Future<Map<String, dynamic>> enrollFace({
    required String userId,
    required String name,
    String? imagePath, // used on mobile; ignored on web
    Uint8List? imageBytes, // Direct image bytes for mobile
  }) async {
    try {
      Uint8List? finalImageBytes;

      if (kIsWeb) {
        finalImageBytes = await _pickImageBytes(imagePath);
      } else {
        // On mobile, prioritize imageBytes if provided, otherwise use imagePath
        if (imageBytes != null) {
          finalImageBytes = imageBytes;
        } else if (imagePath != null) {
          final file = File(imagePath);
          finalImageBytes = await file.readAsBytes();
        } else {
          return {'success': false, 'message': 'Image data required on mobile - either imageBytes or imagePath must be provided'};
        }
      }

      if (finalImageBytes == null) {
        return {'success': false, 'message': 'No image selected'};
      }

      final String fileName = kIsWeb
          ? 'face_image.jpg'
          : (imagePath != null ? imagePath.split('/').last : 'face_image.jpg');
      final FormData formData = FormData.fromMap({
        'user_id': userId,
        'name': name,
        'file': MultipartFile.fromBytes(
          finalImageBytes,
          filename: fileName,
          contentType: MediaType('image', 'jpeg'),
        ),
      });

      print('Attempting to connect to: $baseUrl/face-recognition/enroll');

      final response = await _dio.post(
        '$baseUrl/face-recognition/enroll',
        data: formData,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return {'success': true, 'data': response.data};
      } else {
        return {
          'success': false,
          'message':
              'Server error (${response.statusCode}): ${response.statusMessage}',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Enrollment error: $errorMsg');
      return {'success': false, 'message': errorMsg};
    } catch (e) {
      print('Unexpected enrollment error: $e');
      return {'success': false, 'message': 'Unexpected error: $e'};
    }
  }

  Future<Map<String, dynamic>> verifyFace({
    String? imagePath, // used on mobile; ignored on web
    Uint8List? imageBytes, // Direct image bytes for mobile
  }) async {
    try {
      Uint8List? finalImageBytes;

      if (kIsWeb) {
        finalImageBytes = await _pickImageBytes(imagePath);
      } else {
        // On mobile, prioritize imageBytes if provided, otherwise use imagePath
        if (imageBytes != null) {
          finalImageBytes = imageBytes;
        } else if (imagePath != null) {
          final file = File(imagePath);
          finalImageBytes = await file.readAsBytes();
        } else {
          return {'success': false, 'message': 'Image data required on mobile - either imageBytes or imagePath must be provided'};
        }
      }

      if (finalImageBytes == null) {
        return {'success': false, 'message': 'No image selected'};
      }

      final String fileName = kIsWeb
          ? 'face_image.jpg'
          : (imagePath != null ? imagePath.split('/').last : 'face_image.jpg');
      final FormData formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(
          finalImageBytes,
          filename: fileName,
          contentType: MediaType('image', 'jpeg'),
        ),
      });

      print('Attempting to connect to: $baseUrl/face-recognition/verify');

      final response = await _dio.post(
        '$baseUrl/face-recognition/verify',
        data: formData,
      );

      if (response.statusCode == 200) {
        return {'is_match': true, 'data': response.data, 'confidence': response.data['confidence'] ?? 0.0};
      } else if (response.statusCode == 404) {
        return {'is_match': false, 'message': 'No matching face found', 'confidence': 0.0};
      } else {
        return {
          'is_match': false,
          'message': 'Server error (${response.statusCode}): ${response.statusMessage}',
          'confidence': 0.0
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Verification error: $errorMsg');
      return {'is_match': false, 'message': errorMsg, 'confidence': 0.0};
    } catch (e) {
      print('Unexpected verification error: $e');
      return {'is_match': false, 'message': 'Unexpected error: $e', 'confidence': 0.0};
    }
  }

  // New methods to handle Uint8List directly (for camera images)
  Future<Map<String, dynamic>> enrollFaceWithBytes({
    required String userId,
    required String name,
    required Uint8List imageBytes,
  }) async {
    try {
      final FormData formData = FormData.fromMap({
        'user_id': userId,
        'name': name,
        'file': MultipartFile.fromBytes(
          imageBytes,
          filename: 'face_image.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
      });

      print('Attempting to connect to: $baseUrl/face-recognition/enroll');

      final response = await _dio.post(
        '$baseUrl/face-recognition/enroll',
        data: formData,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return {'success': true, 'data': response.data};
      } else {
        return {
          'success': false,
          'message':
              'Server error (${response.statusCode}): ${response.statusMessage}',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Enrollment error: $errorMsg');
      return {'success': false, 'message': errorMsg};
    } catch (e) {
      print('Unexpected enrollment error: $e');
      return {'success': false, 'message': 'Unexpected error: $e'};
    }
  }

  Future<Map<String, dynamic>> verifyFaceWithBytes({
    required Uint8List imageBytes,
  }) async {
    try {
      final FormData formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(
          imageBytes,
          filename: 'face_image.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
      });

      print('Attempting to connect to: $baseUrl/face-recognition/verify');

      final response = await _dio.post(
        '$baseUrl/face-recognition/verify',
        data: formData,
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': response.data};
      } else {
        return {
          'success': false,
          'message':
              'Server error (${response.statusCode}): ${response.statusMessage}',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Verification error: $errorMsg');
      return {'success': false, 'message': errorMsg};
    } catch (e) {
      print('Unexpected verification error: $e');
      return {'success': false, 'message': 'Unexpected error: $e'};
    }
  }

  // Face login method that returns complete user data and token
  Future<Map<String, dynamic>> loginWithFace({
    required Uint8List imageBytes,
  }) async {
    try {
      final FormData formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(
          imageBytes,
          filename: 'face_image.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
      });

      print(
        'Attempting to connect to: $baseUrl/face-recognition/login-with-face',
      );

      final response = await _dio.post(
        '$baseUrl/face-recognition/login-with-face',
        data: formData,
      );

      if (response.statusCode == 200) {
        final data = response.data;
        await saveToken(data['token']);

        // Store user info
        await _storage.write(
          key: 'current_username',
          value: data['user']['username'],
        );
        await _storage.write(
          key: 'current_fullname',
          value: data['user']['full_name'] ?? data['user']['username'],
        );

        return {'success': true, 'data': data};
      } else {
        final data = response.data;
        return {
          'success': false,
          'error': data['detail'] ?? 'Face login failed',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      return {'success': false, 'error': errorMsg};
    } catch (e) {
      return {'success': false, 'error': 'Network error. Please try again.'};
    }
  }

  // Login method for the extended functionality
  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await _dio.post(
        '$baseUrl/auth/login',
        data: {'username': username, 'password': password},
      );

      if (response.statusCode == 200) {
        final data = response.data;
        await saveToken(data['token']);

        // Store user info
        await _storage.write(
          key: 'current_username',
          value: data['user']['username'],
        );
        await _storage.write(
          key: 'current_fullname',
          value: data['user']['full_name'] ?? data['user']['username'],
        );

        return {'success': true, 'data': data};
      } else {
        final data = response.data;
        return {'success': false, 'error': data['detail'] ?? 'Login failed'};
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      return {'success': false, 'error': errorMsg};
    } catch (e) {
      return {'success': false, 'error': 'Network error. Please try again.'};
    }
  }

  // Logout method for the extended functionality
  Future<void> logout() async {
    final token = await getToken();
    if (token != null) {
      try {
        await _dio.post(
          '$baseUrl/auth/logout',
          options: Options(headers: {'Authorization': 'Bearer $token'}),
        );
      } catch (e) {
        print('Logout error: $e');
      }
    }
    await removeToken();
  }

  // Get user profile
  Future<UserModel> getProfile() async {
    final token = await getToken();

    if (token == null || token.isEmpty) {
      throw Exception('Not authenticated. Please login again.');
    }

    try {
      final response = await _dio.get(
        '$baseUrl/user/profile',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        return UserModel.fromJson(data);
      } else {
        final errorData = response.data;
        throw Exception(errorData['detail'] ?? 'Failed to load profile');
      }
    } on DioException catch (e) {
      final errorData = e.response?.data;
      throw Exception(errorData['detail'] ?? 'Network error: ${e.toString()}');
    } catch (e) {
      throw Exception('Network error: ${e.toString()}');
    }
  }

  // Get user profile by username
  Future<Map<String, dynamic>?> getProfileFromUsername(String username) async {
    // This would be implemented to fetch profile by username from backend
    // For now, return null since we're relying on token-based profile access
    return null;
  }

  // Update user profile with basic data
  Future<Map<String, dynamic>> updateUserProfile({
    required String username,
    String? fullName,
    String? email,
    String? phone,
    String? address,
    String? currentCity,
    String? currentCountry,
    String? hotelName,
  }) async {
    final token = await getToken();

    final response = await _dio.put(
      '$baseUrl/user/profile',
      data: {
        'full_name': fullName ?? username,
        'email': email ?? '$username@example.com',
        'phone': phone ?? '',
        'address': address ?? '',
        'current_city': currentCity ?? '',
        'current_country': currentCountry ?? '',
        'hotel_name': hotelName ?? '',
      },
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      final data = response.data;
      return {'success': true, 'data': data};
    } else {
      final data = response.data;
      return {'success': false, 'error': data['detail'] ?? 'Update failed'};
    }
  }

  // Update user profile
  Future<Map<String, dynamic>> updateProfile(UserModel user) async {
    final token = await getToken();

    final response = await _dio.put(
      '$baseUrl/user/profile',
      data: user.toJson(),
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      final data = response.data;
      return {'success': true, 'data': data};
    } else {
      final data = response.data;
      return {'success': false, 'error': data['detail'] ?? 'Update failed'};
    }
  }

  // Register a new user with the backend
  Future<Map<String, dynamic>> register(
    String username,
    String email,
    String password,
  ) async {
    try {
      final response = await _dio.post(
        '$baseUrl/user/register',
        data: {
          'username': username,
          'email': email,
          'password': password,
          'full_name': username, // Use username as full name initially
        },
        options: Options(headers: {'Content-Type': 'application/json'}),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = response.data;
        return {'success': true, 'data': data};
      } else {
        final data = response.data;
        return {
          'success': false,
          'error': data['detail'] ?? 'Registration failed',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Registration error: $errorMsg');
      return {'success': false, 'error': errorMsg};
    } catch (e) {
      final errorMsg = 'Network error. Please try again.';
      print('Registration error: $e');
      return {'success': false, 'error': errorMsg};
    }
  }

  // Register a new user with profile and emergency contacts
  Future<Map<String, dynamic>> registerWithProfile({
    required String username,
    required String password,
    required Map<String, dynamic> profileData,
    required List<ContactModel> contacts,
  }) async {
    try {
      final response = await _dio.post(
        '$baseUrl/user/register',
        data: {
          'username': username,
          'email': profileData['email'] ?? '$username@example.com',
          'password': password,
          'full_name':
              profileData['fullName'] ?? profileData['full_name'] ?? username,
          'address': profileData['address'] ?? '',
          'phone': profileData['phone'] ?? profileData['phone_number'] ?? '',
          'current_city':
              profileData['city'] ?? profileData['current_city'] ?? '',
          'current_country':
              profileData['country'] ?? profileData['current_country'] ?? '',
          'hotel_name': profileData['hotel'] ?? profileData['hotel_name'] ?? '',
        },
        options: Options(headers: {'Content-Type': 'application/json'}),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        // If user was created successfully, add emergency contacts
        if (contacts.isNotEmpty) {
          // Try to add emergency contacts
          try {
            await updateEmergencyContacts(contacts);
          } catch (e) {
            print('Error adding emergency contacts: $e');
            // Don't fail the registration if contacts fail
          }
        }

        final data = response.data;
        return {'success': true, 'data': data};
      } else {
        final data = response.data;
        return {
          'success': false,
          'error': data['detail'] ?? 'Registration with profile failed',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      return {'success': false, 'error': errorMsg};
    } catch (e) {
      return {'success': false, 'error': 'Network error. Please try again.'};
    }
  }

  // Get emergency contacts
  Future<List<ContactModel>> getEmergencyContacts() async {
    final token = await getToken();

    if (token == null || token.isEmpty) {
      // If no token, return empty list or handle appropriately
      print('No authentication token found');
      return []; // Return empty list instead of throwing exception
    }

    try {
      final response = await _dio.get(
        '$baseUrl/user/emergency-contacts/',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        return data.map((json) => ContactModel.fromJson(json)).toList();
      } else {
        final errorData = response.data;
        throw Exception(errorData['detail'] ?? 'Failed to load contacts');
      }
    } on DioException catch (e) {
      final errorData = e.response?.data;
      throw Exception(errorData['detail'] ?? 'Network error: ${e.toString()}');
    } catch (e) {
      throw Exception('Network error: ${e.toString()}');
    }
  }

  // Update emergency contacts
  Future<Map<String, dynamic>> updateEmergencyContacts(
    List<ContactModel> contacts,
  ) async {
    final token = await getToken();

    final response = await _dio.put(
      '$baseUrl/user/emergency-contacts/',
      data: {'contacts': contacts.map((c) => c.toJson()).toList()},
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      final data = response.data;
      return {'success': true, 'data': data};
    } else {
      final data = response.data;
      return {'success': false, 'error': data['detail'] ?? 'Update failed'};
    }
  }

  // Trigger emergency SOS
  Future<Map<String, dynamic>> triggerEmergencySOS() async {
    String userName = 'unknown_user';

    // Try to get username from storage first (this should have the logged-in username)
    try {
      String? storedUsername = await _storage.read(key: 'current_username');
      if (storedUsername != null &&
          storedUsername.isNotEmpty &&
          storedUsername != 'unknown') {
        userName = storedUsername;
        print('Using stored username for emergency: $userName');
      } else {
        print('No valid username found in storage: $storedUsername');
      }
    } catch (e) {
      print('Error reading username from storage: $e');
    }

    // If we still don't have a valid username, try to get it from the token by fetching profile
    if (userName == 'unknown_user' || userName.isEmpty) {
      final token = await getToken();

      if (token != null && token.isNotEmpty) {
        try {
          final profile = await getProfile();
          userName = profile.username;

          // Update storage with the retrieved username for future use
          try {
            await _storage.write(key: 'current_username', value: userName);
          } catch (e) {
            print('Error saving username to storage: $e');
          }
        } catch (e) {
          print('Could not fetch profile for emergency SOS: $e');
          // Don't return error here, just continue with unknown_user as fallback
        }
      } else {
        print('No token available for emergency SOS');
      }
    }

    final payload = {
      'type': 'emergency',
      'user_name': userName,
      'signal': 'SOS_BUTTON',
    };

    try {
      final token = await getToken(); // Get token again for the request

      final response = await _dio.post(
        '$baseUrl/emergency/webhook',
        data: payload,
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            // Include authorization if token exists, but don't fail if it doesn't
            if (token != null && token.isNotEmpty)
              'Authorization': 'Bearer $token',
          },
        ),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        print('Emergency SOS triggered successfully for user: $userName');
        return {'success': true, 'data': data};
      } else {
        print('Emergency SOS failed with status: ${response.statusCode}');
        return {
          'success': false,
          'error': 'Server responded with status: ${response.statusCode}',
        };
      }
    } on DioException catch (e) {
      print('DioException in triggerEmergencySOS: $e');
      if (e.response != null) {
        print('Response error: ${e.response!.data}');
        return {
          'success': false,
          'error':
              'Server error: ${e.response!.statusCode} - ${e.response!.data}',
        };
      } else {
        return {'success': false, 'error': 'Network error: ${e.message}'};
      }
    } catch (e) {
      print('Error in triggerEmergencySOS: $e');
      return {'success': false, 'error': 'Unexpected error: $e'};
    }
  }

  // Alias for triggerEmergencySOS - used by EmergencyButton widget
  Future<Map<String, dynamic>> triggerEmergency() async {
    return await triggerEmergencySOS();
  }

  // Method for face liveness detection
  Future<Map<String, dynamic>> detectFaceLiveness({
    required Uint8List imageBytes,
  }) async {
    try {
      final FormData formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(  // Changed from 'file' to 'image' to match backend expectation
          imageBytes,
          filename: 'face_image.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
      });

      print('Attempting to connect to: $baseUrl/detect');

      final response = await _dio.post(
        '$baseUrl/detect',
        data: formData,
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': response.data};
      } else {
        return {
          'success': false,
          'message':
              'Server error (${response.statusCode}): ${response.statusMessage}',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Face liveness detection error: $errorMsg');
      return {'success': false, 'message': errorMsg};
    } catch (e) {
      print('Unexpected face liveness detection error: $e');
      return {'success': false, 'message': 'Unexpected error: $e'};
    }
  }

  // Method for palm enrollment
  Future<Map<String, dynamic>> enrollPalm({
    required String name,
    required String imageBase64,
  }) async {
    try {
      final response = await _dio.post(
        '$baseUrl/palm/enroll_user',
        data: {
          'name': name,
          'image_data': imageBase64,  // base64 encoded image
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ${await getToken()}', // Include auth token
          },
        ),
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': response.data};
      } else {
        return {
          'success': false,
          'message':
              'Server error (${response.statusCode}): ${response.statusMessage}',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Palm enrollment error: $errorMsg');
      return {'success': false, 'message': errorMsg};
    } catch (e) {
      print('Unexpected palm enrollment error: $e');
      return {'success': false, 'message': 'Unexpected error: $e'};
    }
  }

  // Method for palm verification
  Future<Map<String, dynamic>> verifyPalm({
    required String imageBase64,
  }) async {
    try {
      final response = await _dio.post(
        '$baseUrl/palm/verify_user',
        data: {
          'image_data': imageBase64,  // base64 encoded image
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ${await getToken()}', // Include auth token
          },
        ),
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': response.data};
      } else {
        return {
          'success': false,
          'message':
              'Server error (${response.statusCode}): ${response.statusMessage}',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      print('Palm verification error: $errorMsg');
      return {'success': false, 'message': errorMsg};
    } catch (e) {
      print('Unexpected palm verification error: $e');
      return {'success': false, 'message': 'Unexpected error: $e'};
    }
  }

  // Method for palm login
  Future<Map<String, dynamic>> loginWithPalm({
    required String imageBase64,
  }) async {
    try {
      final response = await _dio.post(
        '$baseUrl/auth/palm-auth',
        data: {
          'palm_image': imageBase64,  // base64 encoded image
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        await saveToken(data['token']);

        // Store user info
        await _storage.write(
          key: 'current_username',
          value: data['user']['username'],
        );
        await _storage.write(
          key: 'current_fullname',
          value: data['user']['full_name'] ?? data['user']['username'],
        );

        return {'success': true, 'data': data};
      } else {
        final data = response.data;
        return {
          'success': false,
          'error': data['detail'] ?? 'Palm login failed',
        };
      }
    } on DioException catch (e) {
      String errorMsg = 'Network error: ${e.message}';
      if (e.response != null) {
        final statusCode = e.response!.statusCode;
        final data = e.response!.data;
        if (data is Map && data.containsKey('detail')) {
          errorMsg = 'Server error ($statusCode): ${data['detail']}';
        } else {
          errorMsg = 'Server error ($statusCode): ${e.response!.statusMessage}';
        }
      }
      return {'success': false, 'error': errorMsg};
    } catch (e) {
      return {'success': false, 'error': 'Network error. Please try again.'};
    }
  }

  Future<String?> getUsername() async {
    return await _storage.read(key: 'current_username');
  }

  // Check if user has face enrollment
  Future<bool> hasFaceEnrollment(String userId) async {
    try {
      final response = await _dio.get('$baseUrl/face-recognition/user/$userId/has-face-enrollment');
      
      if (response.statusCode == 200) {
        final data = response.data;
        return data['has_enrollment'] == true;
      } else {
        print('Error checking face enrollment: ${response.statusCode}');
        return false;
      }
    } on DioException catch (e) {
      print('DioException checking face enrollment: $e');
      return false;
    } catch (e) {
      print('Error checking face enrollment: $e');
      return false;
    }
  }
}
