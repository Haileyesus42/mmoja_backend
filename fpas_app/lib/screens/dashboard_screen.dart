import 'package:flutter/material.dart';
import 'package:fpas_app/auth/login_screen.dart';
import 'dart:ui' as ui;
import 'camera_screen.dart'; // Import the camera screen
import 'profile_screen.dart'; // Import profile screen
import '../services/auth_service.dart'; // Import auth service for logout
import '../widgets/sos_button.dart'; // Import the SOS button widget

class DashboardScreen extends StatefulWidget {
  final String username;

  const DashboardScreen({super.key, required this.username});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final AuthService _authService = AuthService();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'FPAS Dashboard - ${widget.username}',
          style: const TextStyle(fontSize: 16),
        ),
        backgroundColor: theme.brightness == Brightness.dark
            ? Colors.grey[900]
            : theme.primaryColor, // Dark app bar
        foregroundColor: Colors.white,
        automaticallyImplyLeading:
            false, // We'll provide our own leading button
        toolbarHeight: 56, // Compact toolbar
        leading: Builder(
          builder: (context) => IconButton(
            icon: const Icon(Icons.menu),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        actions: const [
          SosButton(), // Add SOS button to the app bar
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          shrinkWrap: true,
          children: [
            DrawerHeader(
              decoration: BoxDecoration(
                color: theme.brightness == Brightness.dark
                    ? Colors.grey[900]
                    : theme.primaryColor,
              ),
              margin: EdgeInsets.zero,
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Icon(Icons.face, size: 32, color: Colors.white),
                  const SizedBox(height: 4),
                  Text(
                    widget.username,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    'Emergency Management System', // Updated subtitle
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ],
              ),
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              leading: const Icon(Icons.home, size: 20),
              title: const Text('Dashboard', style: TextStyle(fontSize: 14)),
              selected: true,
              dense: true,
              minVerticalPadding: 4,
              onTap: () {
                // Stay on dashboard
                Navigator.pop(context);
              },
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              leading: const Icon(Icons.app_registration, size: 20),
              title: const Text('Enroll Face', style: TextStyle(fontSize: 14)),
              dense: true,
              minVerticalPadding: 4,
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => CameraScreen(mode: 'enroll', username: widget.username),
                  ),
                );
              },
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              leading: const Icon(Icons.verified_user, size: 20),
              title: const Text('Verify Face', style: TextStyle(fontSize: 14)),
              dense: true,
              minVerticalPadding: 4,
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => CameraScreen(mode: 'verify', username: widget.username),
                  ),
                );
              },
            ),
            const Divider(height: 16, thickness: 1),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              leading: const Icon(Icons.logout, size: 20),
              title: const Text('Logout', style: TextStyle(fontSize: 14)),
              dense: true,
              minVerticalPadding: 4,
              onTap: () async {
                // Perform logout
                await AuthService().logout();

                // Close the drawer first
                Navigator.of(context).pop();

                // Navigate back to login screen by replacing all routes with the login screen
                Navigator.of(context).pushAndRemoveUntil(
                  MaterialPageRoute(
                    builder: (context) => LoginScreen(), // Removed const
                  ),
                  (Route<dynamic> route) => false,
                );
              },
            ),
          ],
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Welcome message
            Card(
              elevation: 2,
              margin: const EdgeInsets.only(bottom: 16),
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  children: [
                    Icon(Icons.face, size: 40, color: theme.primaryColor),
                    const SizedBox(height: 8),
                    Text(
                      'Welcome, ${widget.username}!',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Secure and reliable face recognition',
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),

            // Cards list - using ListView instead of GridView for better performance
            Expanded(
              child: ListView(
                padding: EdgeInsets.zero,
                children: [
                  // Face Authentication Card
                  Card(
                    elevation: 2,
                    margin: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                CameraScreen(mode: 'verify', username: widget.username),
                          ),
                        );
                      },
                      child: Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 20,
                              backgroundColor: theme.primaryColor,
                              child: const Icon(
                                Icons.face,
                                color: Colors.white,
                                size: 18,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    'Face Authentication',
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: theme.primaryColor,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  const Text(
                                    'Verify using facial recognition',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Icon(
                              Icons.arrow_forward_ios,
                              color: Colors.grey[600],
                              size: 14,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // User Profile Card
                  Card(
                    elevation: 2,
                    margin: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      onTap: () {
                        // Navigate to Profile Screen
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ProfileScreen(),
                          ),
                        );
                      },
                      child: Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 20,
                              backgroundColor: Colors.blue,
                              child: const Icon(
                                Icons.person,
                                color: Colors.white,
                                size: 18,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    'User Profile',
                                    style: const TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.blue,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  const Text(
                                    'Manage personal information',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Icon(
                              Icons.arrow_forward_ios,
                              color: Colors.grey[600],
                              size: 14,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // Security Settings Card
                  Card(
                    elevation: 2,
                    margin: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      onTap: () {
                        // No screen available for Security Settings, removed navigation
                      },
                      child: Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 20,
                              backgroundColor: Colors.orange,
                              child: const Icon(
                                Icons.security,
                                color: Colors.white,
                                size: 18,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    'Security Settings',
                                    style: const TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.orange,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  const Text(
                                    'Configure security preferences',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Icon(
                              Icons.arrow_forward_ios,
                              color: Colors.grey[600],
                              size: 14,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Face guide painter (oval shape) - kept compact
class _FaceGuidePainter extends CustomPainter {
  final Color borderColor;

  _FaceGuidePainter({required this.borderColor});

  @override
  void paint(Canvas canvas, ui.Size size) {
    final paint = Paint()
      ..color = Colors.black.withOpacity(0.5)
      ..style = PaintingStyle.fill;
    canvas.drawRect(ui.Rect.fromLTWH(0, 0, size.width, size.height), paint);

    final ovalWidth = size.width * 0.7;
    final ovalHeight = size.width * 0.9;
    final left = (size.width - ovalWidth) / 2;
    final top = (size.height - ovalHeight) / 2;
    final ovalRect = ui.Rect.fromLTWH(left, top, ovalWidth, ovalHeight);

    final clearPaint = Paint()
      ..color = Colors.transparent
      ..blendMode = BlendMode.clear;
    canvas.drawOval(ovalRect, clearPaint);

    final borderPaint = Paint()
      ..color = borderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0;
    canvas.drawOval(ovalRect, borderPaint);
  }

  @override
  bool shouldRepaint(covariant _FaceGuidePainter oldDelegate) {
    return oldDelegate.borderColor != borderColor;
  }
}
