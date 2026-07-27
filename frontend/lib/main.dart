import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:logger/logger.dart';

import 'config/app_constants.dart';
import 'providers/auth_provider.dart';
import 'providers/settings_provider.dart';
import 'screens/auth_screen.dart';
import 'screens/main_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Hive for local caching
  await Hive.initFlutter();
  
  runApp(const ProviderScope(child: DeallushApp()));
}

/// Main application widget
class DeallushApp extends ConsumerWidget {
  const DeallushApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeProvider);
    final fontSize = ref.watch(fontSizeProvider);
    final authState = ref.watch(authProvider);

    // Build router based on auth state
    final goRouter = GoRouter(
      initialLocation: '/',
      redirect: (context, state) {
        // Check authentication state
        final isAuthenticated = authState.maybeWhen(
          data: (auth) => auth.isAuthenticated,
          orElse: () => false,
        );

        final isLoggingIn = state.matchedLocation == '/auth';

        // If not authenticated, redirect to auth screen
        if (!isAuthenticated && !isLoggingIn) {
          return '/auth';
        }

        // If authenticated and trying to access auth, redirect to home
        if (isAuthenticated && isLoggingIn) {
          return '/';
        }

        return null;
      },
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const MainScreen(),
        ),
        GoRoute(
          path: '/auth',
          builder: (context, state) => const AuthScreen(),
        ),
      ],
    );

    return MaterialApp.router(
      title: 'Deallus',
      theme: _buildLightTheme(fontSize),
      darkTheme: _buildDarkTheme(fontSize),
      themeMode: _convertThemeMode(themeMode),
      routerConfig: goRouter,
    );
  }

  /// Build light theme
  ThemeData _buildLightTheme(double fontSize) {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      primarySwatch: Colors.blue,
      textTheme: TextTheme(
        displayLarge: TextStyle(fontSize: fontSize + 8),
        displayMedium: TextStyle(fontSize: fontSize + 6),
        displaySmall: TextStyle(fontSize: fontSize + 4),
        headlineMedium: TextStyle(fontSize: fontSize + 4),
        headlineSmall: TextStyle(fontSize: fontSize + 2),
        titleLarge: TextStyle(fontSize: fontSize + 2),
        titleMedium: TextStyle(fontSize: fontSize),
        titleSmall: TextStyle(fontSize: fontSize - 2),
        bodyLarge: TextStyle(fontSize: fontSize),
        bodyMedium: TextStyle(fontSize: fontSize - 2),
        bodySmall: TextStyle(fontSize: fontSize - 4),
        labelLarge: TextStyle(fontSize: fontSize - 2),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: fontSize + 4,
          fontWeight: FontWeight.w600,
          color: Colors.black,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        filled: true,
        fillColor: Colors.grey[50],
      ),
    );
  }

  /// Build dark theme
  ThemeData _buildDarkTheme(double fontSize) {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      primarySwatch: Colors.blue,
      textTheme: TextTheme(
        displayLarge: TextStyle(fontSize: fontSize + 8),
        displayMedium: TextStyle(fontSize: fontSize + 6),
        displaySmall: TextStyle(fontSize: fontSize + 4),
        headlineMedium: TextStyle(fontSize: fontSize + 4),
        headlineSmall: TextStyle(fontSize: fontSize + 2),
        titleLarge: TextStyle(fontSize: fontSize + 2),
        titleMedium: TextStyle(fontSize: fontSize),
        titleSmall: TextStyle(fontSize: fontSize - 2),
        bodyLarge: TextStyle(fontSize: fontSize),
        bodyMedium: TextStyle(fontSize: fontSize - 2),
        bodySmall: TextStyle(fontSize: fontSize - 4),
        labelLarge: TextStyle(fontSize: fontSize - 2),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.grey[900],
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: fontSize + 4,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        filled: true,
        fillColor: Colors.grey[800],
      ),
    );
  }

  /// Convert ThemeMode enum to Flutter's ThemeMode
  ThemeMode _convertThemeMode(dynamic theme) {
    if (theme.toString().contains('light')) {
      return ThemeMode.light;
    } else if (theme.toString().contains('dark')) {
      return ThemeMode.dark;
    }
    return ThemeMode.system;
  }
}
