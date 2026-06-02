import 'package:flutter/material.dart';

// Define primary colors for the FPAS app
const Color primaryColor = Color(0xFF2196F3);
const Color secondaryColor = Color(0xFF03DAC6);
const Color backgroundColor = Color(0xFFF5F7FA);
const Color surfaceColor = Colors.white;
const Color errorColor = Color(0xFFB00020);
const Color onPrimaryColor = Colors.white;
const Color onSecondaryColor = Colors.white;
const Color onBackgroundColor = Colors.black;
const Color onSurfaceColor = Colors.black;

// Define dark theme specific colors
const Color darkPrimaryColor = Color(0xFFBB86FC);
const Color darkSecondaryColor = Color(0xFF03DAC6);
const Color darkBackgroundColor = Color(0xFF121212);
const Color darkSurfaceColor = Color(0xFF1E1E1E);
const Color darkErrorColor = Color(0xFFCF6679);
const Color darkOnPrimaryColor = Color(0xFF000000);
const Color darkOnSecondaryColor = Color(0xFF000000);
const Color darkOnBackgroundColor = Color(0xFFE6E6E6);
const Color darkOnSurfaceColor = Color(0xFFE6E6E6);

// Light theme
final ThemeData lightTheme = ThemeData(
  useMaterial3: true,
  brightness: Brightness.light,
  primarySwatch: Colors.blue,
  primaryColor: primaryColor,
  colorScheme: const ColorScheme.light(
    primary: primaryColor,
    secondary: secondaryColor,
    surface: surfaceColor,
    error: errorColor,
    onPrimary: onPrimaryColor,
    onSecondary: onSecondaryColor,
    onSurface: onSurfaceColor,
    onError: Colors.white,
  ),
  scaffoldBackgroundColor: backgroundColor,
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: primaryColor,
      foregroundColor: onPrimaryColor,
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: primaryColor,
      side: const BorderSide(color: primaryColor),
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: surfaceColor,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide(
        color: primaryColor,
        width: 2,
      ),
    ),
  ),
);

// Dark theme
final ThemeData darkTheme = ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  primarySwatch: Colors.blue,
  primaryColor: primaryColor,
  colorScheme: const ColorScheme.dark(
    primary: darkPrimaryColor,
    secondary: darkSecondaryColor,
    surface: darkSurfaceColor,
    error: darkErrorColor,
    onPrimary: darkOnPrimaryColor,
    onSecondary: darkOnSecondaryColor,
    onSurface: darkOnSurfaceColor,
    onError: Colors.white,
  ),
  scaffoldBackgroundColor: darkBackgroundColor,
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: darkPrimaryColor,
      foregroundColor: darkOnPrimaryColor,
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: darkPrimaryColor,
      side: const BorderSide(color: darkPrimaryColor),
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: darkSurfaceColor,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide(
        color: darkPrimaryColor,
        width: 2,
      ),
    ),
  ),
);