import 'package:flutter/material.dart';
import 'camera_screen.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../auth/login_screen.dart'; // Import login screen
import '../models/contact_model.dart';

class AuthenticationSetupScreen extends StatefulWidget {
  final String username;
  final String password;
  final Map<String, dynamic> profileData;
  final List<ContactModel> contacts;

  const AuthenticationSetupScreen({
    super.key,
    required this.username,
    required this.password,
    required this.profileData,
    required this.contacts,
  });

  @override
  State<AuthenticationSetupScreen> createState() =>
      _AuthenticationSetupScreenState();
}

class _AuthenticationSetupScreenState extends State<AuthenticationSetupScreen> {
  bool _faceRecognitionEnabled = false;
  bool _palmRecognitionEnabled = false;
  bool _isLoading = false;
  final AuthService _authService = AuthService();
  final ApiService _apiService = ApiService();

  void _setupFaceRecognition() async {
    // Navigate to camera screen for face enrollment
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) =>
            CameraScreen(mode: 'enroll', username: widget.username),
      ),
    );

    if (result != null && result['enrolled'] == true) {
      String enrolledName = result['name'] ?? widget.username;
      setState(() {
        _faceRecognitionEnabled = true;
      });
      _showMessage('Face recognition set up successfully for $enrolledName!');
    } else if (result != null && result['enrolled'] == false) {
      _showMessage('Face enrollment failed. Please try again.');
    }
    // If result is null, the user likely cancelled the enrollment process
  }

  void _setupPalmRecognition() async {
    // Navigate to camera screen for palm enrollment
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) =>
            CameraScreen(mode: 'palm_enroll', username: widget.username),
      ),
    );

    if (result != null && result['enrolled'] == true) {
      String enrolledName = result['name'] ?? widget.username;
      setState(() {
        _palmRecognitionEnabled = true;
      });
      _showMessage('Palm recognition set up successfully for $enrolledName!');
    } else if (result != null && result['enrolled'] == false) {
      _showMessage('Palm enrollment failed. Please try again.');
    }
    // If result is null, the user likely cancelled the enrollment process
  }

  void _showMessage(String message) {
    if (mounted) { // Check if the widget is still mounted
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  void _completeSetup() {
    setState(() {
      _isLoading = true;
    });

    // First, log the user in to get a valid authentication token
    _authService.login(widget.username, widget.password).then((loginSuccess) {
      if (loginSuccess) {
        // Now that user is logged in and has a valid token, save emergency contacts
        _apiService
            .updateEmergencyContacts(widget.contacts)
            .then((contactResult) {
              if (contactResult['success']) {
                // After saving contacts, update the user profile
                _updateProfileSilently(); // Update profile in the background without blocking
              } else {
                setState(() {
                  _isLoading = false;
                });
                _showMessage(
                  contactResult['error'] ?? 'Failed to save emergency contacts. Please try again.',
                );
              }
            })
            .catchError((error) {
              if (mounted) {
                setState(() {
                  _isLoading = false;
                });
                _showMessage('Error saving emergency contacts: $error');
              }
            });
      } else {
        setState(() {
          _isLoading = false;
        });
        _showMessage('Login failed. Cannot save emergency contacts.');
      }
    }).catchError((error) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        _showMessage('Error logging in: $error');
      }
    });
  }

  // Helper method to update profile in the background without blocking the flow
  void _updateProfileSilently() {
    _apiService
        .updateUserProfile(
          username: widget.username,
          fullName:
              widget.profileData['fullName'] ??
              widget.profileData['full_name'] ??
              widget.username,
          email:
              widget.profileData['email'] ??
              '${widget.username}@example.com',
          phone:
              widget.profileData['phone'] ??
              widget.profileData['phone_number'] ??
              '',
          address: widget.profileData['address'] ?? '',
          currentCity:
              widget.profileData['city'] ??
              widget.profileData['current_city'] ??
              '',
          currentCountry:
              widget.profileData['country'] ??
              widget.profileData['current_country'] ??
              '',
          hotelName:
              widget.profileData['hotel'] ??
              widget.profileData['hotel_name'] ??
              '',
        )
        .then((profileResult) {
          // Profile update completed (whether success or failure), navigate to login
          if (mounted) {
            setState(() {
              _isLoading = false;
            });
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (context) => const LoginScreen(),
              ),
            );
          }
        })
        .catchError((error) {
          // Profile update failed, but that's okay, contacts were saved
          // Navigate to login anyway
          if (mounted) {
            setState(() {
              _isLoading = false;
            });
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (context) => const LoginScreen(),
              ),
            );
          }
        });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Set Up Authentication'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Authentication Methods',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Set up biometric authentication for faster access',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 14, color: Colors.grey),
                ),
                const SizedBox(height: 24),

                // Palm Recognition Setup
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.handshake_outlined,
                              size: 28,
                              color: _palmRecognitionEnabled
                                  ? Colors.green
                                  : Colors.blue,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Palm Recognition',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.black,
                                    ),
                                  ),
                                  Text(
                                    _palmRecognitionEnabled
                                        ? 'Enabled - Ready to use'
                                        : 'Tap below to set up',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: _palmRecognitionEnabled
                                          ? Colors.green
                                          : Colors.grey[600],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerRight,
                          child: ElevatedButton(
                            onPressed: !_palmRecognitionEnabled
                                ? _setupPalmRecognition
                                : null,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _palmRecognitionEnabled
                                  ? Colors.green
                                  : Colors.blue,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 8,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ),
                            child: Text(
                              _palmRecognitionEnabled ? 'Enabled' : 'Set Up',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                // Face Recognition Setup
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.face,
                              size: 28,
                              color: _faceRecognitionEnabled
                                  ? Colors.green
                                  : Colors.blue,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Face Recognition',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.black,
                                    ),
                                  ),
                                  Text(
                                    _faceRecognitionEnabled
                                        ? 'Enabled - Ready to use'
                                        : 'Tap below to set up',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: _faceRecognitionEnabled
                                          ? Colors.green
                                          : Colors.grey[600],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerRight,
                          child: ElevatedButton(
                            onPressed: !_faceRecognitionEnabled
                                ? _setupFaceRecognition
                                : null,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _faceRecognitionEnabled
                                  ? Colors.green
                                  : Colors.blue,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 8,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ),
                            child: Text(
                              _faceRecognitionEnabled ? 'Enabled' : 'Set Up',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                ElevatedButton(
                  onPressed: _isLoading ? null : _completeSetup,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text(
                          'Complete Setup & Go to Login',
                          style: TextStyle(fontSize: 14),
                        ),
                ),
                
                // Add a hint about the credentials to help with debugging
                const SizedBox(height: 16),
                Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.yellow.shade100,
                    border: Border.all(color: Colors.yellow.shade300),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    'Using credentials:\nUsername: ${widget.username}\nPassword: [hidden]',
                    style: TextStyle(fontSize: 12, color: Colors.black54),
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}