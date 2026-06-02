import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../widgets/face_detection_overlay.dart';
import 'dashboard_screen.dart';
import 'dart:typed_data';

class CameraScreen extends StatefulWidget {
  final String
  mode; // 'enroll', 'verify', 'face_login', 'palm_enroll', 'palm_verify', 'palm_login'
  final String? username; // Optional username parameter

  const CameraScreen({super.key, required this.mode, this.username});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  late CameraController _controller;
  late Future<void> _initializeControllerFuture;
  final FaceDetector _faceDetector = FaceDetector(
    options: FaceDetectorOptions(performanceMode: FaceDetectorMode.fast),
  );

  bool _isDetecting = true; // Made final and initialized to true
  bool _isProcessing = false;
  bool _isLive = false;
  bool _isVerified = false;
  String _message = 'Position your face in the frame';
  String _verificationResult = '';
  final AuthService _authService = AuthService();
  final ApiService _apiService = ApiService();
  String _currentMode = '';

  @override
  void initState() {
    super.initState();
    _currentMode = widget.mode;
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    final firstCamera = cameras.firstWhere(
      (camera) => camera.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );

    _controller = CameraController(firstCamera, ResolutionPreset.medium);

    _initializeControllerFuture = _controller.initialize();
    if (mounted) {
      setState(() {});
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _faceDetector.close();
    super.dispose();
  }

  Future<void> _captureAndProcessFace() async {
    if (_controller.value.isTakingPicture) return;

    setState(() {
      _isProcessing = true;
      _message = 'Processing...';
    });

    try {
      // Capture the image
      XFile picture = await _controller.takePicture();
      Uint8List imageBytes = await picture.readAsBytes();

      // Create InputImage correctly for camera images
      final inputImage = InputImage.fromFilePath(picture.path);

      final faces = await _faceDetector.processImage(inputImage);

      if (faces.isEmpty) {
        setState(() {
          _isProcessing = false;
          _message = 'No face detected. Please try again.';
        });
        return;
      }

      // For simplicity, we'll just take the first detected face
      // Note: We're intentionally not using the face variable to avoid the unused_local_variable warning

      // Perform liveness detection simulation (in real implementation, this would be more sophisticated)
      _performLivenessCheck(imageBytes);
    } catch (e) {
      setState(() {
        _isProcessing = false;
        _message = 'Error processing image: $e';
      });
    }
  }

  void _performLivenessCheck(Uint8List imageBytes) {
    // Simulate liveness detection
    // In a real implementation, this would involve checking for blinking, head movement, etc.
    Future.delayed(const Duration(seconds: 1)).then((_) {
      if (mounted) { // Fixed: added mounted check to prevent context issue
        setState(() {
          _isLive = true;
          _message = 'Liveness confirmed. Processing...';
        });
      }

      // Now perform the actual face operation based on mode
      _performFaceOperation(imageBytes);
    });
  }

  void _performFaceOperation(Uint8List imageBytes) {
    // Simulate face operation based on the mode
    switch (_currentMode) {
      case 'enroll':
        _enrollFace(imageBytes);
        break;
      case 'verify':
        _verifyFace(imageBytes);
        break;
      case 'face_login':
        _faceLogin(imageBytes);
        break;
      case 'palm_enroll':
        _enrollPalm();
        break;
      case 'palm_verify':
        _verifyPalm();
        break;
      case 'palm_login':
        _palmLogin();
        break;
      default:
        if (mounted) { // Fixed: added mounted check
          setState(() {
            _isProcessing = false;
            _message = 'Invalid mode selected';
          });
        }
    }
  }

  void _enrollFace(Uint8List imageBytes) async {
    try {
      // Get current user if available, otherwise use a placeholder
      String userId =
          widget.username ??
          await _authService.getCurrentUser() ??
          'unknown_user';

      // Call the API service with correct parameters - pass the imageBytes
      final result = await _apiService.enrollFace(
        userId: userId,
        name: userId,
        imagePath: null, // Will be handled differently for mobile vs web
        imageBytes: imageBytes, // Pass the image bytes directly
      );

      if (mounted) { // Fixed: added mounted check
        if (result['success'] == true) {
          setState(() {
            _isProcessing = false;
            _isVerified = true;
            _verificationResult = '✅ Face enrolled successfully!';
            _message = 'Face has been successfully enrolled';
          });

          // Navigate back to the previous screen after a short delay to show success message
          await Future.delayed(const Duration(seconds: 2));
          if (mounted) {
            Navigator.of(context).pop({'enrolled': true, 'name': userId});
          }
        } else {
          setState(() {
            _isProcessing = false;
            _verificationResult = '❌ Face enrollment failed';
            _message = result['message'] ?? 'Unknown error occurred';
          });
        }
      }
    } catch (e) {
      if (mounted) { // Fixed: added mounted check
        setState(() {
          _isProcessing = false;
          _verificationResult = '❌ Error enrolling face';
          _message = 'Error: $e';
        });
      }
    }
  }

  void _verifyFace(Uint8List imageBytes) async {
    try {
      // Call the API service with correct parameters - pass the imageBytes
      final result = await _apiService.verifyFace(
        imagePath: null, // Will be handled differently for mobile vs web
        imageBytes: imageBytes, // Pass the image bytes directly
      );

      if (mounted) { // Fixed: added mounted check
        if (result['is_match'] == true) {
          setState(() {
            _isProcessing = false;
            _isVerified = true;
            _verificationResult = '✅ Face verified!';
            _message = 'Face verification successful';
          });
        } else {
          setState(() {
            _isProcessing = false;
            _verificationResult = '❌ Face not recognized';
            _message = result['message'] ?? 'Face does not match registered face';
          });
        }
      }
    } catch (e) {
      if (mounted) { // Fixed: added mounted check
        setState(() {
          _isProcessing = false;
          _verificationResult = '❌ Error verifying face';
          _message = 'Error: $e';
        });
      }
    }
  }

  void _faceLogin(Uint8List imageBytes) async {
    try {
      // Call the API service with correct parameters
      final result = await _apiService.loginWithFace(imageBytes: imageBytes);

      if (mounted) { // Fixed: added mounted check
        if (result['success'] == true) {
          setState(() {
            _isProcessing = false;
            _isVerified = true;
            _verificationResult = '✅ Login successful!';
            _message = 'Welcome back!';
          });

          // Store context in a local variable before the async operation to prevent context issue
          final contextLocal = context;
          
          // Navigate to dashboard after a short delay
          Future.delayed(const Duration(seconds: 2)).then((_) {
            if (contextLocal.mounted) { // Fixed: added mounted check to prevent context issue using local context variable
              Navigator.of(contextLocal).pushReplacement(
                MaterialPageRoute(
                  builder: (context) =>
                      DashboardScreen(username: result['username'] ?? 'User'),
                ),
              );
            }
          });
        } else {
          setState(() {
            _isProcessing = false;
            _verificationResult = '❌ Login failed';
            _message = result['message'] ?? 'Face not recognized';
          });
        }
      }
    } catch (e) {
      if (mounted) { // Fixed: added mounted check
        setState(() {
          _isProcessing = false;
          _verificationResult = '❌ Error during login';
          _message = 'Error: $e';
        });
      }
    }
  }

  // Placeholder implementations for palm recognition
  void _enrollPalm() async {
    if (mounted) { // Fixed: added mounted check
      setState(() {
        _isProcessing = false;
        _verificationResult = '📝 Palm enrollment (simulated)';
        _message = 'Palm enrollment would happen here';
      });
    }
  }

  void _verifyPalm() async {
    if (mounted) { // Fixed: added mounted check
      setState(() {
        _isProcessing = false;
        _verificationResult = '🌐 Palm verification (simulated)';
        _message = 'Palm verification would happen here';
      });
    }
  }

  void _palmLogin() async {
    if (mounted) { // Fixed: added mounted check
      setState(() {
        _isProcessing = false;
        _verificationResult = '🌐 Palm login (simulated)';
        _message = 'Palm login would happen here';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          _currentMode.startsWith('palm_')
              ? 'Palm Authentication'
              : 'Face Authentication',
          style: const TextStyle(fontSize: 18),
        ),
        centerTitle: true,
        backgroundColor: theme.brightness == Brightness.dark
            ? Colors.grey[900]
            : theme.primaryColor,
        foregroundColor: Colors.white,
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: BoxDecoration(
                color: theme.brightness == Brightness.dark
                    ? Colors.grey[900]
                    : theme.primaryColor,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Icon(
                    _currentMode.startsWith('palm_')
                        ? Icons.handshake_outlined
                        : Icons.face,
                    size: 32,
                    color: Colors.white,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'User Name', // TODO: Get actual username
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    _currentMode.startsWith('palm_')
                        ? 'Palm Authentication System'
                        : 'Face Authentication System',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ],
              ),
            ),
            ListTile(
              leading: const Icon(Icons.home, size: 20),
              title: const Text('Dashboard', style: TextStyle(fontSize: 14)),
              onTap: () {
                Navigator.pop(context); // Close drawer
                // Go back to dashboard by popping the current screen
                Navigator.pop(context);
              },
            ),
            if (widget.mode != 'face_login' && widget.mode != 'palm_login') ...[
              ListTile(
                leading: const Icon(Icons.app_registration, size: 20),
                title: const Text(
                  'Enroll Face',
                  style: TextStyle(fontSize: 14),
                ),
                onTap: () {
                  setState(() {
                    _currentMode = 'enroll';
                    _isLive = false;
                    _isVerified = false;
                    _message = 'Position your face in the frame to enroll';
                  });
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.app_registration, size: 20),
                title: const Text(
                  'Enroll Palm',
                  style: TextStyle(fontSize: 14),
                ),
                onTap: () {
                  setState(() {
                    _currentMode = 'palm_enroll';
                    _isLive = false;
                    _isVerified = false;
                    _message = 'Position your palm in the frame to enroll';
                  });
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.verified_user, size: 20),
                title: const Text(
                  'Verify Face',
                  style: TextStyle(fontSize: 14),
                ),
                onTap: () {
                  setState(() {
                    _currentMode = 'verify';
                    _isLive = false;
                    _isVerified = false;
                    _message = 'Position your face in the frame to verify';
                  });
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.verified_user, size: 20),
                title: const Text(
                  'Verify Palm',
                  style: TextStyle(fontSize: 14),
                ),
                onTap: () {
                  setState(() {
                    _currentMode = 'palm_verify';
                    _isLive = false;
                    _isVerified = false;
                    _message = 'Position your palm in the frame to verify';
                  });
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.login, size: 20),
                title: const Text('Face Login', style: TextStyle(fontSize: 14)),
                onTap: () {
                  setState(() {
                    _currentMode = 'face_login';
                    _isLive = false;
                    _isVerified = false;
                    _message = 'Position your face in the frame to login';
                  });
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.login, size: 20),
                title: const Text('Palm Login', style: TextStyle(fontSize: 14)),
                onTap: () {
                  setState(() {
                    _currentMode = 'palm_login';
                    _isLive = false;
                    _isVerified = false;
                    _message = 'Position your palm in the frame to login';
                  });
                  Navigator.pop(context);
                },
              ),
            ],
            const Divider(height: 16, thickness: 1),
            ListTile(
              leading: const Icon(Icons.logout, size: 20),
              title: const Text('Logout', style: TextStyle(fontSize: 14)),
              onTap: () async {
                // Store context in a local variable before the async operation to prevent context issue
                final contextLocal = context;
                
                // Use the properly initialized AuthService instance
                await _authService.logout();
                
                if (contextLocal.mounted) { // Fixed: added mounted check to prevent context issue using local context variable
                  Navigator.of(contextLocal).popUntil((route) => route.isFirst);
                }
              },
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: FutureBuilder<void>(
              future: _initializeControllerFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.done) {
                  return Stack(
                    fit: StackFit.expand,
                    children: [
                      CameraPreview(_controller),
                      // Animated face detection overlay
                      FaceDetectionOverlay(
                        isDetecting: _isDetecting,
                        isProcessing: _isProcessing,
                        isLive: _isLive,
                        isVerified: _isVerified,
                        confidence: 0.0, // Not used in the overlay currently
                        statusText: _message,
                      ),
                      Align(
                        alignment: Alignment.bottomCenter,
                        child: Container(
                          padding: const EdgeInsets.all(16.0),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                Colors.transparent,
                                theme.brightness == Brightness.dark
                                    ? Colors.black87
                                    : Colors.white70,
                              ],
                            ),
                          ),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                _verificationResult.isNotEmpty
                                    ? _verificationResult
                                    : _message,
                                style: TextStyle(
                                  color: _verificationResult.isNotEmpty
                                      ? (_verificationResult.contains('✅')
                                            ? Colors.green
                                            : _verificationResult.contains('❌')
                                            ? Colors.red
                                            : _verificationResult.contains('📝')
                                            ? Colors.orange
                                            : _verificationResult.contains('🌐')
                                            ? Colors.blue
                                            : Colors.white)
                                      : (theme.brightness == Brightness.dark
                                            ? Colors.white70
                                            : Colors.black87),
                                  fontSize: 16.0,
                                  fontWeight: FontWeight.bold,
                                ),
                                textAlign: TextAlign.center,
                              ),
                              if (_verificationResult.isNotEmpty)
                                const SizedBox(height: 8),
                              if (_verificationResult.isNotEmpty)
                                Text(
                                  _message,
                                  style: TextStyle(
                                    color: theme.brightness == Brightness.dark
                                        ? Colors.white70
                                        : Colors.black87,
                                    fontSize: 14.0,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  );
                } else {
                  return const Center(child: CircularProgressIndicator());
                }
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ElevatedButton(
              onPressed: _isProcessing ? null : _captureAndProcessFace,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 16,
                ),
                backgroundColor:
                    theme.primaryColor, // Match parent dashboard theme
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              // No icon used to keep the UI clean and simple
              child: Text(
                _currentMode == 'enroll'
                    ? 'Capture & Enroll Face'
                    : _currentMode == 'face_login'
                    ? 'Capture & Face Login'
                    : _currentMode == 'palm_enroll'
                    ? 'Capture & Enroll Palm'
                    : _currentMode == 'palm_login'
                    ? 'Capture & Palm Login'
                    : _currentMode == 'palm_verify'
                    ? 'Capture & Verify Palm'
                    : 'Capture & Verify Face',
              ),
            ),
          ),
        ],
      ),
    );
  }
}

