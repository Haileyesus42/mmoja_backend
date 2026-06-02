import 'package:flutter/material.dart';
import 'package:fpas_app/services/auth_service.dart';
import '../screens/dashboard_screen.dart';
import '../screens/camera_screen.dart'; // Import camera screen for face recognition

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final AuthService _authService = AuthService();
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (_usernameController.text.isEmpty) {
      if (mounted) { // Check if the widget is still mounted
        _showMessage('Please enter username');
      }
      return;
    }

    if (_passwordController.text.isEmpty) {
      // Check if the user has face enrollment set up
      bool hasFaceEnrollment = await _authService.hasFaceEnrollment(_usernameController.text.trim());
      
      if (hasFaceEnrollment) {
        // If user has face enrollment but no password, suggest face login
        if (mounted) { // Check if the widget is still mounted
          _showMessage('Face enrollment detected. Use face recognition or enter password.');
        }
        return;
      } else {
        if (mounted) { // Check if the widget is still mounted
          _showMessage('Please enter password');
        }
        return;
      }
    }

    if (mounted) { // Check if the widget is still mounted
      setState(() {
        _isLoading = true;
      });
    }

    try {
      bool success = await _authService.login(
        _usernameController.text.trim(),
        _passwordController.text,
      );

      if (success) {
        // Get the current logged-in user to pass to the dashboard
        String? currentUser = await _authService.getCurrentUser();
        if (mounted) { // Check if the widget is still mounted
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
              builder: (context) => DashboardScreen(username: currentUser ?? ''),
            ),
          );
        }
      } else {
        if (mounted) { // Check if the widget is still mounted
          _showMessage('Invalid username or password');
        }
      }
    } catch (e) {
      if (mounted) { // Check if the widget is still mounted
        _showMessage('Login failed: $e');
      }
    } finally {
      if (mounted) { // Check if the widget is still mounted
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _showMessage(String message) {
    if (mounted) { // Check if the widget is still mounted
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  // Method to handle face recognition login
  Future<void> _loginWithFace() async {
    String? currentUser = await _authService.getCurrentUser();
    bool hasFaceEnrollment = await _authService.hasFaceEnrollment(currentUser);
    
    // If we know the current user and they have face enrollment, go directly to face login
    if (currentUser != null && currentUser.isNotEmpty && hasFaceEnrollment) {
      if (mounted) { // Check if the widget is still mounted
        // Navigate to camera screen in face login mode
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => const CameraScreen(mode: 'face_login'),
          ),
        );
      }
    } else {
      if (mounted) { // Check if the widget is still mounted
        // Otherwise, navigate to camera screen in face login mode anyway
        // The user will need to enroll first if they haven't already
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => const CameraScreen(mode: 'face_login'),
          ),
        );
      }
    }
  }

  // Method to handle palm recognition login
  Future<void> _loginWithPalm() async {
    // Navigate to camera screen in palm login mode
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => const CameraScreen(mode: 'palm_login'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login'), centerTitle: true),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Welcome Back!',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Please sign in to continue',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, color: Colors.grey),
                ),
                const SizedBox(height: 40),
                TextField(
                  controller: _usernameController,
                  decoration: InputDecoration(
                    labelText: 'Username',
                    prefixIcon: const Icon(Icons.person),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _isLoading ? null : _login,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Sign In'),
                ),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: _loginWithFace,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    side: BorderSide(color: Colors.blue.shade300),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.face, color: Colors.blue.shade300),
                      const SizedBox(width: 8),
                      Text(
                        'Sign in with Face Recognition',
                        style: TextStyle(color: Colors.blue.shade300),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: _loginWithPalm,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    side: BorderSide(color: Colors.green.shade300),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.handshake_outlined, color: Colors.green.shade300),
                      const SizedBox(width: 8),
                      Text(
                        'Sign in with Palm Recognition',
                        style: TextStyle(color: Colors.green.shade300),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pushNamed('/register');
                  },
                  child: const Text('Don\'t have an account? Sign Up'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
