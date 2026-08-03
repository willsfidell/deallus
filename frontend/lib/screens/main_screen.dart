import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../widgets/left_sidebar/sidebar_widget.dart';
import '../screens/chat_screen.dart';

/// Main application layout with sidebar and chat panel
class MainScreen extends ConsumerWidget {
  const MainScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Row(
        children: [
          // Left Sidebar (fixed width)
          SizedBox(
            width: 300,
            child: Container(
              decoration: BoxDecoration(
                border: Border(
                  right: BorderSide(
                    color: Colors.grey.shade300,
                  ),
                ),
              ),
              child: SidebarWidget(),
            ),
          ),

          // Right Chat Panel (flexible)
          Expanded(
            child: Container(
              color: Colors.white,
              child: const ChatScreen(),
            ),
          ),
        ],
      ),
    );
  }
}
