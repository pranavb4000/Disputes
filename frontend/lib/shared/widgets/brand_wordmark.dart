import 'package:flutter/material.dart';

/// Text wordmark following the brand format rule: "IDFC FIRST" in capitals, "Bank" in sentence case.
///
/// Replace with the official logo artwork from the brand team when available (README > Branding):
/// keep the 2.8:1 aspect ratio and the breathing space (4x standard, 2x minimum).
class BrandWordmark extends StatelessWidget {
  const BrandWordmark({super.key, this.color = Colors.white, this.size = 20});

  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'IDFC FIRST Bank',
      child: Text.rich(
        const TextSpan(
          children: [
            TextSpan(text: 'IDFC FIRST', style: TextStyle(fontWeight: FontWeight.w700, letterSpacing: 0.5)),
            TextSpan(text: ' Bank'),
          ],
        ),
        style: TextStyle(color: color, fontSize: size, height: 1.1),
      ),
    );
  }
}
