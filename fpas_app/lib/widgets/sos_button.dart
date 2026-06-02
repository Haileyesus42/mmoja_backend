import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class SosButton extends StatefulWidget {
  const SosButton({super.key});

  @override
  State<SosButton> createState() => _SosButtonState();
}

class _SosButtonState extends State<SosButton> {
  bool _isPressed = false;
  bool _isSending = false;

  Future<void> _triggerEmergencySOS() async {
    print("SOS Button: Long press detected"); // Debug log
    if (_isSending) {
      print("SOS Button: Already sending, returning early");
      return;
    }

    print("SOS Button: Starting emergency process");
    setState(() {
      _isSending = true;
    });

    try {
      print("SOS Button: Getting API service from provider");
      final apiService = Provider.of<ApiService>(context, listen: false);
      print("SOS Button: Calling triggerEmergencySOS method");
      final result = await apiService.triggerEmergencySOS();
      print("SOS Button: Received result from API: $result");

      if (result['success']) {
        print("SOS Button: Emergency alert sent successfully");
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Emergency alert sent successfully!'),
              backgroundColor: Colors.red,
              duration: Duration(seconds: 3),
            ),
          );
        }
      } else {
        print("SOS Button: Failed to send emergency alert: ${result['error']}");
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to send emergency alert: ${result['error']}'),
              backgroundColor: Colors.red,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      }
    } catch (e) {
      print("SOS Button: Error sending emergency alert: $e");
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error sending emergency alert: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } finally {
      print("SOS Button: Setting isSending to false");
      if (mounted) {
        setState(() {
          _isSending = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    print("SOS Button: Building widget");
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: Tooltip(
        message: 'Long press for emergency SOS',
        child: GestureDetector(
          onLongPress: _triggerEmergencySOS,
          onLongPressStart: (_) {
            print("SOS Button: Long press started");
            setState(() {
              _isPressed = true;
            });
          },
          onLongPressEnd: (_) {
            print("SOS Button: Long press ended");
            setState(() {
              _isPressed = false;
            });
          },
          child: Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: _isSending 
                  ? Colors.grey 
                  : _isPressed 
                      ? Colors.red.shade800 
                      : Colors.red,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.3),
                  blurRadius: 5,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                Icon(
                  Icons.error_outline,
                  color: Colors.white,
                  size: 20,
                ),
                if (_isSending)
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Center(
                      child: SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      ),
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