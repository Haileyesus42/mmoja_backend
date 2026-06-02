import 'package:flutter/material.dart';
import 'dart:ui' as ui;

class FaceDetectionOverlay extends StatefulWidget {
  final bool isDetecting;
  final bool isProcessing;
  final bool isLive;
  final bool isVerified;
  final double confidence;
  final String statusText;

  const FaceDetectionOverlay({
    super.key,
    required this.isDetecting,
    required this.isProcessing,
    required this.isLive,
    required this.isVerified,
    required this.confidence,
    required this.statusText,
  });

  @override
  State<FaceDetectionOverlay> createState() => _FaceDetectionOverlayState();
}

class _FaceDetectionOverlayState extends State<FaceDetectionOverlay>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _checkmarkController;
  late AnimationController _livenessController;
  
  late Animation<double> _pulseAnimation;
  late Animation<double> _checkmarkScaleAnimation;
  late Animation<double> _livenessOpacityAnimation;

  @override
  void initState() {
    super.initState();
    
    // Pulse animation for the oval frame
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);
    
    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.2,
    ).animate(CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut));

    // Checkmark animation for success state
    _checkmarkController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    
    _checkmarkScaleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _checkmarkController, curve: Curves.elasticOut));

    // Liveness detection animation
    _livenessController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    )..repeat(reverse: true);
    
    _livenessOpacityAnimation = Tween<double>(
      begin: 0.3,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _livenessController, curve: Curves.easeIn));
  }

  @override
  void didUpdateWidget(FaceDetectionOverlay oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    // Trigger checkmark animation when verification succeeds
    if (!oldWidget.isVerified && widget.isVerified) {
      _checkmarkController.forward().then((_) {
        _checkmarkController.reset();
      });
    }
    
    // Start liveness animation when processing begins
    if (!oldWidget.isProcessing && widget.isProcessing) {
      _livenessController.repeat(reverse: true);
    } else if (oldWidget.isProcessing && !widget.isProcessing) {
      _livenessController.stop();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _checkmarkController.dispose();
    _livenessController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return CustomPaint(
      painter: _FaceDetectionPainter(
        borderColor: _getBorderColor(theme),
        borderWidth: _getBorderWidth(),
        pulseValue: _pulseAnimation.value,
        isProcessing: widget.isProcessing,
        isLive: widget.isLive,
        isVerified: widget.isVerified,
        livenessOpacity: _livenessOpacityAnimation.value,
      ),
      size: Size.infinite,
    );
  }

  Color _getBorderColor(ThemeData theme) {
    if (widget.isVerified) {
      return Colors.green;
    } else if (widget.isLive) {
      return Colors.greenAccent;
    } else if (widget.isProcessing) {
      return Colors.amber;
    } else {
      return theme.primaryColor;
    }
  }

  double _getBorderWidth() {
    if (widget.isVerified || widget.isLive) {
      return 4.0;
    } else if (widget.isProcessing) {
      return 3.0;
    } else {
      return 2.0;
    }
  }
}

class _FaceDetectionPainter extends CustomPainter {
  final Color borderColor;
  final double borderWidth;
  final double pulseValue;
  final bool isProcessing;
  final bool isLive;
  final bool isVerified;
  final double livenessOpacity;

  _FaceDetectionPainter({
    required this.borderColor,
    required this.borderWidth,
    required this.pulseValue,
    required this.isProcessing,
    required this.isLive,
    required this.isVerified,
    required this.livenessOpacity,
  });

  @override
  void paint(Canvas canvas, ui.Size size) {
    // Define the oval area where the face should be positioned
    final ovalWidth = size.width * 0.7;
    final ovalHeight = size.width * 0.9;
    final left = (size.width - ovalWidth) / 2;
    final top = (size.height - ovalHeight) / 2;
    final ovalRect = ui.Rect.fromLTWH(left, top, ovalWidth, ovalHeight);

    // Draw the dark overlay with transparency over the entire screen except the oval
    final rectPaint = Paint()
      ..color = Colors.black.withOpacity(0.6)
      ..style = PaintingStyle.fill;

    // Draw four rectangles around the oval to create the overlay effect
    // Top rectangle
    canvas.drawRect(ui.Rect.fromLTWH(0, 0, size.width, top), rectPaint);
    // Left rectangle
    canvas.drawRect(ui.Rect.fromLTWH(0, top, left, ovalHeight), rectPaint);
    // Right rectangle
    canvas.drawRect(
      ui.Rect.fromLTWH(
        left + ovalWidth,
        top,
        size.width - (left + ovalWidth),
        ovalHeight,
      ),
      rectPaint,
    );
    // Bottom rectangle
    canvas.drawRect(
      ui.Rect.fromLTWH(
        0,
        top + ovalHeight,
        size.width,
        size.height - (top + ovalHeight),
      ),
      rectPaint,
    );

    // Draw the animated border around the oval
    final borderPaint = Paint()
      ..color = borderColor.withOpacity(isProcessing ? 0.8 : 1.0)
      ..style = PaintingStyle.stroke
      ..strokeWidth = borderWidth;

    // Apply pulse effect
    final scaledRect = ui.Rect.fromCenter(
      center: ovalRect.center,
      width: ovalRect.width * pulseValue,
      height: ovalRect.height * pulseValue,
    );

    canvas.drawOval(scaledRect, borderPaint);

    // Draw liveness detection indicators
    if (isProcessing && !isVerified) {
      _drawLivenessIndicators(canvas, ovalRect);
    }

    // Draw success indicator when verified
    if (isVerified) {
      _drawSuccessIndicator(canvas, ovalRect);
    }
  }

  void _drawLivenessIndicators(Canvas canvas, ui.Rect ovalRect) {
    final indicatorPaint = Paint()
      ..color = Colors.amber.withOpacity(livenessOpacity)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Draw multiple concentric ovals to indicate liveness detection
    for (int i = 0; i < 3; i++) {
      final offset = (i + 1) * 8;
      final animatedOffset = offset * (1 + 0.1 * livenessOpacity);
      
      final rect = ui.Rect.fromCenter(
        center: ovalRect.center,
        width: ovalRect.width + animatedOffset,
        height: ovalRect.height + animatedOffset,
      );
      
      canvas.drawOval(rect, indicatorPaint);
    }
  }

  void _drawSuccessIndicator(Canvas canvas, ui.Rect ovalRect) {
    // Draw a green checkmark in the center of the oval
    final checkPaint = Paint()
      ..color = Colors.green
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round;

    final centerX = ovalRect.center.dx;
    final centerY = ovalRect.center.dy + (ovalRect.height * 0.1);

    // Draw checkmark
    canvas.drawLine(
      ui.Offset(centerX - 20, centerY),
      ui.Offset(centerX - 5, centerY + 15),
      checkPaint,
    );
    canvas.drawLine(
      ui.Offset(centerX - 5, centerY + 15),
      ui.Offset(centerX + 25, centerY - 15),
      checkPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _FaceDetectionPainter oldDelegate) {
    return oldDelegate.borderColor != borderColor ||
        oldDelegate.borderWidth != borderWidth ||
        oldDelegate.pulseValue != pulseValue ||
        oldDelegate.isProcessing != isProcessing ||
        oldDelegate.isLive != isLive ||
        oldDelegate.isVerified != isVerified ||
        oldDelegate.livenessOpacity != livenessOpacity;
  }
}